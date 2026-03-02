# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-03-01

### Added

- **Parsers:** Amex Mexico, BBVA Mexico TDC, HSBC Mexico TDC (OCR-based)
- **Export formats:** Generic (all fields), Sure/Maybe Finance, Monarch Money
- **Categorization:** SQLite-backed with 22 categories and 80+ pre-seeded rules
- **CLI:** `bankparse parse`, `categories`, `rules`, `info` commands
- **OCR support:** HSBC CID-encoded PDFs via pytesseract + pdf2image
- **Multi-cardholder:** Amex statements distinguish titular vs additional
- **Foreign currency:** Original amount, currency code, and exchange rate preserved
- **MSI tracking:** Installment info for both "sin intereses" and "con intereses"
- **Filtering:** By cardholder, transaction type, fees, MSI, charges-only
