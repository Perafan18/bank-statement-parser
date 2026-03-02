# Bank Statement Parser

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

---

See [Usage](usage.md) for full CLI reference, [Architecture](architecture.md) for project internals.
