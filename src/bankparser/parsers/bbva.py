"""Parser for BBVA Mexico (Bancomer) TDC (credit card) statements.

BBVA TDC PDF statements have:
- Header with account info, period, balances
- "CARGOS,COMPRAS Y ABONOS REGULARES(NO A MESES)" section with transactions
- Each transaction: two dates (operation + charge), description, +/- sign, $ amount
- Optional foreign-currency continuation line with original amount and exchange rate

NOTE: BBVA statement formats vary between credit cards, debit accounts,
and different statement periods. If the parser doesn't work perfectly
with your statement, share a redacted sample to improve it.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType
from bankparser.parsers.base import BaseParser

# BBVA uses abbreviated months in some formats
MONTHS_ABBREV = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4,
    "may": 5, "jun": 6, "jul": 7, "ago": 8,
    "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}


class BBVAParser(BaseParser):
    """Parses BBVA Mexico (Bancomer) PDF statements."""

    bank_name = "bbva"

    # ── Detection ─────────────────────────────────────────────────────────────

    def can_parse(self, pdf_path: Path) -> bool:
        text = self.extract_first_page_text(pdf_path).lower()
        return (
            "bbva" in text
            or "bancomer" in text
            or "bbva méxico" in text
            or "bbva mexico" in text
        )

    # ── Regexes ───────────────────────────────────────────────────────────────

    # Transaction line: two dates, description, +/- sign, $ amount
    # e.g. "11-ene-2026 12-ene-2026 OXXO TONALA + $48.50"
    TX_RE = re.compile(
        r'^(\d{1,2}-[a-z]{3}-\d{4})\s+(\d{1,2}-[a-z]{3}-\d{4})\s+(.+?)\s+([+-])\s+\$([\d,]+\.\d{2})\s*$'
    )

    # Foreign currency continuation line
    # e.g. "USD $100.45 TIPO DE CAMBIO $17.99"
    FOREIGN_RE = re.compile(
        r'^\s*([A-Z]{3})\s+\$([\d,]+\.\d{2})\s+TIPO DE CAMBIO\s+\$([\d,.]+)'
    )

    # Installment prefix in description: "03 DE 03 TIENDA GRANDE"
    INSTALLMENT_RE = re.compile(r'^(\d{2}\s+DE\s+\d{2,3})\s+(.+)')

    # MSI sin intereses row: date, description, original amount, pending, required, installment, rate
    MSI_SIN_RE = re.compile(
        r'^(\d{1,2}-[a-z]{3}-\d{4})\s+(.+?)\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+(\d+\s+de\s+\d+)\s+([\d.]+%)'
    )

    # MSI con intereses row: date, description, original, pending, interest, iva, required, installment, rate
    MSI_CON_RE = re.compile(
        r'^(\d{1,2}-[a-z]{3}-\d{4})\s+(.+?)\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+(\d+\s+de\s+\d+)\s+([\d.]+%)'
    )

    # Lines to skip (non-transaction content)
    SKIP_PATTERNS = [
        re.compile(r'^CARGOS,COMPRAS Y ABONOS'),
        re.compile(r'^Fecha'),
        re.compile(r'^de la\s+Descripción'),
        re.compile(r'^de cargo'),
        re.compile(r'^operación'),
        re.compile(r'^TOTAL\s+(CARGOS|ABONOS)'),
        re.compile(r'^IVA\s*:\$'),
        re.compile(r'^Capital de promoción'),
    ]

    # ── Main parse ────────────────────────────────────────────────────────────

    def parse(self, pdf_path: Path) -> ParseResult:
        pages_text = self.extract_text_from_pdf(pdf_path)
        warnings: list[str] = []

        full_text = "\n".join(pages_text)
        info = self._extract_info(full_text)

        # Collect all lines from all pages
        all_lines: list[str] = []
        for text in pages_text:
            all_lines.extend(text.split('\n'))

        transactions = self._parse_regular_section(all_lines)
        transactions.extend(self._parse_msi_section(all_lines))

        return ParseResult(info=info, transactions=transactions, warnings=warnings)

    # ── Info extraction ───────────────────────────────────────────────────────

    @staticmethod
    def _parse_bbva_date(date_str: str) -> date:
        """Parse a BBVA date in 'DD-mmm-YYYY' format (e.g. '08-ene-2026')."""
        day_s, month_s, year_s = date_str.split("-")
        month = MONTHS_ABBREV[month_s.lower()]
        return date(int(year_s), month, int(day_s))

    def _extract_info(self, text: str) -> StatementInfo:
        info = StatementInfo(bank=self.bank_name)

        # Account number: "Numero de tarjeta: 4152XXXXXXXXXXXX"
        acct_match = re.search(r'Número de tarjeta:\s*(\d+)', text)
        if acct_match:
            info.account_number = acct_match.group(1)

        # Period: "Periodo: 08-ene-2026 al 07-feb-2026"
        period_match = re.search(
            r'Periodo:\s+(\d{1,2}-[a-z]{3}-\d{4})\s+al\s+(\d{1,2}-[a-z]{3}-\d{4})',
            text,
        )
        if period_match:
            try:
                info.period_start = self._parse_bbva_date(period_match.group(1))
                info.period_end = self._parse_bbva_date(period_match.group(2))
            except (ValueError, KeyError):
                pass

        # Cardholder: line immediately after "TU PAGO REQUERIDO ESTE PERIODO"
        name_match = re.search(
            r'TU PAGO REQUERIDO ESTE PERIODO\n([A-ZÁÉÍÓÚÑ ]+)\n', text
        )
        if name_match:
            info.cardholder = name_match.group(1).strip()

        # Cut date: "Fecha de corte: 07-feb-2026"
        cut_match = re.search(
            r'Fecha de corte:\s+(\d{1,2}-[a-z]{3}-\d{4})', text
        )
        if cut_match:
            try:
                info.cut_date = self._parse_bbva_date(cut_match.group(1))
            except (ValueError, KeyError):
                pass

        # Previous balance: "Adeudo del periodo anterior $19,810.48"
        balance_match = re.search(
            r'Adeudo del periodo anterior\s+\$([\d,]+\.\d{2})', text
        )
        if balance_match:
            info.previous_balance = self.parse_mx_amount(balance_match.group(1))

        return info

    # ── Transaction parsing ───────────────────────────────────────────────────

    def _parse_regular_section(self, lines: list[str]) -> list[Transaction]:
        """Parse the CARGOS,COMPRAS Y ABONOS REGULARES section.

        Iterates through lines, matching transaction patterns and looking
        ahead for foreign-currency continuation lines.
        """
        transactions: list[Transaction] = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Skip non-transaction lines
            if self._should_skip(line.strip()):
                i += 1
                continue

            # Try to match a transaction line
            tx_match = self.TX_RE.match(line.strip())
            if not tx_match:
                i += 1
                continue

            # Extract fields from the match
            op_date_str = tx_match.group(1)
            charge_date_str = tx_match.group(2)
            description = tx_match.group(3).strip()
            sign = tx_match.group(4)
            amount_str = tx_match.group(5)

            # Parse dates
            tx_date = self._parse_bbva_date(op_date_str)
            amount = self.parse_mx_amount(amount_str)

            # Look ahead for foreign currency continuation
            original_amount = None
            original_currency = None
            exchange_rate = None
            j = i + 1

            if j < len(lines):
                foreign_match = self.FOREIGN_RE.match(lines[j])
                if foreign_match:
                    original_currency = foreign_match.group(1)
                    original_amount = self.parse_mx_amount(foreign_match.group(2))
                    exchange_rate = float(foreign_match.group(3).replace(',', ''))
                    j += 1

            # Determine sign: - means payment/credit, + means charge
            is_minus = sign == "-"
            if is_minus:
                amount = -amount

            # Check for installment prefix in description
            installment = ""
            inst_match = self.INSTALLMENT_RE.match(description)
            if inst_match:
                installment = inst_match.group(1)

            # Classify transaction
            tx_type = self._classify(description, is_minus, installment)

            tx = Transaction(
                date=tx_date,
                description=description,
                amount=amount,
                currency="MXN",
                bank=self.bank_name,
                tx_type=tx_type,
                installment=installment,
                original_amount=original_amount,
                original_currency=original_currency,
                exchange_rate=exchange_rate,
            )
            transactions.append(tx)
            i = j
            continue

        return transactions

    def _parse_msi_section(self, lines: list[str]) -> list[Transaction]:
        """Parse the MSI (Meses sin intereses) sections.

        Finds both 'MESES SIN INTERESES' and 'MESES CON INTERESES' section
        headers and parses the transaction rows within each section.
        Skips table header lines and continuation lines (e.g. '36 M.').
        """
        transactions: list[Transaction] = []

        # Track which section we are currently in: None, "sin", or "con"
        current_section: str | None = None

        for line in lines:
            stripped = line.strip()

            # Detect section headers
            if "COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES" in stripped:
                current_section = "sin"
                continue
            if "COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES" in stripped:
                current_section = "con"
                continue

            # If not in an MSI section, skip
            if current_section is None:
                continue

            # Skip empty lines
            if not stripped:
                continue

            # Try to match a row depending on the current section
            if current_section == "con":
                match = self.MSI_CON_RE.match(stripped)
                if match:
                    tx = Transaction(
                        date=self._parse_bbva_date(match.group(1)),
                        description=match.group(2).strip(),
                        amount=self.parse_mx_amount(match.group(3)),
                        currency="MXN",
                        bank=self.bank_name,
                        tx_type=TransactionType.MSI,
                        installment=match.group(8),
                    )
                    transactions.append(tx)
                # Non-matching lines (table headers, continuation lines like "36 M.")
                # are simply skipped
                continue

            if current_section == "sin":
                match = self.MSI_SIN_RE.match(stripped)
                if match:
                    tx = Transaction(
                        date=self._parse_bbva_date(match.group(1)),
                        description=match.group(2).strip(),
                        amount=self.parse_mx_amount(match.group(3)),
                        currency="MXN",
                        bank=self.bank_name,
                        tx_type=TransactionType.MSI,
                        installment=match.group(6),
                    )
                    transactions.append(tx)
                continue

        return transactions

    def _classify(self, description: str, is_minus: bool, installment: str = "") -> TransactionType:
        """Classify a transaction based on its description and sign.

        Rules (checked in order, more specific patterns first):
        - "BMOVIL.PAGO TDC" or minus-sign + "PAGO" -> PAYMENT
        - "CONTRATACION BENEFICIOS" -> FEE
        - "ABONO FINANC. COMPRAS" or "ALTA PARA MESES S/INTERESES" -> MSI_ADJUSTMENT
        - "INTERES" in description -> INTEREST
        - "XX DE YY EFECTIVO INMEDIATO" or installment prefix -> MSI
        - Minus sign (not already classified) -> PAYMENT
        - Plus sign -> CHARGE
        """
        desc = description.upper()

        # Payment: BMOVIL.PAGO TDC or any minus-sign with PAGO
        if "BMOVIL.PAGO TDC" in desc:
            return TransactionType.PAYMENT
        if is_minus and "PAGO" in desc:
            return TransactionType.PAYMENT

        # Fee: CONTRATACION BENEFICIOS (before INTEREST, since some fees
        # may contain "intereses" in a different context)
        if "CONTRATACION BENEFICIOS" in desc:
            return TransactionType.FEE

        # MSI Adjustment: ABONO FINANC. COMPRAS, ALTA PARA MESES S/INTERESES
        # Must be checked before INTEREST because "S/INTERESES" contains "INTERES"
        if "ABONO FINANC" in desc:
            return TransactionType.MSI_ADJUSTMENT
        if "ALTA PARA MESES S/INTERESES" in desc:
            return TransactionType.MSI_ADJUSTMENT

        # Interest: * INTERESES EFI * or anything with INTERES
        if "INTERES" in desc:
            return TransactionType.INTEREST

        # MSI: installment pattern (XX DE YY) in description
        if installment:
            return TransactionType.MSI
        if re.search(r'\d{2}\s+DE\s+\d{2,3}\s+EFECTIVO INMEDIATO', desc):
            return TransactionType.MSI

        # Remaining minus-sign transactions
        if is_minus:
            return TransactionType.PAYMENT

        return TransactionType.CHARGE

    def _should_skip(self, line: str) -> bool:
        """Check if a line should be skipped (headers, totals, breakdowns)."""
        for pattern in self.SKIP_PATTERNS:
            if pattern.match(line):
                return True
        return False
