# Fake PDF Fixtures for Integration Testing

**Date:** 2026-03-01
**Status:** Approved

## Goal

Create programmatically-generated PDFs (one per bank) that closely mimic real bank statement layouts, committed to the repo as test fixtures. These enable true end-to-end integration tests: PDF file → parser → ParseResult — with no mocks.

## Approach

**reportlab** scripts generate PDFs with visually realistic layouts. Each bank has a dedicated generator script. For HSBC, the PDF is rendered as a scanned image (Pillow) to force the OCR path.

## File Structure

```
tests/
├── fixtures/
│   ├── generators/
│   │   ├── __init__.py       # CLI: python -m tests.fixtures.generators
│   │   ├── _shared.py        # Shared helpers: draw_header, draw_table, fake data
│   │   ├── generate_amex.py  # Generates amex_dec_jan_2026.pdf
│   │   ├── generate_bbva.py  # Generates bbva_jan_2026.pdf
│   │   └── generate_hsbc.py  # Generates hsbc_dec_jan_2026.pdf
│   └── pdfs/
│       ├── amex_dec_jan_2026.pdf
│       ├── bbva_jan_2026.pdf
│       └── hsbc_dec_jan_2026.pdf
├── test_parsers/
│   ├── test_amex_pdf.py      # Integration tests using Amex fixture
│   ├── test_bbva_pdf.py      # Integration tests using BBVA fixture
│   └── test_hsbc_pdf.py      # Integration tests using HSBC fixture
```

## Transaction Data (~60 per bank)

Each generator defines fake transaction data covering all types:

| Type | ~Count | Examples |
|------|--------|---------|
| Regular charges | 35-40 | OXXO, UBER, AMAZON, LIVERPOOL, COSTCO |
| Payments | 2-3 | GRACIAS POR SU PAGO, PAGO DOMICILIADO |
| Credits/refunds | 2-3 | DEVOLUCION TIENDA, BONIFICACION |
| MSI installments | 3-4 | MESES EN AUTOMATICO, CARGO 03 DE 12 |
| Foreign currency (USD) | 3-4 | DIGITALOCEAN, SPOTIFY |
| Fees | 1-2 | CUOTA ANUAL, COMISION |
| Interest | 1-2 | INTERES FINANCIERO |
| Tax (IVA) | 1-2 | IVA APLICABLE |
| Additional cardholder | 5-8 | Amex only |

Period: December 2025 → January 2026 (crosses year boundary). Realistic but fictional merchant names. Varied amounts.

## Bank-Specific Layouts

### Amex

Generated with `reportlab.canvas.Canvas` using `drawString()` for precise text positioning.

**Page 1 (summary):**
- "Estado de Cuenta" + "American Express" header
- Account: `3717-XXXXXX-XXXXX`, cut date: `08-Ene-2026`
- Period: `Del 9 deDiciembre al8 deEnero de2026` (deliberately broken whitespace to mimic pdfplumber extraction)
- Cardholder: `PEDRO MARTINEZ GONZALEZ`
- Balance summary

**Pages 2-4 (transactions):**
- Section header: "Fecha y Detalle / Importe en MN"
- Transaction lines: `DD de[Mes] DESCRIPCION MONTO` (includes split-date lines where month is on next line)
- Metadata lines: RFC references, CARGO installments, Dólar foreign currency, CR indicators
- Total lines: `Total de las transacciones en $ de PEDRO MARTINEZ...` (triggers cardholder switch)
- Additional cardholder section
- 2-3 orphan transactions (no date prefix, simulating page break splits)

**Key pdfplumber quirk to reproduce:** Text is positioned so that `page.extract_text()` returns lines with broken whitespace: `deDiciembre`, `al8`, `de2026`. This is achieved by placing text fragments close together without explicit spaces.

### BBVA

**Page 1 (summary):**
- "Estado de Cuenta" + "BBVA" header area
- Card number: `XXXX XXXX XXXX XXXX`
- Period, cardholder, balances

**Pages 2-3 (regular transactions):**
- Section: "CARGOS,COMPRAS Y ABONOS REGULARES(NO A MESES)"
- Format: `DD-mmm-YYYY DD-mmm-YYYY DESCRIPCION +/- $MONTO`
- Foreign currency continuation lines: `USD $100.45 TIPO DE CAMBIO $17.99`

**Page 4 (MSI):**
- Section: "COMPRAS A MESES SIN INTERESES"
- Format: `DD-mmm-YYYY DESCRIPCION $ORIG $PENDING $MONTHLY X de Y RATE%`
- Section: "COMPRAS A MESES CON INTERESES" (adds interest fields)

### HSBC (scanned image)

The PDF is generated as embedded PNG images (one per page) using Pillow to render text. This makes pdfplumber unable to extract text (no text layer), forcing the OCR path through pytesseract.

**Image generation with Pillow:**
- White background, black text, monospace font
- Simulated table with column alignment
- Controlled OCR artifacts: pipe characters (`|`), underscores (`_`), brackets at predictable positions

**Layout:**
- Header: "HSBC" + statement metadata
- Table columns: Fecha Op | Fecha Cargo | Descripcion | Importe
- Credit indicators: `|-]` marker, SUPAGO keyword
- Foreign currency section: `MONEDA EXTRANJERA: X.XX USD TC: XX.XXXXX`

## Tests

New integration test files per bank. Tests call the real parser on the fixture PDF without any mocks.

```python
FIXTURE = Path(__file__).parent.parent / "fixtures" / "pdfs" / "amex_dec_jan_2026.pdf"

@pytest.fixture
def result():
    parser = AmexParser()
    return parser.parse(FIXTURE)

class TestAmexPdfIntegration:
    def test_transaction_count(self, result):
        assert result.transaction_count == 60

    def test_december_dates_are_2025(self, result):
        # Year boundary validation
        ...

    def test_total_charges_and_credits(self, result):
        # Cross-check totals against known expected values
        ...
```

HSBC tests require OCR dependencies. Mark with `pytest.importorskip("pytesseract")`.

Existing inline text tests are preserved as-is for unit testing.

## Dependencies

- **reportlab** → added to `[dev]` extras (PDFs are committed; regeneration is optional)
- **Pillow** → added to `[dev]` extras (HSBC image-based PDF generation)
- **tesseract-ocr + tesseract-ocr-spa + poppler-utils** → system packages for HSBC OCR tests in CI

## Regeneration

Each generator is a standalone script:

```bash
python -m tests.fixtures.generators.generate_amex
python -m tests.fixtures.generators.generate_bbva
python -m tests.fixtures.generators.generate_hsbc
# Or all at once:
python -m tests.fixtures.generators
```

Generators are idempotent — same data produces same PDF. To change fixture data, modify the script, regenerate, and commit the new PDF.
