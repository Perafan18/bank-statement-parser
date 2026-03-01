# 🏦 Bank Statement Parser

Parse Mexican bank statement PDFs (American Express, BBVA, HSBC) into CSV files
compatible with personal finance apps like [Sure](https://github.com/we-promise/sure),
Monarch Money, and others.

## Features

- **Multi-bank support**: Amex, BBVA, HSBC Mexico — with auto-detection
- **Smart categorization**: SQLite-backed rules you can customize
- **Multiple export formats**: Generic, Sure/Maybe Finance, Monarch Money
- **MSI tracking**: Installment info preserved (cargo X de Y)
- **Foreign currency**: Original amount + exchange rate preserved
- **Multi-cardholder**: Distinguishes titular vs additional cardholders
- **Filtering**: By cardholder, transaction type, fees, etc.

## Installation

```bash
# Clone and install in development mode
git clone <your-repo-url>
cd bank-statement-parser
pip install -e ".[dev]"
```

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

# Filter by cardholder
bankparse parse statement.pdf --cardholder haydee
```

## Category Management

Categories live in a SQLite database at `~/.bankparser/bankparser.db`.
Comes pre-seeded with ~20 categories and ~80 rules.

```bash
# List all categories
bankparse categories list

# Add a new category
bankparse categories add "Pets" --icon "🐕"

# List rules
bankparse rules list

# Add a custom rule
bankparse rules add "COSTCO" "Groceries"
bankparse rules add "VET" "Pets" --bank amex --priority 20

# Remove a rule
bankparse rules remove 42
```

## Export Formats

| Format    | Description                        | Columns                                          |
|-----------|------------------------------------|--------------------------------------------------|
| `generic` | All fields, maximum detail         | date, description, amount, currency, bank, ...   |
| `sure`    | Sure / Maybe Finance               | date, name, amount, currency, category, tags, ... |
| `monarch` | Monarch Money                      | Date, Merchant, Amount, Category, Account, ...   |

## Adding a New Bank

1. Create `src/bankparser/parsers/mybank.py`
2. Extend `BaseParser`
3. Implement `can_parse()` and `parse()`
4. Register in `src/bankparser/parsers/__init__.py`

```python
from bankparser.parsers.base import BaseParser
from bankparser.models import ParseResult

class MyBankParser(BaseParser):
    bank_name = "mybank"

    def can_parse(self, pdf_path):
        text = self.extract_first_page_text(pdf_path)
        return "my bank" in text.lower()

    def parse(self, pdf_path):
        # Your parsing logic here
        ...
```

## Running Tests

```bash
pytest
pytest -v --cov=bankparser
```

## Project Structure

```
bank-statement-parser/
├── src/bankparser/
│   ├── cli.py              # Click CLI entry point
│   ├── models.py           # Transaction, StatementInfo, ParseResult
│   ├── database.py         # SQLite categories + rules
│   ├── categorizer.py      # Rule-based categorization
│   ├── parsers/
│   │   ├── base.py         # BaseParser (abstract)
│   │   ├── amex.py         # American Express Mexico
│   │   ├── bbva.py         # BBVA Mexico
│   │   └── hsbc.py         # HSBC Mexico
│   └── exporters/
│       ├── base.py         # BaseExporter (abstract)
│       ├── generic.py      # Full-detail CSV
│       ├── sure.py         # Sure / Maybe Finance
│       └── monarch.py      # Monarch Money
├── tests/
├── pyproject.toml
└── README.md
```

## BBVA & HSBC Notes

The BBVA and HSBC parsers are built based on common statement formats
from these banks in Mexico. Since PDF layouts can vary between products
(credit card vs debit, digital vs printed), you may need to adjust the
regex patterns if your statement doesn't parse correctly.

To debug, run:

```python
import pdfplumber
with pdfplumber.open("your_statement.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"=== PAGE {i+1} ===")
        print(page.extract_text())
```

Then adjust the patterns in the corresponding parser file.
