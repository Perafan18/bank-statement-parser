"""Parser for BBVA Mexico (Bancomer) credit card and debit statements.

BBVA Mexico PDF statements typically have:
- Header with account info, period, balances
- "MOVIMIENTOS DEL PERIODO" section with tabular transactions
- Format: DD/MMM  DESCRIPTION  CARGO/ABONO  AMOUNT
- Or:     DD/MMM/YYYY  DESCRIPTION  AMOUNT

NOTE: BBVA statement formats vary between credit cards, debit accounts,
and different statement periods. If the parser doesn't work perfectly
with your statement, share a redacted sample to improve it.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType
from bankparser.parsers.base import BaseParser, MONTHS_ES

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

    # Date formats BBVA uses:
    # "09/ENE"  "09/Ene"  "09/01"  "09/01/2026"  "09 ENE"
    DATE_PATTERNS = [
        # DD/MMM or DD/MMM/YYYY (month as 3-letter abbreviation)
        re.compile(
            r'^(\d{1,2})[/\s]([A-Za-z]{3})(?:[/\s](\d{2,4}))?\s+(.+?)\s+([\d,]+\.\d{2})\s*$'
        ),
        # DD/MM or DD/MM/YYYY (numeric month)
        re.compile(
            r'^(\d{1,2})/(\d{2})(?:/(\d{2,4}))?\s+(.+?)\s+([\d,]+\.\d{2})\s*$'
        ),
    ]

    # Two-column format: description on one side, cargo/abono on the other
    TWO_COL_RE = re.compile(
        r'^(\d{1,2})[/\s]([A-Za-z]{3}|\d{2})(?:[/\s](\d{2,4}))?\s+'
        r'(.+?)\s+'
        r'([\d,]+\.\d{2})\s*(-?)$'
    )

    SKIP_PATTERNS = [
        r'^Estado de [Cc]uenta', r'^ESTADO DE CUENTA',
        r'^Resumen', r'^RESUMEN', r'^Página', r'^PÁGINA',
        r'^Saldo anterior', r'^SALDO ANTERIOR',
        r'^Total de movimientos', r'^TOTAL DE MOVIMIENTOS',
        r'^Fecha de corte', r'^FECHA DE CORTE',
        r'^Saldo al corte', r'^SALDO AL CORTE',
        r'^Pago mínimo', r'^PAGO MÍNIMO',
        r'^Fecha límite', r'^FECHA LÍMITE',
        r'^MOVIMIENTOS DEL PERIODO', r'^Movimientos del periodo',
        r'^Concepto\s+Cargo', r'^CONCEPTO\s+CARGO',
        r'^Fecha\s+Concepto', r'^FECHA\s+CONCEPTO',
        r'^CAT\s', r'^Tasa de interés',
        r'^CLABE:', r'^RFC:',
        r'^Para cualquier', r'^Línea BBVA',
    ]

    # ── Main parse ────────────────────────────────────────────────────────────

    def parse(self, pdf_path: Path) -> ParseResult:
        pages_text = self.extract_text_from_pdf(pdf_path)
        warnings: list[str] = []

        info = self._extract_info(pages_text[0] if pages_text else "")
        year = info.period_end.year if info.period_end else date.today().year

        # Collect all lines from all pages
        all_lines: list[str] = []
        for text in pages_text:
            all_lines.extend(text.split('\n'))

        transactions = self._parse_lines(all_lines, year, warnings)

        return ParseResult(info=info, transactions=transactions, warnings=warnings)

    # ── Info extraction ───────────────────────────────────────────────────────

    def _extract_info(self, first_page: str) -> StatementInfo:
        info = StatementInfo(bank=self.bank_name)

        # Account number (BBVA uses various formats)
        # "Número de cuenta: 1234 5678 9012 3456" or "No. de Tarjeta: 4152..."
        acct_patterns = [
            r'(?:cuenta|tarjeta)[:\s]+(\d[\d\s*-]+\d)',
            r'(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})',
        ]
        for pattern in acct_patterns:
            match = re.search(pattern, first_page, re.IGNORECASE)
            if match:
                info.account_number = re.sub(r'\s+', '', match.group(1))
                break

        # Period: "Del 10 de Diciembre al 09 de Enero de 2026"
        # Or: "Periodo: 10/Dic/2025 al 09/Ene/2026"
        period_match = re.search(
            r'[Dd]el\s+(\d{1,2})\s+de\s+([A-Za-záéíóúñ]+)\s+'
            r'(?:de\s+\d{4}\s+)?al\s+(\d{1,2})\s+de\s+([A-Za-záéíóúñ]+)\s+de\s+(\d{4})',
            first_page,
        )
        if period_match:
            year = int(period_match.group(5))
            try:
                end_month = MONTHS_ES.get(period_match.group(4).lower())
                start_month = MONTHS_ES.get(period_match.group(2).lower())
                if start_month and end_month:
                    start_year = year if start_month <= end_month else year - 1
                    info.period_start = date(
                        start_year, start_month, int(period_match.group(1))
                    )
                    info.period_end = date(year, end_month, int(period_match.group(3)))
            except (ValueError, TypeError):
                pass

        # Cardholder
        name_match = re.search(r'(?:NOMBRE|Nombre|Cliente)[:\s]+([A-ZÁÉÍÓÚÑ ]+)', first_page)
        if name_match:
            info.cardholder = name_match.group(1).strip()

        return info

    # ── Transaction parsing ───────────────────────────────────────────────────

    def _parse_lines(
        self, lines: list[str], year: int, warnings: list[str]
    ) -> list[Transaction]:
        transactions: list[Transaction] = []
        in_movements = False

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Detect start of movements section
            if re.match(r'(?i)movimientos?\s+(del\s+)?periodo', line):
                in_movements = True
                continue

            if self._should_skip(line):
                continue

            if not in_movements:
                # Also try to parse if line looks like a transaction
                # (some BBVA statements don't have a clear section header)
                pass

            # Try each date pattern
            tx = self._try_parse_transaction(line, year)
            if tx:
                transactions.append(tx)

        return transactions

    def _try_parse_transaction(self, line: str, year: int) -> Transaction | None:
        """Try to parse a line as a transaction."""

        for pattern in self.DATE_PATTERNS:
            match = pattern.match(line)
            if match:
                return self._build_transaction(match, year)

        return None

    def _build_transaction(self, match: re.Match, year: int) -> Transaction | None:
        """Build a Transaction from a regex match."""
        day = int(match.group(1))
        month_raw = match.group(2)
        year_raw = match.group(3)  # might be None
        description = match.group(4).strip()
        amount_str = match.group(5)

        # Resolve month
        month = self._resolve_month(month_raw)
        if month is None:
            return None

        # Resolve year
        if year_raw:
            tx_year = int(year_raw)
            if tx_year < 100:
                tx_year += 2000
        else:
            tx_year = year

        try:
            tx_date = date(tx_year, month, day)
        except ValueError:
            return None

        amount = self.parse_mx_amount(amount_str)

        # Determine if credit/debit
        is_credit = self._is_credit(description)
        tx_type = self._classify(description, is_credit)

        if is_credit:
            amount = -amount

        return Transaction(
            date=tx_date,
            description=description,
            amount=amount,
            currency="MXN",
            bank=self.bank_name,
            tx_type=tx_type,
        )

    def _resolve_month(self, month_raw: str) -> int | None:
        """Resolve month from abbreviation or number."""
        if month_raw.isdigit():
            m = int(month_raw)
            return m if 1 <= m <= 12 else None

        abbrev = month_raw.lower()[:3]
        return MONTHS_ABBREV.get(abbrev) or MONTHS_ES.get(abbrev)

    def _is_credit(self, description: str) -> bool:
        """Heuristic to detect credits in BBVA statements."""
        desc = description.upper()
        return any(kw in desc for kw in [
            "PAGO", "ABONO", "DEVOLUCION", "DEVOLUCIÓN", "BONIFICACION",
            "BONIFICACIÓN", "TRANSFERENCIA RECIBIDA",
        ])

    def _classify(self, description: str, is_credit: bool) -> TransactionType:
        desc = description.upper()
        if any(kw in desc for kw in ["PAGO DE", "PAGO RECIBIDO", "SU PAGO", "ABONO"]):
            return TransactionType.PAYMENT
        if "INTERES" in desc and ("ORDINARIO" in desc or "FINANCIERO" in desc):
            return TransactionType.INTEREST
        if "COMISION" in desc or "COMISIÓN" in desc:
            return TransactionType.FEE
        if "IVA" in desc or "I.V.A" in desc:
            return TransactionType.TAX
        if "ANUALIDAD" in desc or "CUOTA ANUAL" in desc:
            return TransactionType.FEE
        if is_credit:
            return TransactionType.CREDIT
        return TransactionType.CHARGE

    def _should_skip(self, line: str) -> bool:
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, line):
                return True
        return False
