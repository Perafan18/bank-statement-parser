# Adding a New Bank Parser

This is a step-by-step guide. Use the BBVA parser (`src/bankparser/parsers/bbva.py`) as the reference implementation since it's the cleanest example.

## Step 1: Study the PDF

Before writing any code, extract the text from your bank's PDF to understand its structure:

```python
import pdfplumber

with pdfplumber.open("statement.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n{'='*60}")
        print(f"PAGE {i + 1}")
        print('='*60)
        print(page.extract_text())
```

If pdfplumber returns garbled text (e.g. `(cid:XX)` characters), the PDF uses CID-encoded fonts and you'll need OCR. See the HSBC parser for how to handle this.

Identify:
- **Bank identifiers** on the first page (for `can_parse()`)
- **Statement metadata**: account number, period, cardholder name, balances
- **Transaction format**: what columns exist, how dates are formatted, how credits vs charges are distinguished
- **Section markers**: headers like "CARGOS Y ABONOS", totals lines, page breaks
- **Special transactions**: MSI installments, foreign currency, fees, interest

## Step 2: Create the parser file

Create `src/bankparser/parsers/mybank.py`:

```python
"""Parser for MyBank Mexico credit card statements."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType
from bankparser.parsers.base import BaseParser


class MyBankParser(BaseParser):
    """Parses MyBank Mexico PDF statements."""

    bank_name = "mybank"

    # ── Detection ─────────────────────────────────────────────────────────

    def can_parse(self, pdf_path: Path) -> bool:
        """Check if this PDF belongs to MyBank.

        Look for bank-specific text on the first page. Use multiple
        identifiers to avoid false positives (e.g. a BBVA statement
        that mentions "amex" in an address).
        """
        text = self.extract_first_page_text(pdf_path).lower()
        return "mybank" in text or "my bank mexico" in text

    # ── Regexes ───────────────────────────────────────────────────────────

    # Define regex patterns as class-level compiled constants.
    # Use re.compile() for performance (these run on every line).
    #
    # Example: transaction line "15/01/2026 OXXO TONALA $48.50"
    TX_RE = re.compile(
        r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+\$([\d,]+\.\d{2})\s*$'
    )

    # Lines to skip (headers, totals, noise)
    SKIP_PATTERNS = [
        re.compile(r'^FECHA\s+DESCRIPCION'),  # table header
        re.compile(r'^TOTAL'),                  # totals row
    ]

    # ── Main parse ────────────────────────────────────────────────────────

    def parse(self, pdf_path: Path) -> ParseResult:
        pages_text = self.extract_text_from_pdf(pdf_path)
        warnings: list[str] = []

        full_text = "\n".join(pages_text)
        info = self._extract_info(full_text)

        # Collect all lines from all pages
        all_lines: list[str] = []
        for text in pages_text:
            all_lines.extend(text.split('\n'))

        transactions = self._parse_transactions(all_lines, warnings)

        # Propagate cardholder from statement info
        if info.cardholder:
            for tx in transactions:
                tx.cardholder = info.cardholder

        return ParseResult(info=info, transactions=transactions, warnings=warnings)

    # ── Info extraction ───────────────────────────────────────────────────

    def _extract_info(self, text: str) -> StatementInfo:
        info = StatementInfo(bank=self.bank_name)
        # Extract account number, period, cardholder, etc. with regex
        # ...
        return info

    # ── Transaction parsing ───────────────────────────────────────────────

    def _parse_transactions(
        self, lines: list[str], warnings: list[str],
    ) -> list[Transaction]:
        transactions: list[Transaction] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or self._should_skip(stripped):
                continue

            match = self.TX_RE.match(stripped)
            if not match:
                continue

            # Parse fields from the match
            date_str = match.group(1)
            description = match.group(2).strip()
            amount = self.parse_mx_amount(match.group(3))

            # Classify the transaction
            tx_type = self._classify(description, is_credit=False)

            tx = Transaction(
                date=self._parse_date(date_str),
                description=description,
                amount=amount,
                currency="MXN",
                bank=self.bank_name,
                tx_type=tx_type,
            )
            transactions.append(tx)

        return transactions

    # ── Helpers ────────────────────────────────────────────────────────────

    def _classify(self, description: str, is_credit: bool) -> TransactionType:
        """Classify a transaction based on description and sign."""
        desc = description.upper()
        if "PAGO" in desc:
            return TransactionType.PAYMENT
        if "INTERES" in desc:
            return TransactionType.INTEREST
        if "IVA" in desc:
            return TransactionType.TAX
        if "COMISION" in desc or "ANUALIDAD" in desc:
            return TransactionType.FEE
        if is_credit:
            return TransactionType.CREDIT
        return TransactionType.CHARGE

    def _should_skip(self, line: str) -> bool:
        """Check if a line is a header, total, or noise."""
        for pattern in self.SKIP_PATTERNS:
            if pattern.match(line):
                return True
        return False
```

