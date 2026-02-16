# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python CLI tool that parses Mexican bank statement PDFs (Amex, BBVA, HSBC) into CSV files for personal finance apps (Sure/Maybe Finance, Monarch Money). Uses pdfplumber for PDF extraction and Click for the CLI.

## Commands

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with coverage
pytest --cov=bankparser

# Run a single test file
pytest tests/test_models.py

# Run a specific test
pytest tests/test_categorizer.py::TestDatabase::test_add_category

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
- **cli.py** — Click CLI entry point. Commands: `parse`, `categories`, `rules`, `info`.

## Adding a New Bank Parser

1. Create `src/bankparser/parsers/mybank.py` extending `BaseParser`
2. Implement `can_parse()` (first-page text detection) and `parse()` (regex extraction)
3. Register in `src/bankparser/parsers/__init__.py`

## Adding a New Export Format

1. Create `src/bankparser/exporters/myformat.py` extending `BaseExporter`
2. Implement `get_headers()` and `format_row()`
3. Register in `src/bankparser/exporters/__init__.py`

## Conventions

- Python 3.10+, `from __future__ import annotations` used throughout
- Type hints on all public APIs
- Dataclasses for models, enums for types
- Regex patterns as module-level UPPERCASE constants
- Spanish date/number parsing helpers in `BaseParser` (Mexican bank formats)
- Tests use pytest fixtures (`tmp_db`, `sample_transactions` in conftest.py)
- No linter or formatter configured
