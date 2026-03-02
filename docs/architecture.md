# Architecture

```
PDF ──→ Parser (auto-detect) ──→ ParseResult ──→ Categorizer ──→ Exporter ──→ CSV
         │                         │                │
         │ can_parse()             │ StatementInfo   │ SQLite rules
         │ parse()                 │ Transaction[]   │ (priority-ordered)
         │                         │ warnings[]      │
         ▼                         ▼                 ▼
    ParserRegistry            models.py          database.py
```

## Core models (`models.py`)

| Model | Purpose |
|-------|---------|
| `Transaction` | A single transaction. Every parser produces these, every exporter consumes them. Fields: date, description, amount, currency, bank, cardholder, tx_type, category, installment, reference, original_amount, original_currency, exchange_rate, tags |
| `TransactionType` | Enum: `CHARGE`, `PAYMENT`, `CREDIT`, `FEE`, `INTEREST`, `TAX`, `MSI`, `MSI_ADJUSTMENT`, `TRANSFER` |
| `StatementInfo` | Statement metadata: bank, account_number, cardholder, period dates, balances |
| `ParseResult` | Container: `info` (StatementInfo) + `transactions` (list) + `warnings` (list) |

## Parsers (`parsers/`)

Registry pattern with auto-detection. Each parser extends `BaseParser`:

| Parser | Bank | Text extraction | Notes |
|--------|------|-----------------|-------|
| `AmexParser` | American Express Mexico | pdfplumber | Multi-cardholder, MSI, foreign currency (USD), RFC references |
| `BBVAParser` | BBVA Mexico (Bancomer) TDC | pdfplumber | Two-section parsing (regular + MSI sin/con intereses), `+/-` sign convention |
| `HSBCParser` | HSBC Mexico TDC | OCR (pytesseract) | CID-encoded fonts require OCR, extensive artifact cleanup |

## Exporters (`exporters/`)

Registry pattern. Each exporter extends `BaseExporter`:

| Exporter | Format | Target app |
|----------|--------|------------|
| `GenericExporter` | All 14 fields | Raw analysis |
| `SureExporter` | 8 fields with tags/notes | Sure / Maybe Finance |
| `MonarchExporter` | 8 fields with account label | Monarch Money |

## Database (`database.py`)

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
