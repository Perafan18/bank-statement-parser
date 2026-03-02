# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## User Preferences

- **Siempre hablar en español** en todas las interacciones con el usuario. Código, commits y documentación técnica pueden ser en inglés.

## Project Overview

Python CLI tool that parses Mexican bank statement PDFs (Amex, BBVA, HSBC) into CSV files for personal finance apps (Sure/Maybe Finance, Monarch Money). Uses pdfplumber for PDF extraction and Click for the CLI.

## Commands

```bash
# Install in dev mode (use python3, not python — no python alias on this system)
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with coverage
pytest --cov=bankparser

# Run a single test file
pytest tests/test_models.py

# Run a specific test
pytest tests/test_categorizer.py::TestDatabase::test_add_category

# Lint and format
ruff check src/ tests/
ruff check --fix src/ tests/
ruff format src/ tests/

# Type check
mypy src/

# Dependency audit
pip-audit

# CLI usage (after install)
bankparse parse statement.pdf
```

## Architecture

**Data flow:** PDF → Parser (auto-detect bank) → ParseResult → Categorizer (SQLite rules) → Exporter → CSV

Key modules in `src/bankparser/`:

- **models.py** — Core dataclasses: `Transaction`, `StatementInfo`, `ParseResult`, `TransactionType` enum
- **parsers/** — Registry pattern. `BaseParser` (abstract) with `can_parse()`/`parse()` interface. Bank-specific implementations (amex.py, bbva.py, hsbc.py) use regex to extract transactions from pdfplumber text. `ParserRegistry` auto-detects bank by scanning first page.
- **exporters/** — Registry pattern. `BaseExporter` (abstract) with `get_headers()`/`format_row()` interface. Formats: generic (all fields), sure (Sure/Maybe Finance), monarch (Monarch Money).
- **database.py** — SQLite at `~/.bankparser/bankparser.db`. Stores categories and pattern-matching rules with priority. Seeds ~22 categories and ~80 rules on first init.
- **categorizer.py** — Assigns categories: forced type overrides (Payment, Interest, etc.) → SQLite rule matching (case-insensitive substring + bank-specific, priority-ordered) → "Uncategorized" fallback.
- **interactive.py** — Interactive CLI prompts for categorizing unknown transaction descriptions. Called by `cli.py` after parsing.
- **cli.py** — Click CLI entry point. Commands: `parse`, `categories`, `rules`, `info`.

## Adding a New Bank Parser

1. Create `src/bankparser/parsers/mybank.py` extending `BaseParser`
2. Implement `can_parse()` (first-page text detection) and `parse()` (regex extraction)
3. Register in `src/bankparser/parsers/__init__.py`
4. See README.md for detailed step-by-step guide with code templates

## Adding a New Export Format

1. Create `src/bankparser/exporters/myformat.py` extending `BaseExporter`
2. Implement `get_headers()` and `format_row()`
3. Register in `src/bankparser/exporters/__init__.py`

## Parsing Quirks (Tribal Knowledge)

- **pdfplumber whitespace**: pdfplumber frequently removes spaces in extracted text. Amex produces `deDiciembre`, `al8`, `de2026` instead of `de Diciembre`, `al 8`, `de 2026`. Always use `\s*` (not `\s+`) between prepositions and month/day names in regexes.
- **Split-date transactions (Amex)**: Most Amex transactions have the date split across two lines: `18 de GRACIAS POR SU PAGO 6,005.17` / `Diciembre CR`. The parser handles this via month-continuation detection in the `ValueError` handler.
- **Orphan transactions**: Page breaks can separate a transaction from its date. The parser tracks `last_date` and uses `ORPHAN_TX_RE` to catch these.
- **Year boundary (Dec→Jan statements)**: Transactions with dates after `period_end` belong to the previous year. The parser uses `tx_date > period_end` to adjust.
- **MONTHS_ES**: `base.py` has both full (`enero`) and abbreviated (`ene`) Spanish month names. Cut dates use abbreviated forms (`08-Ene-2026`).
- **HSBC OCR**: HSBC uses CID-encoded fonts that pdfplumber can't decode. The parser falls back to Tesseract OCR with Spanish language pack. Requires system packages: `tesseract-ocr`, `tesseract-ocr-spa`, `poppler-utils`.
- **Amex _consume_metadata**: After each transaction line, a lookahead consumes continuation lines (CR, RFC, CARGO installment, Dólar foreign currency). This is extracted into `_consume_metadata()` and reused by normal, split-date, and orphan transaction paths.

## Conventions

- Python 3.10+, `from __future__ import annotations` used throughout
- Type hints on all public APIs
- Dataclasses for models, enums for types
- Regex patterns as class-level UPPERCASE compiled constants
- Spanish date/number parsing helpers in `BaseParser` (Mexican bank formats)
- Tests use pytest fixtures (`tmp_db`, `sample_transactions` in conftest.py)
- Tests use inline text fixtures (mock `extract_text_from_pdf`), not real PDFs
- Ruff for linting/formatting, mypy for type checking (config in pyproject.toml)
- Line length: 100 chars (ruff). Tests exempt from E501.
