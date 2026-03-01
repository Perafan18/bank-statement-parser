# Critical Patch Design

Date: 2026-03-01
Scope: Bug fixes and robustness improvements (Enfoque A)

## Context

Audit of the codebase revealed 4 critical runtime issues and 3 trivial fixes that should be addressed before the project is made public.

## Changes

### 1. `parse_mx_amount` — graceful error with context

**File:** `src/bankparser/parsers/base.py`

Wrap `float()` in try/except ValueError. Re-raise with context message including the original string. Callers in each parser should catch this in their transaction-building loops and append a warning to ParseResult instead of aborting the entire parse.

### 2. HSBC OCR dependency guard

**File:** `src/bankparser/parsers/hsbc.py`

- In `parse()`: check that `pdf2image` and `pytesseract` are importable before calling `extract_text_with_ocr`. Raise `RuntimeError` with install instructions if not.
- In `can_parse()`: return `False` early if OCR deps are missing (instead of swallowing ImportError via bare `except Exception: pass`).

### 3. DB rollback after IntegrityError

**File:** `src/bankparser/database.py`

- In `add_category()`: wrap execute+commit in try/except `sqlite3.IntegrityError`, call `self.conn.rollback()`, then re-raise.
- Same pattern for `add_rule()`.

### 4. CLI robust error handling

**File:** `src/bankparser/cli.py`

- Catch `Exception` (not just `ValueError`) in the parse file loop, log the error, and continue to next file.
- Use `try/finally` to guarantee `db.close()`.
- Move `sys.exit(1)` after `db.close()`.

### 5. Fix `prog_name`

**File:** `src/bankparser/cli.py`

Change `prog_name="bankparser"` to `prog_name="bankparse"` in `@click.version_option`.

### 6. Remove dead code

**File:** `src/bankparser/models.py`

Remove `StatementInfo.cat` field (never set by any parser, never read by any exporter).

### 7. Fix README quick start

**File:** `README.md`

Change `bankparse statement.pdf` to `bankparse parse statement.pdf`.

## Out of Scope

- Code duplication consolidation (Enfoque B)
- Test coverage gaps (Enfoque C)
- Schema versioning, rule caching (Enfoque C)