## Step 3: Register the parser

In `src/bankparser/parsers/__init__.py`, add your parser to `create_default_registry()`:

```python
def create_default_registry() -> ParserRegistry:
    from bankparser.parsers.amex import AmexParser
    from bankparser.parsers.bbva import BBVAParser
    from bankparser.parsers.hsbc import HSBCParser
    from bankparser.parsers.mybank import MyBankParser  # add import

    registry = ParserRegistry()
    registry.register(AmexParser())
    registry.register(BBVAParser())
    registry.register(HSBCParser())
    registry.register(MyBankParser())  # register it
    return registry
```

## Step 4: Add bank-specific categorization rules

In `src/bankparser/database.py`, add rules to `DEFAULT_RULES`:

```python
DEFAULT_RULES = [
    # ... existing rules ...

    # MyBank-specific
    ("PAGO DOMICILIADO", "Payment", "mybank", 100),
    ("COMISION MENSUAL", "Fees", "mybank", 100),
]
```

Note: these only apply to new databases. Existing users must add rules manually via the CLI.

## Step 5: Write tests

Create `tests/test_parsers/test_mybank.py`. Use inline text fixtures (not real PDFs) so tests run anywhere:

```python
"""Tests for the MyBank parser."""

from datetime import date
import pytest
from bankparser.models import TransactionType
from bankparser.parsers.mybank import MyBankParser


# Use real text extracted from a statement (redacted)
MYBANK_INFO_TEXT = """MyBank Mexico S.A.
Numero de cuenta: 1234567890
Periodo: 01/01/2026 al 31/01/2026
JUAN GARCIA LOPEZ
"""

MYBANK_TRANSACTIONS_TEXT = """\
FECHA DESCRIPCION MONTO
15/01/2026 OXXO TONALA $48.50
16/01/2026 PAGO RECIBIDO -$10,000.00
TOTAL $48.50
"""


class TestMyBankParser:
    @pytest.fixture
    def parser(self):
        return MyBankParser()

    def test_bank_name(self, parser):
        assert parser.bank_name == "mybank"

    def test_extract_info(self, parser):
        info = parser._extract_info(MYBANK_INFO_TEXT)
        assert info.bank == "mybank"
        # assert info.account_number == "1234567890"
        # assert info.cardholder == "JUAN GARCIA LOPEZ"

    def test_parse_transactions(self, parser):
        lines = MYBANK_TRANSACTIONS_TEXT.split("\n")
        transactions = parser._parse_transactions(lines, [])
        assert len(transactions) >= 1

    def test_classify_payment(self, parser):
        assert parser._classify("PAGO RECIBIDO", True) == TransactionType.PAYMENT

    def test_classify_charge(self, parser):
        assert parser._classify("OXXO TONALA", False) == TransactionType.CHARGE
```

Run tests: `pytest tests/test_parsers/test_mybank.py -v`

## Step 6: Test with a real PDF

Put a real (redacted) statement in `samples/mybank/` (excluded from git by `*.pdf` in `.gitignore`):

```bash
bankparse parse samples/mybank/statement.pdf --bank mybank
```

## BaseParser helpers available to all parsers

| Helper | Description |
|--------|-------------|
| `parse_spanish_date(day, month_name, year)` | Full Spanish month names: "Enero", "Febrero", etc. |
| `parse_mx_amount(amount_str)` | Mexican format: `"$1,234.56"` → `1234.56`. Raises `ValueError` with context on bad input. |
| `extract_text_from_pdf(pdf_path)` | Returns `list[str]` (one string per page) via pdfplumber |
| `extract_first_page_text(pdf_path)` | Returns first page text only (fast, for detection) |
| `extract_text_with_ocr(pdf_path, dpi, psm)` | OCR via pytesseract + pdf2image. Requires `[ocr]` extras + system packages. |

## Common patterns in Mexican bank statements

- **Dates**: `DD de Mes` (Amex), `DD-mmm-YYYY` (BBVA/HSBC), `DD/MM/YYYY`
- **Amounts**: Always `$X,XXX.XX` format with comma thousands separator
- **Credits/payments**: Indicated by `-` sign, `CR` suffix, or separate column
- **MSI**: "Meses sin intereses" installments, usually in a separate section
- **Foreign currency**: Continuation line with original amount, currency code, and exchange rate
- **IVA**: Tax on fees/interest, usually a separate line item
