# Usage

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
