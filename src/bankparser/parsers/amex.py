"""Parser for American Express Mexico credit card statements."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType
from bankparser.parsers.base import BaseParser, MONTHS_ES


class AmexParser(BaseParser):
    """Parses American Express Mexico PDF statements.

    Handles:
    - MXN and foreign currency (USD) transactions
    - Multiple cardholders (titular + adicionales)
    - MSI (meses sin intereses) installments
    - Payments, credits, fees, interest, IVA
    """

    bank_name = "amex"

    # ── Detection ─────────────────────────────────────────────────────────────

    def can_parse(self, pdf_path: Path) -> bool:
        text = self.extract_first_page_text(pdf_path)
        return (
            "american express" in text.lower()
            or "americanexpress" in text.lower()
            or "amex" in text.lower()
            or "3717-" in text  # Amex Mexico account prefix
        )

    # ── Regexes ───────────────────────────────────────────────────────────────

    # Transaction line: "DD deMes DESCRIPTION AMOUNT"
    TX_DATE_RE = re.compile(
        r'^(\d{1,2})\s+de\s*([A-Za-záéíóúñ]+)\s+(.+?)\s+([\d,]+\.\d{2})\s*$'
    )
    CR_RE = re.compile(r'\bCR\b')
    INSTALLMENT_RE = re.compile(r'CARGO\s+(\d{2}\s+DE\s*\d{2,3})', re.IGNORECASE)
    FOREIGN_RE = re.compile(r'Dólar\s+U\.S\.A\.\s+([\d,]+\.\d{2})\s+TC:([\d.]+)')
    TOTAL_RE = re.compile(
        r'Total\s+de\s+las\s+transacciones\s+en\s+\$\s+de\s+(.+?)\s+([\d,]+\.\d{2})'
    )
    TOTAL_FOREIGN_RE = re.compile(
        r'Total\s+de\s+Transacciones\s+en\s+Moneda\s+Extranjera\s+de'
    )

    SKIP_PATTERNS = [
        r'^Estado de Cuenta', r'^Número de Cuenta', r'^Tarjetahabiente',
        r'^Comisiones:', r'^Total Nuevos Cargos', r'^Fecha y Detalle',
        r'^Importe en MN', r'^Paga desde', r'^Recuerda que',
        r'^En Canales', r'^Desde tu App', r'^Desde la Web',
        r'^Paga con tu', r'^El pago puede', r'^Para mayor info',
        r'^Transacciones de Meses sin Intereses', r'^Descripción de compras',
        r'^Intereses y de Meses', r'^Transacciones financieras aplicables',
        r'^Total de Meses sin Intereses', r'^Total de las transacciones y comisiones',
        r'^Total de IVA', r'^Cuando pagas', r'^en tu cuenta',
    ]

    # ── Main parse ────────────────────────────────────────────────────────────

    def parse(self, pdf_path: Path) -> ParseResult:
        pages_text = self.extract_text_from_pdf(pdf_path)
        warnings: list[str] = []

        # Extract metadata from first page
        info = self._extract_info(pages_text[0] if pages_text else "")

        # Determine default cardholder from statement
        default_cardholder = info.cardholder or "TITULAR"
        current_cardholder = default_cardholder
        year = info.period_end.year if info.period_end else 2026

        # Parse transaction pages (skip first page = summary)
        all_lines: list[str] = []
        for page_text in pages_text[1:]:
            all_lines.extend(page_text.split('\n'))

        transactions: list[Transaction] = []
        i = 0

        while i < len(all_lines):
            line = all_lines[i].strip()

            if not line or self._should_skip(line):
                i += 1
                continue

            # Cardholder section change on total lines
            total_match = self.TOTAL_RE.search(line)
            if total_match:
                name = total_match.group(1).strip().upper()
                if default_cardholder.split()[0].upper() in name:
                    # After "Total de Pedro..." → next transactions are additional cardholder
                    current_cardholder = "ADICIONAL"
                else:
                    current_cardholder = default_cardholder
                i += 1
                continue

            if self.TOTAL_FOREIGN_RE.search(line):
                current_cardholder = default_cardholder
                i += 1
                continue

            # Section changes
            if "Meses sin Intereses" in line and "Total" not in line:
                i += 1
                continue
            if "Transacciones financieras aplicables" in line:
                i += 1
                continue
            if "Total de Meses sin Intereses" in line:
                i += 1
                continue

            # Try to match a transaction
            tx_match = self.TX_DATE_RE.match(line)
            if tx_match:
                day = int(tx_match.group(1))
                month_name = tx_match.group(2)
                description = tx_match.group(3).strip()
                amount = self.parse_mx_amount(tx_match.group(4))
                is_credit = bool(self.CR_RE.search(line))

                try:
                    tx_date = self.parse_spanish_date(day, month_name, year)
                except ValueError:
                    warnings.append(f"Could not parse date: {day} de {month_name} {year}")
                    i += 1
                    continue

                # Handle year boundary (Jan dates in a Dec-Jan statement)
                if info.period_start and info.period_end:
                    if info.period_start.month > tx_date.month and tx_date.month <= 2:
                        tx_date = tx_date.replace(year=year)

                # Look ahead for metadata lines
                installment = ""
                reference = ""
                original_usd = None
                exchange_rate = None
                j = i + 1

                while j < len(all_lines):
                    next_line = all_lines[j].strip()

                    if next_line == "CR":
                        is_credit = True
                        j += 1
                        continue

                    inst_match = self.INSTALLMENT_RE.search(next_line)
                    if inst_match:
                        installment = inst_match.group(1)
                        j += 1
                        continue

                    if next_line.startswith("RFC") or re.match(r'^RFC\s*[A-Z]', next_line):
                        if self.CR_RE.search(next_line):
                            is_credit = True
                        reference = re.sub(r'\s*CR\s*$', '', next_line).strip()
                        j += 1
                        continue

                    foreign_match = self.FOREIGN_RE.search(next_line)
                    if foreign_match:
                        original_usd = self.parse_mx_amount(foreign_match.group(1))
                        exchange_rate = float(foreign_match.group(2))
                        j += 1
                        continue

                    break

                # Classify and build transaction
                tx_type = self._classify(description, is_credit)
                if is_credit:
                    amount = -amount

                tx = Transaction(
                    date=tx_date,
                    description=description,
                    amount=amount,
                    currency="MXN",
                    bank=self.bank_name,
                    cardholder=current_cardholder,
                    tx_type=tx_type,
                    installment=installment,
                    reference=reference,
                    original_amount=original_usd,
                    original_currency="USD" if original_usd else None,
                    exchange_rate=exchange_rate,
                )
                transactions.append(tx)
                i = j
                continue

            i += 1

        # Update cardholder names if we found them in the totals
        self._resolve_cardholders(transactions, all_lines, default_cardholder)

        return ParseResult(info=info, transactions=transactions, warnings=warnings)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _extract_info(self, first_page: str) -> StatementInfo:
        info = StatementInfo(bank=self.bank_name)

        # Account number
        acct_match = re.search(r'(\d{4}-\d{6}-\d{5})', first_page)
        if acct_match:
            info.account_number = acct_match.group(1)

        # Cut date  "08-Feb-2026"
        cut_match = re.search(r'(\d{2})-([A-Za-z]+)-(\d{4})', first_page)
        if cut_match:
            try:
                info.cut_date = self.parse_spanish_date(
                    int(cut_match.group(1)),
                    cut_match.group(2),
                    int(cut_match.group(3)),
                )
            except ValueError:
                pass

        # Period "Del 9 de Enero al 8 de Febrero de 2026"
        period_match = re.search(
            r'Del\s+(\d{1,2})\s+de\s+([A-Za-záéíóúñ]+)\s+al\s+(\d{1,2})\s+de\s+([A-Za-záéíóúñ]+)\s+de\s+(\d{4})',
            first_page,
        )
        if period_match:
            year = int(period_match.group(5))
            try:
                info.period_start = self.parse_spanish_date(
                    int(period_match.group(1)), period_match.group(2), year
                )
                info.period_end = self.parse_spanish_date(
                    int(period_match.group(3)), period_match.group(4), year
                )
            except ValueError:
                pass

        # Cardholder name (usually right below "Tarjetahabiente")
        name_match = re.search(r'Tarjetahabiente\s+\d{4}.*?\n([A-ZÁÉÍÓÚÑ ]+)', first_page)
        if name_match:
            info.cardholder = name_match.group(1).strip()

        return info

    def _should_skip(self, line: str) -> bool:
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, line):
                return True
        return False

    def _classify(self, description: str, is_credit: bool) -> TransactionType:
        desc = description.upper()
        if "GRACIAS POR SU PAGO" in desc:
            return TransactionType.PAYMENT
        if "MONTO A DIFERIR" in desc:
            return TransactionType.MSI_ADJUSTMENT
        if "MESES EN AUTOMÁTICO" in desc:
            return TransactionType.MSI
        if "CUOTA ANUAL" in desc:
            return TransactionType.FEE
        if "IVA APLICABLE" in desc:
            return TransactionType.TAX
        if "INTERÉS FINANCIERO" in desc or "INTERES FINANCIERO" in desc:
            return TransactionType.INTEREST
        if is_credit:
            return TransactionType.CREDIT
        return TransactionType.CHARGE

    def _resolve_cardholders(
        self,
        transactions: list[Transaction],
        lines: list[str],
        default_cardholder: str,
    ):
        """Try to find the additional cardholder name from total lines."""
        additional_name = None
        for line in lines:
            match = self.TOTAL_RE.search(line)
            if match:
                name = match.group(1).strip()
                if default_cardholder.split()[0].upper() not in name.upper():
                    additional_name = name

        if additional_name:
            for tx in transactions:
                if tx.cardholder == "ADICIONAL":
                    tx.cardholder = additional_name
                elif tx.cardholder == default_cardholder:
                    pass  # keep as-is
