"""Parser for HSBC Mexico TDC (credit card) statements.

HSBC Mexico TDC PDF statements use CID-encoded fonts that pdfplumber
cannot decode, so this parser uses OCR (pytesseract + pdf2image).

Transaction format from OCR:
  DD-Mmm-YYYY DD-Mmm-YYYY [artifacts]DESCRIPTION $AMOUNT    (charge)
  DD-Mmm-YYYY DD-Mmm-YYYY [artifacts]DESCRIPTION A $AMOUNT  (credit/payment)

Foreign currency transactions have a MONEDA EXTRANJERA line:
  DD-Mmm-YYYY DD-Mmm-YYYY MONEDA EXTRANJERA: 9.98 USD TC: 17.99 ... $179.51

OCR artifacts from table borders (|, _, [) are cleaned automatically.

NOTE: OCR quality varies. Dense transaction tables may have amounts
split to separate lines. The parser extracts what it can reliably
parse and warns about discrepancies against the statement totals.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType
from bankparser.parsers.base import BaseParser

MONTHS_ABBREV = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4,
    "may": 5, "jun": 6, "jul": 7, "ago": 8,
    "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}


class HSBCParser(BaseParser):
    """Parses HSBC Mexico TDC PDF statements using OCR."""

    bank_name = "hsbc"

    # ── Detection ─────────────────────────────────────────────────────────────

    def can_parse(self, pdf_path: Path) -> bool:
        # Try pdfplumber first (fast)
        text = self.extract_first_page_text(pdf_path).lower()
        if "hsbc" in text:
            return True
        # Fall back to OCR (slow but necessary for CID-encoded fonts)
        try:
            pages = self.extract_text_with_ocr(pdf_path, dpi=150)
            if pages:
                return "hsbc" in pages[0].lower()
        except Exception:
            pass
        return False

    # ── Regexes ───────────────────────────────────────────────────────────────

    _DATE_PAT = r'(\d{1,2}-[A-Za-z]{3}-\d{4})'

    # Full transaction line: two dates + description + amount
    # OCR artifacts before amount: 1+1$, [+1$, |-]$, || $ (table border chars)
    # Extra digit after year tolerated (OCR may produce "20268" for "2026")
    TX_RE = re.compile(
        _DATE_PAT + r'\s+' + _DATE_PAT + r'\d?\s*[_|[\])\s]*'
        r'(.+?)\s*(?:[|+\[\]1\-]+\s*)?\$?\s*([\d,]+\.\d{2})\s*$'
    )

    # Transaction line without amount (OCR split amount to another line)
    TX_NO_AMOUNT_RE = re.compile(
        _DATE_PAT + r'\s+' + _DATE_PAT + r'\d?\s*[_|[\])\s]*(.+?)\s*$'
    )

    # MONEDA EXTRANJERA line (foreign currency)
    # e.g. "12-Feb-2026 12-Feb-2026 MONEDA EXTRANJERA: 9.98 USD TC: 17.28657 ... $172.52"
    FOREIGN_RE = re.compile(
        r'MONEDA EXTRANJERA:\s*([\d,.]+)\s+([A-Z]{3})\s+TC:\s*([\d,.]+)'
    )

    # MXN amount at end of MONEDA EXTRANJERA line (may have OCR artifacts)
    FOREIGN_MXN_RE = re.compile(r'[\$\[]\s*([\d,]+\.\d{2})\s*$')

    # Standalone amount line (orphaned by OCR)
    AMOUNT_LINE_RE = re.compile(r'^\s*-?\s*\$?\s*([\d,]+\.\d{2})\s*$')

    # Section markers
    SECTION_RE = re.compile(r'CARGOS,?\s*ABONOS\s+Y\s+COMPRAS\s+REGULARES')
    TARJETA_RE = re.compile(r'Tarjeta\s+(titular|adicional)\s+(\d+)', re.IGNORECASE)
    TOTAL_RE = re.compile(r'^Total\s*(cargos|abonos)', re.IGNORECASE)

    # Lines to skip inside transaction section
    SKIP_PATTERNS = [
        re.compile(r'^i+\.\s+Fecha'),
        re.compile(r'^operación'),
        re.compile(r'^l?i+\.\s+Fecha'),
        re.compile(r'^Notas:'),
        re.compile(r'^Ver notas'),
        re.compile(r'^Número de cuenta'),
        re.compile(r'^Página'),
        re.compile(r'^>?\s*H\s*S\s*B\s*C'),
        re.compile(r'^\d{4,5}\s+\d{2}\s*$'),
    ]

    # ── Main parse ────────────────────────────────────────────────────────────

    def parse(self, pdf_path: Path) -> ParseResult:
        pages_text = self.extract_text_with_ocr(pdf_path)
        warnings: list[str] = []

        full_text = "\n".join(pages_text)
        info = self._extract_info(full_text)

        all_lines: list[str] = []
        for text in pages_text:
            all_lines.extend(text.split('\n'))

        transactions = self._parse_transactions(all_lines, warnings)

        return ParseResult(info=info, transactions=transactions, warnings=warnings)

    # ── Info extraction ───────────────────────────────────────────────────────

    def _extract_info(self, text: str) -> StatementInfo:
        info = StatementInfo(bank=self.bank_name)

        # Account: NÚMERO DE CUENTA: 4524 2160 2342 9864
        # OCR may drop the accent: "NUMERO" vs "NÚMERO"
        acct_match = re.search(
            r'N[ÚU]MERO DE CUENTA:\s*(\d{4}\s*\d{4}\s*\d{4}\s*\d{4})', text
        )
        if acct_match:
            info.account_number = acct_match.group(1).replace(' ', '')

        # Period: Periodo: 15-Dic-2025 al 12-Ene-2026
        period_match = re.search(
            r'Periodo:\s*' + self._DATE_PAT + r'\s+al\s+' + self._DATE_PAT,
            text,
        )
        if period_match:
            try:
                info.period_start = self._parse_hsbc_date(period_match.group(1))
                info.period_end = self._parse_hsbc_date(period_match.group(2))
            except (ValueError, KeyError):
                pass

        # Cardholder: line after "TU PAGO REQUERIDO ESTE PERIODO"
        name_match = re.search(
            r'TU PAGO REQUERIDO ESTE PERIODO\n([A-ZÁÉÍÓÚÑ ]+)\n', text
        )
        if name_match:
            info.cardholder = name_match.group(1).strip()

        # Cut date: Fecha de corte: 12-Ene-2026
        cut_match = re.search(
            r'Fecha de corte:\s*' + self._DATE_PAT, text
        )
        if cut_match:
            try:
                info.cut_date = self._parse_hsbc_date(cut_match.group(1))
            except (ValueError, KeyError):
                pass

        # Previous balance: Adeudo del periodo anterior |= $29,093.55
        balance_match = re.search(
            r'Adeudo del periodo anterior\s*[|=\s]*\$\s*([\d,]+\.\d{2})', text
        )
        if balance_match:
            info.previous_balance = self.parse_mx_amount(balance_match.group(1))

        return info

    # ── Date parsing ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_hsbc_date(date_str: str) -> date:
        """Parse HSBC date 'DD-Mmm-YYYY' (e.g. '15-Dic-2025').

        Handles common OCR errors: O→0 in day/year, l→1 in day/year.
        """
        parts = date_str.split('-')
        if len(parts) != 3:
            raise ValueError(f"Invalid date: {date_str}")

        day_s, month_s, year_s = parts
        # Fix OCR errors in day and year (not month)
        for old, new in [('O', '0'), ('o', '0'), ('l', '1'), ('S', '5')]:
            day_s = day_s.replace(old, new)
            year_s = year_s.replace(old, new)

        month = MONTHS_ABBREV.get(month_s.lower())
        if month is None:
            raise ValueError(f"Unknown month: {month_s}")

        return date(int(year_s), month, int(day_s))

    # ── Transaction parsing ───────────────────────────────────────────────────

    @staticmethod
    def _fix_ocr_digits(line: str) -> str:
        """Fix common OCR digit substitutions in date positions.

        Replaces letter O with digit 0 when adjacent to other digits
        (e.g. 'O5-Feb-2026' → '05-Feb-2026', '2O26' → '2026').
        """
        line = re.sub(r'(?<=\d)O', '0', line)
        line = re.sub(r'O(?=\d)', '0', line)
        return line

    def _parse_transactions(self, lines: list[str], warnings: list[str]) -> list[Transaction]:
        transactions: list[Transaction] = []
        in_section = False
        pending_description: str | None = None
        i = 0

        while i < len(lines):
            stripped = self._fix_ocr_digits(lines[i].strip())

            if not stripped:
                i += 1
                continue

            # Detect transaction section start
            if self.SECTION_RE.search(stripped):
                in_section = True
                i += 1
                continue

            # Detect section end (totals)
            if self.TOTAL_RE.match(stripped):
                # Don't exit section - there may be more Total lines
                i += 1
                continue

            # Skip non-transaction-section content
            if not in_section:
                i += 1
                continue

            # Skip known header/noise lines inside the section
            if self._should_skip(stripped):
                i += 1
                continue

            # Skip cardholder section headers
            if self.TARJETA_RE.search(stripped):
                i += 1
                continue

            # Handle MONEDA EXTRANJERA (foreign currency) line
            if 'MONEDA EXTRANJERA' in stripped:
                tx = self._parse_foreign_tx(stripped, pending_description)
                if tx:
                    transactions.append(tx)
                pending_description = None
                i += 1
                continue

            # Try full transaction line (dates + description + amount)
            tx_match = self.TX_RE.match(stripped)
            if tx_match:
                tx = self._build_transaction(tx_match, stripped)
                if tx:
                    transactions.append(tx)
                pending_description = None
                i += 1
                continue

            # Try transaction line without amount (OCR split)
            no_amt_match = self.TX_NO_AMOUNT_RE.match(stripped)
            if no_amt_match:
                desc = self._clean_description(no_amt_match.group(3))
                # Look ahead for an amount line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    amt_match = self.AMOUNT_LINE_RE.match(lines[j].strip())
                    if amt_match:
                        amount = self.parse_mx_amount(amt_match.group(1))
                        is_credit = 'SUPAGO' in desc.upper() or 'PAGO' in desc.upper()
                        tx = self._build_transaction_manual(
                            no_amt_match.group(1), desc, amount, is_credit,
                        )
                        if tx:
                            transactions.append(tx)
                        i = j + 1
                        pending_description = None
                        continue
                # No amount found - store description for potential foreign tx
                pending_description = desc
                i += 1
                continue

            # Non-date line inside section - could be a description for foreign tx
            if not stripped.startswith('$') and not self.AMOUNT_LINE_RE.match(stripped):
                # Only store if it looks like a merchant description
                if re.search(r'[A-Z]{2,}', stripped):
                    pending_description = self._clean_description(stripped)

            i += 1

        return transactions

    # OCR table sign indicators between description and amount:
    #   |+| → charge (OCR reads as 1+1, [+1, [+])
    #   |-| → credit/abono (OCR reads as |-], |-[, ||)
    # "||" = |-| with middle garbled (|+| reads as 1+1, not ||)
    ABONO_INDICATOR_RE = re.compile(r'[|\[]\s*-\s*[|\[\]]|(?<!\+)\|\|(?!\+)')

    def _build_transaction(self, match: re.Match, original_line: str) -> Transaction | None:
        """Build a Transaction from a TX_RE match."""
        op_date_str = match.group(1)
        description = self._clean_description(match.group(3))
        amount_str = match.group(4)

        # Detect credit/abono from description keywords or OCR table indicators
        # The table has |-| for credits (OCR: |-], ||) and |+| for charges (OCR: 1+1, [+1)
        is_credit = "SUPAGO" in description.upper()
        if not is_credit:
            # Check for minus indicator in the junk between description and amount
            # Extract the part between description end and amount start
            desc_end = original_line.find(description) + len(description) if description in original_line else -1
            if desc_end > 0:
                junk = original_line[desc_end:original_line.rfind(amount_str)]
                is_credit = bool(self.ABONO_INDICATOR_RE.search(junk))
        # Clean trailing "A", "||" or other OCR artifacts from description
        description = re.sub(r'\s*(?:A|\|{1,2})\s*$', '', description)

        try:
            tx_date = self._parse_hsbc_date(op_date_str)
        except (ValueError, KeyError):
            return None

        amount = self.parse_mx_amount(amount_str)
        if is_credit:
            amount = -amount

        tx_type = self._classify(description, is_credit)

        return Transaction(
            date=tx_date,
            description=description,
            amount=amount,
            currency="MXN",
            bank=self.bank_name,
            tx_type=tx_type,
        )

    def _build_transaction_manual(
        self, op_date_str: str, description: str, amount: float, is_credit: bool,
    ) -> Transaction | None:
        """Build a Transaction from manually extracted fields."""
        try:
            tx_date = self._parse_hsbc_date(op_date_str)
        except (ValueError, KeyError):
            return None

        if is_credit:
            amount = -amount

        tx_type = self._classify(description, is_credit)

        return Transaction(
            date=tx_date,
            description=description,
            amount=amount,
            currency="MXN",
            bank=self.bank_name,
            tx_type=tx_type,
        )

    def _parse_foreign_tx(
        self, line: str, pending_description: str | None,
    ) -> Transaction | None:
        """Parse a MONEDA EXTRANJERA line into a foreign-currency transaction."""
        foreign_match = self.FOREIGN_RE.search(line)
        if not foreign_match:
            return None

        original_amount = float(foreign_match.group(1).replace(',', ''))
        original_currency = foreign_match.group(2)
        exchange_rate = float(foreign_match.group(3).replace(',', ''))

        # Get MXN amount from end of line, falling back to calculated value
        # OCR may garble "$179.51" into "[5179.51" or "[517252" (no decimal)
        expected_mxn = round(original_amount * exchange_rate, 2)
        mxn_match = self.FOREIGN_MXN_RE.search(line)
        if mxn_match:
            mxn_amount = self.parse_mx_amount(mxn_match.group(1))
            # Sanity check: if >50% off from calculated, use calculated
            if abs(mxn_amount - expected_mxn) / expected_mxn > 0.5:
                mxn_amount = expected_mxn
        else:
            # OCR garbled the amount (no decimal point), use calculated
            mxn_amount = expected_mxn

        # Get date from beginning of line
        date_match = re.match(self._DATE_PAT, line)
        if not date_match:
            return None

        try:
            tx_date = self._parse_hsbc_date(date_match.group(1))
        except (ValueError, KeyError):
            return None

        description = pending_description or f"Foreign purchase ({original_currency})"

        return Transaction(
            date=tx_date,
            description=description,
            amount=mxn_amount,
            currency="MXN",
            bank=self.bank_name,
            tx_type=TransactionType.CHARGE,
            original_amount=original_amount,
            original_currency=original_currency,
            exchange_rate=exchange_rate,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _clean_description(desc: str) -> str:
        """Remove OCR artifacts from description."""
        # Remove leading pipe, underscore, bracket artifacts
        desc = re.sub(r'^[_|[\])\s]+', '', desc)
        # Remove trailing underscores and artifacts
        desc = re.sub(r'[_|]+$', '', desc)
        # Collapse multiple spaces
        desc = re.sub(r'\s{2,}', ' ', desc)
        return desc.strip()

    def _classify(self, description: str, is_credit: bool) -> TransactionType:
        """Classify a transaction based on description and credit flag.

        HSBC payments use "SUPAGO GRACIAS" as description. We match "SUPAGO"
        specifically and require "PAGO" as a word boundary (not inside
        "MERPAGO" or "PAGODA").
        """
        desc = description.upper()

        if "SUPAGO" in desc:
            return TransactionType.PAYMENT
        if re.search(r'\bPAGO\b', desc) or re.search(r'\bABONO\b', desc):
            return TransactionType.PAYMENT
        if "INTERES" in desc:
            return TransactionType.INTEREST
        if any(kw in desc for kw in ["COMISION", "COMISIÓN", "ANUALIDAD"]):
            return TransactionType.FEE
        if "IVA" in desc:
            return TransactionType.TAX
        if is_credit:
            return TransactionType.CREDIT

        return TransactionType.CHARGE

    def _should_skip(self, line: str) -> bool:
        """Check if a line should be skipped inside the transaction section."""
        for pattern in self.SKIP_PATTERNS:
            if pattern.match(line):
                return True
        return False
