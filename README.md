# Bank Statement Parser

[![CI](https://github.com/Perafan18/bank-statement-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/Perafan18/bank-statement-parser/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/bankparser)](https://pypi.org/project/bankparser/)
[![Python](https://img.shields.io/pypi/pyversions/bankparser)](https://pypi.org/project/bankparser/)
[![License](https://img.shields.io/github/license/Perafan18/bank-statement-parser)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://Perafan18.github.io/bank-statement-parser/)

Parse Mexican bank statement PDFs (American Express, BBVA, HSBC) into CSV files
compatible with personal finance apps like [Sure](https://github.com/we-promise/sure),
Monarch Money, and others.

## Features

- **Multi-bank support**: Amex, BBVA, HSBC Mexico with auto-detection
- **Smart categorization**: SQLite-backed rules with priority, bank-specific patterns, and ~80 pre-seeded rules
- **Multiple export formats**: Generic (all fields), Sure/Maybe Finance, Monarch Money
- **MSI tracking**: Installment info preserved (cargo X de Y), both "sin intereses" and "con intereses"
- **Foreign currency**: Original amount, currency code, and exchange rate preserved
- **Multi-cardholder**: Distinguishes titular vs additional cardholders (Amex)
- **Filtering**: By cardholder, transaction type, fees, MSI, charges-only
- **OCR fallback**: HSBC statements with CID-encoded fonts are parsed via Tesseract OCR

## Installation

```bash
git clone https://github.com/Perafan18/bank-statement-parser.git
cd bank-statement-parser
pip install -e ".[dev]"
```

### OCR support (required for HSBC)

HSBC Mexico statements use CID-encoded fonts that pdfplumber cannot decode. To parse HSBC statements, install the OCR dependencies:

```bash
# Python packages
pip install -e ".[ocr]"

# System packages (Ubuntu/Debian)
sudo apt install tesseract-ocr tesseract-ocr-spa poppler-utils

# macOS
brew install tesseract poppler
```

Without these, BBVA and Amex statements will work normally, but HSBC parsing will show a clear error message with install instructions.

## Quick Start

```bash
# Parse a statement (auto-detects bank)
bankparse parse statement.pdf

# Specify bank and format
bankparse parse statement.pdf --bank amex --format sure

# Multiple files at once
bankparse parse *.pdf -f sure -o all_transactions.csv

# Only actual purchases (no fees, interest, MSI)
bankparse parse statement.pdf --charges-only

# Exclude fees and interest but keep everything else
bankparse parse statement.pdf --no-fees

# Exclude MSI installments
bankparse parse statement.pdf --no-msi

# Filter by cardholder name (substring match)
bankparse parse statement.pdf --cardholder garcia
```

## Category Management

Categories and rules live in a SQLite database at `~/.bankparser/bankparser.db`. The database is created automatically on first run with ~22 categories and ~80 rules pre-seeded.

```bash
# List all categories
bankparse categories list

# Add a new category
bankparse categories add "Pets" --icon "🐕"

# Remove a category (also removes its rules)
bankparse categories remove "Pets" --yes

# List all rules (sorted by priority)
bankparse rules list

# List rules for a specific bank
bankparse rules list --bank bbva

# Add a custom rule (higher priority = checked first)
bankparse rules add "COSTCO" "Groceries"
bankparse rules add "VET" "Pets" --bank amex --priority 20

# Remove a rule by ID
bankparse rules remove 42

# Show database stats
bankparse info
```

### How categorization works

Transactions are categorized in this order:

1. **Type override**: Payments, Interest, Fees, Tax, MSI, and MSI Adjustment transactions are auto-categorized by their `TransactionType` regardless of description
2. **Rule matching**: The description is matched against `category_rules` (case-insensitive substring match, ordered by priority descending, bank-specific rules checked alongside wildcard `*` rules)
3. **Fallback**: If no rule matches, the transaction is categorized as "Uncategorized"

## Export Formats

| Format    | App                  | Key Columns                                                |
|-----------|----------------------|------------------------------------------------------------|
| `generic` | Any / raw analysis   | date, description, amount, currency, bank, cardholder, type, category, installment, reference, original_amount, original_currency, exchange_rate, tags |
| `sure`    | Sure / Maybe Finance | date, name, amount, currency, category, tags, account, notes |
| `monarch` | Monarch Money        | Date, Merchant, Amount, Category, Account, Tags, Notes, Original Currency |

### Amount conventions

- **Charges** are positive amounts (e.g. `499.00`)
- **Payments and credits** are negative amounts (e.g. `-10000.00`)
- All amounts are in MXN unless `original_currency` is set

## Architecture

```
PDF ──→ Parser (auto-detect) ──→ ParseResult ──→ Categorizer ──→ Exporter ──→ CSV
         │                         │                │
         │ can_parse()             │ StatementInfo   │ SQLite rules
         │ parse()                 │ Transaction[]   │ (priority-ordered)
         │                         │ warnings[]      │
         ▼                         ▼                 ▼
    ParserRegistry            models.py          database.py
```

### Core models (`models.py`)

| Model | Purpose |
|-------|---------|
| `Transaction` | A single transaction. Every parser produces these, every exporter consumes them. Fields: date, description, amount, currency, bank, cardholder, tx_type, category, installment, reference, original_amount, original_currency, exchange_rate, tags |
| `TransactionType` | Enum: `CHARGE`, `PAYMENT`, `CREDIT`, `FEE`, `INTEREST`, `TAX`, `MSI`, `MSI_ADJUSTMENT`, `TRANSFER` |
| `StatementInfo` | Statement metadata: bank, account_number, cardholder, period dates, balances |
| `ParseResult` | Container: `info` (StatementInfo) + `transactions` (list) + `warnings` (list) |

### Parsers (`parsers/`)

Registry pattern with auto-detection. Each parser extends `BaseParser`:

| Parser | Bank | Text extraction | Notes |
|--------|------|-----------------|-------|
| `AmexParser` | American Express Mexico | pdfplumber | Multi-cardholder, MSI, foreign currency (USD), RFC references |
| `BBVAParser` | BBVA Mexico (Bancomer) TDC | pdfplumber | Two-section parsing (regular + MSI sin/con intereses), `+/-` sign convention |
| `HSBCParser` | HSBC Mexico TDC | OCR (pytesseract) | CID-encoded fonts require OCR, extensive artifact cleanup |

### Exporters (`exporters/`)

Registry pattern. Each exporter extends `BaseExporter`:

| Exporter | Format | Target app |
|----------|--------|------------|
| `GenericExporter` | All 14 fields | Raw analysis |
| `SureExporter` | 8 fields with tags/notes | Sure / Maybe Finance |
| `MonarchExporter` | 8 fields with account label | Monarch Money |

### Database (`database.py`)

SQLite at `~/.bankparser/bankparser.db` with two tables:

- **`categories`**: name (unique), parent_name, icon
- **`category_rules`**: pattern, category_name, bank (`*` = all), priority (higher = checked first)

Seeded on first run with ~22 categories (Shopping, Food & Dining, Groceries, Transportation, Subscriptions, etc.) and ~80 rules for common Mexican merchants and bank-specific patterns.

## Project Structure

```
bank-statement-parser/
├── src/bankparser/
│   ├── __init__.py          # Package version
│   ├── cli.py               # Click CLI: parse, categories, rules, info
│   ├── models.py            # Transaction, StatementInfo, ParseResult, TransactionType
│   ├── database.py          # SQLite schema, seed data, CRUD, rule matching
│   ├── categorizer.py       # Type overrides → rule matching → "Uncategorized"
│   ├── parsers/
│   │   ├── __init__.py      # ParserRegistry + create_default_registry()
│   │   ├── base.py          # BaseParser: abstract interface + shared helpers
│   │   ├── amex.py          # American Express Mexico
│   │   ├── bbva.py          # BBVA Mexico (Bancomer) TDC
│   │   └── hsbc.py          # HSBC Mexico TDC (OCR-based)
│   └── exporters/
│       ├── __init__.py      # Exporter registry
│       ├── base.py          # BaseExporter: abstract interface + CSV writing
│       ├── generic.py       # All fields export
│       ├── sure.py          # Sure / Maybe Finance format
│       └── monarch.py       # Monarch Money format
├── tests/
│   ├── conftest.py          # Shared fixtures: tmp_db, sample_transactions
│   ├── test_models.py       # Transaction, ParseResult tests
│   ├── test_categorizer.py  # Database + Categorizer tests
│   ├── test_parsers/
│   │   ├── test_amex.py     # Amex parser + BaseParser helper tests
│   │   ├── test_bbva.py     # BBVA parser tests (inline text fixtures)
│   │   └── test_hsbc.py     # HSBC parser tests (inline text fixtures)
│   └── test_exporters/
│       └── test_exporters.py  # All exporter tests
├── pyproject.toml
├── CLAUDE.md                # AI assistant instructions
└── README.md
```

## Adding a New Bank Parser

This is a step-by-step guide. Use the BBVA parser (`src/bankparser/parsers/bbva.py`) as the reference implementation since it's the cleanest example.

### Step 1: Study the PDF

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

### Step 2: Create the parser file

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

### Step 3: Register the parser

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

### Step 4: Add bank-specific categorization rules

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

### Step 5: Write tests

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

### Step 6: Test with a real PDF

Put a real (redacted) statement in `samples/mybank/` (excluded from git by `*.pdf` in `.gitignore`):

```bash
bankparse parse samples/mybank/statement.pdf --bank mybank
```

### BaseParser helpers available to all parsers

| Helper | Description |
|--------|-------------|
| `parse_spanish_date(day, month_name, year)` | Full Spanish month names: "Enero", "Febrero", etc. |
| `parse_mx_amount(amount_str)` | Mexican format: `"$1,234.56"` → `1234.56`. Raises `ValueError` with context on bad input. |
| `extract_text_from_pdf(pdf_path)` | Returns `list[str]` (one string per page) via pdfplumber |
| `extract_first_page_text(pdf_path)` | Returns first page text only (fast, for detection) |
| `extract_text_with_ocr(pdf_path, dpi, psm)` | OCR via pytesseract + pdf2image. Requires `[ocr]` extras + system packages. |

### Common patterns in Mexican bank statements

- **Dates**: `DD de Mes` (Amex), `DD-mmm-YYYY` (BBVA/HSBC), `DD/MM/YYYY`
- **Amounts**: Always `$X,XXX.XX` format with comma thousands separator
- **Credits/payments**: Indicated by `-` sign, `CR` suffix, or separate column
- **MSI**: "Meses sin intereses" installments, usually in a separate section
- **Foreign currency**: Continuation line with original amount, currency code, and exchange rate
- **IVA**: Tax on fees/interest, usually a separate line item

## Adding a New Export Format

### Step 1: Create the exporter

Create `src/bankparser/exporters/myformat.py`:

```python
"""MyFormat CSV exporter."""

from bankparser.exporters.base import BaseExporter
from bankparser.models import Transaction


class MyFormatExporter(BaseExporter):
    format_name = "myformat"
    description = "MyFormat import compatible"

    def get_headers(self) -> list[str]:
        return ["Date", "Description", "Amount", "Category"]

    def format_row(self, tx: Transaction) -> list[str]:
        return [
            tx.date.isoformat(),
            tx.description,
            f"{tx.amount:.2f}",
            tx.category,
        ]
```

### Step 2: Register it

In `src/bankparser/exporters/__init__.py`:

```python
from bankparser.exporters.myformat import MyFormatExporter

_EXPORTERS: dict[str, BaseExporter] = {
    "generic": GenericExporter(),
    "sure": SureExporter(),
    "monarch": MonarchExporter(),
    "myformat": MyFormatExporter(),  # add here
}
```

It will automatically appear in `bankparse parse --format` options.

## Running Tests

```bash
# All tests
pytest

# Verbose with coverage
pytest -v --cov=bankparser

# Single test file
pytest tests/test_parsers/test_bbva.py

# Single test
pytest tests/test_categorizer.py::TestDatabase::test_add_category

# Only BBVA parser tests
pytest tests/test_parsers/test_bbva.py -v
```

## Development

```bash
# Lint
ruff check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/

# Dependency audit
pip-audit
```

## Debugging a Statement

If a statement doesn't parse correctly:

```python
import pdfplumber

with pdfplumber.open("statement.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n{'='*60}")
        print(f"PAGE {i + 1}")
        print('='*60)
        print(page.extract_text())
```

If pdfplumber returns garbled text, try OCR:

```python
from bankparser.parsers.base import BaseParser

pages = BaseParser.extract_text_with_ocr(Path("statement.pdf"))
for i, text in enumerate(pages):
    print(f"\n=== PAGE {i + 1} ===")
    print(text)
```

Then adjust the regex patterns in the corresponding parser file.

## Roadmap

### Completed (v0.1.0)

- Amex, BBVA, HSBC Mexico TDC parsers
- Generic, Sure, Monarch export formats
- SQLite-backed categorization with ~80 pre-seeded rules
- CLI with parse, categories, rules, info commands
- OCR support for HSBC CID-encoded PDFs
- Robust error handling (graceful amount parsing, OCR dependency guard, DB integrity)

### Planned improvements

**Code quality (next)**
- Consolidate duplicated code across parsers (shared `MONTHS_ABBREV`, `_classify`, `_should_skip`, date parsers) into `BaseParser`
- Pre-compile Amex skip patterns (currently recompiled on every line)
- Replace module-level exporter dict with instance-based registry (matches parser pattern)

**Test coverage**
- CLI tests with Click's `CliRunner`
- `ParserRegistry` unit tests (auto-detection, error paths)
- End-to-end integration test (Parser → Categorizer → Exporter)
- Edge case coverage for `parse_mx_amount`, `Categorizer` fallthrough

**Database**
- Schema versioning for safe migrations
- Incremental seed data (new rules in updates reach existing users)
- In-memory rule cache (avoid re-querying SQLite per transaction)

**New banks**
- Banorte
- Santander Mexico
- Citibanamex
- Debit account statement formats (currently only TDC/credit card)

**New export formats**
- YNAB (You Need a Budget)
- Copilot Money
- Fintual

**Features**
- `bankparse detect statement.pdf` command (debug which bank was detected)
- `--dry-run` flag (preview without writing file)
- `--verbose` flag (detailed parsing output)
- Populate `Transaction.tags` from parser metadata (foreign, msi, etc.)

## License

MIT
