"""Parser for HSBC Mexico credit card and debit statements.

HSBC Mexico PDF statements typically have:
- Summary page with balances
- Transaction pages with format:
  DD MMM  DESCRIPTION  DD MMM  AMOUNT
  (transaction date, description, posting date, amount)
- Some statements use: DD/MM  DESCRIPTION  AMOUNT
- Foreign transactions in separate section

NOTE: HSBC statement formats can vary. If the parser doesn't match
your statement, share a redacted sample to improve it.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType
from bankparser.parsers.base import BaseParser, MONTHS_ES

MONTHS_ABBREV = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4,
    "may": 5, "jun": 6, "jul": 7, "ago": 8,
    "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}


class HSBCParser(BaseParser):
    """Parses HSBC Mexico PDF statements."""

    bank_name = "hsbc"

    # ── Detection ─────────────────────────────────────────────────────────────

    def can_parse(self, pdf_path: Path) -> bool:
        text = self.extract_first_page_text(pdf_path).lower()
        return (
            "hsbc" in text
            or "hsbc méxico" in text
            or "hsbc mexico" in text
        )

    # ── Regexes ───────────────────────────────────────────────────────────────

    # HSBC credit card format:
    # "DD MMM  DESCRIPTION  DD MMM  AMOUNT" (tx date + post date)
    # or "DD/MMM  DESCRIPTION  AMOUNT"
    TX_PATTERNS = [
        # DD MMM DESCRIPTION DD MMM AMOUNT (with posting date)
        re.compile(
            r'^(\d{1,2})\s+([A-Za-z]{3})\s+'  # transaction date
            r'(.+?)\s+'                         # description
            r'\d{1,2}\s+[A-Za-z]{3}\s+'        # posting date (ignored)
            r'([\d,]+\.\d{2})\s*(-?)\s*$'      # amount and optional minus
        ),
        # DD/MMM DESCRIPTION AMOUNT
        re.compile(
            r'^(\d{1,2})[/\s]([A-Za-z]{3})\s+'
            r'(.+?)\s+'
            r'([\d,]+\.\d{2})\s*(-?)\s*$'
        ),
        # DD/MM/YYYY DESCRIPTION AMOUNT
        re.compile(
            r'^(\d{1,2})/(\d{2})/(\d{2,4})\s+'
            r'(.+?)\s+'
            r'([\d,]+\.\d{2})\s*(-?)\s*$'
        ),
    ]

    SKIP_PATTERNS = [
        r'^Estado de [Cc]uenta', r'^ESTADO DE CUENTA',
        r'^Resumen', r'^Página', r'^Pág\.',
        r'^Saldo [Aa]nterior', r'^SALDO',
        r'^Total', r'^TOTAL',
        r'^Fecha de [Cc]orte', r'^Fecha [Ll]ímite',
        r'^Pago [Mm]ínimo', r'^PAGO',
        r'^DETALLE DE MOVIMIENTOS', r'^Detalle de movimientos',
        r'^Fecha\s+Descripción', r'^FECHA\s+DESCRIPCIÓN',
        r'^Transacciones\s+en\s+moneda', r'^TRANSACCIONES',
        r'^Tipo\s+de\s+cambio', r'^TIPO DE CAMBIO',
        r'^CAT\s', r'^Tasa',
        r'^HSBC México', r'^Para mayor',
        r'^Línea\s+HSBC', r'^www\.hsbc',
        r'^\d{4}\s*\*{4,}',  # masked card numbers
    ]

    # Foreign transaction line
    FOREIGN_RE = re.compile(
        r'(?:USD|EUR|GBP)\s+([\d,]+\.\d{2})\s+T\.?C\.?\s*([\d.]+)'
    )

    # ── Main parse ────────────────────────────────────────────────────────────

    def parse(self, pdf_path: Path) -> ParseResult:
        pages_text = self.extract_text_from_pdf(pdf_path)
        warnings: list[str] = []

        info = self._extract_info(pages_text[0] if pages_text else "")
        year = info.period_end.year if info.period_end else date.today().year

        all_lines: list[str] = []
        for text in pages_text:
            all_lines.extend(text.split('\n'))

        transactions: list[Transaction] = []
        i = 0

        while i < len(all_lines):
            line = all_lines[i].strip()

            if not line or self._should_skip(line):
                i += 1
                continue

            tx = self._try_parse_transaction(line, year)
            if tx:
                # Look ahead for foreign currency info
                if i + 1 < len(all_lines):
                    next_line = all_lines[i + 1].strip()
                    foreign_match = self.FOREIGN_RE.search(next_line)
                    if foreign_match:
                        tx.original_amount = self.parse_mx_amount(foreign_match.group(1))
                        tx.original_currency = "USD"  # most common
                        tx.exchange_rate = float(foreign_match.group(2))
                        # Try to detect currency
                        curr_match = re.match(r'(USD|EUR|GBP)', next_line)
                        if curr_match:
                            tx.original_currency = curr_match.group(1)
                        i += 1

                transactions.append(tx)

            i += 1

        return ParseResult(info=info, transactions=transactions, warnings=warnings)

    # ── Info extraction ───────────────────────────────────────────────────────

    def _extract_info(self, first_page: str) -> StatementInfo:
        info = StatementInfo(bank=self.bank_name)

        # Account / card number
        acct_match = re.search(r'(\d{4}[\s*]{1,4}\d{4}[\s*]{1,4}\d{4}[\s*]{1,4}\d{4})', first_page)
        if acct_match:
            info.account_number = re.sub(r'[\s*]+', '', acct_match.group(1))

        # Period
        period_match = re.search(
            r'[Dd]el\s+(\d{1,2})\s+(?:de\s+)?([A-Za-záéíóúñ]+)\s+'
            r'al\s+(\d{1,2})\s+(?:de\s+)?([A-Za-záéíóúñ]+)\s+(?:de\s+)?(\d{4})',
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
        name_match = re.search(r'(?:NOMBRE|Nombre|TITULAR)[:\s]+([A-ZÁÉÍÓÚÑ ]+)', first_page)
        if name_match:
            info.cardholder = name_match.group(1).strip()

        return info

    # ── Transaction parsing ───────────────────────────────────────────────────

    def _try_parse_transaction(self, line: str, year: int) -> Transaction | None:
        for pattern in self.TX_PATTERNS:
            match = pattern.match(line)
            if match:
                return self._build_from_match(match, year)
        return None

    def _build_from_match(self, match: re.Match, year: int) -> Transaction | None:
        groups = match.groups()

        day = int(groups[0])
        month_raw = groups[1]

        # Determine which pattern matched based on group count
        if len(groups) == 5:
            # Pattern with month abbreviation (no year in date)
            description = groups[2].strip()
            amount_str = groups[3]
            is_negative = groups[4] == '-'
            tx_year = year
        elif len(groups) == 6:
            # Pattern with explicit year
            year_raw = groups[2]
            description = groups[3].strip()
            amount_str = groups[4]
            is_negative = groups[5] == '-'
            tx_year = int(year_raw) if year_raw else year
            if tx_year < 100:
                tx_year += 2000
        else:
            return None

        # Resolve month
        month = self._resolve_month(month_raw)
        if month is None:
            return None

        try:
            tx_date = date(tx_year, month, day)
        except ValueError:
            return None

        amount = self.parse_mx_amount(amount_str)
        is_credit = is_negative or self._is_credit(description)

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
        if month_raw.isdigit():
            m = int(month_raw)
            return m if 1 <= m <= 12 else None
        return MONTHS_ABBREV.get(month_raw.lower()[:3])

    def _is_credit(self, description: str) -> bool:
        desc = description.upper()
        return any(kw in desc for kw in [
            "PAGO", "ABONO", "DEVOLUCION", "DEVOLUCIÓN", "BONIFICACION",
        ])

    def _classify(self, description: str, is_credit: bool) -> TransactionType:
        desc = description.upper()
        if any(kw in desc for kw in ["PAGO", "ABONO"]):
            return TransactionType.PAYMENT
        if "INTERES" in desc:
            return TransactionType.INTEREST
        if "COMISION" in desc or "COMISIÓN" in desc or "ANUALIDAD" in desc:
            return TransactionType.FEE
        if "IVA" in desc:
            return TransactionType.TAX
        if is_credit:
            return TransactionType.CREDIT
        return TransactionType.CHARGE

    def _should_skip(self, line: str) -> bool:
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, line):
                return True
        return False
