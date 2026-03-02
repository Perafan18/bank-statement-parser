"""Generate a realistic HSBC Mexico TDC statement PDF (image-based) for testing.

HSBC Mexico TDC statements are scanned/image-based PDFs (CID-encoded fonts),
so the parser uses OCR (pytesseract + pdf2image).  This generator creates a
PDF where each page is a rendered image, forcing the OCR code path.

The text is drawn with Pillow (PIL) onto white images at 150 DPI, then
embedded into a reportlab PDF.  The text must be clean enough for tesseract
to read back reliably.

Transaction format (matching HSBCParser.TX_RE):
  DD-Mmm-YYYY DD-Mmm-YYYY DESCRIPTION $AMOUNT

Foreign currency (matching HSBCParser.FOREIGN_RE):
  DD-Mmm-YYYY DD-Mmm-YYYY MONEDA EXTRANJERA: AMT CUR TC: RATE ... $MXN

Payments use SUPAGO GRACIAS with || indicator (credit/abono).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a standalone script from the generators directory
_GENERATORS_DIR = Path(__file__).resolve().parent
if str(_GENERATORS_DIR) not in sys.path:
    sys.path.insert(0, str(_GENERATORS_DIR))

from _shared import MONTHS_ES_ABBR_TITLE, MONTHS_ES_FULL, PDFS_DIR, format_amount  # noqa: E402

# ---------------------------------------------------------------------------
# Image / PDF constants
# ---------------------------------------------------------------------------

DPI = 150
PAGE_W_PX = int(8.5 * DPI)  # 1275
PAGE_H_PX = int(11 * DPI)  # 1650

# Text rendering
LEFT_MARGIN = 60  # pixels from left edge
TOP_MARGIN = 80  # pixels from top edge
LINE_HEIGHT = 28  # pixels between lines
FONT_SIZE = 18  # PIL default font is small; we scale via textsize approach
MAX_LINES_PER_PAGE = (PAGE_H_PX - TOP_MARGIN - 60) // LINE_HEIGHT

# ---------------------------------------------------------------------------
# Statement metadata
# ---------------------------------------------------------------------------

STATEMENT_INFO = {
    "account_display": "4524 1234 5678 9012",
    "account_number": "4524123456789012",
    "cardholder": "PEDRO MARTINEZ GONZALEZ",
    "period_start_day": 15,
    "period_start_month": 12,
    "period_start_year": 2025,
    "period_end_day": 12,
    "period_end_month": 1,
    "period_end_year": 2026,
    "cut_date_day": 12,
    "cut_date_month": 1,
    "cut_date_year": 2026,
    "previous_balance": 29_093.55,
}


def _hsbc_date(day: int, month: int, year: int) -> str:
    """Format an HSBC-style date: DD-Mmm-YYYY with title-case abbreviated month."""
    return f"{day:02d}-{MONTHS_ES_ABBR_TITLE[month]}-{year}"


def _full_month(month: int) -> str:
    """Return full Spanish month name (lowercase for OCR context)."""
    return MONTHS_ES_FULL[month].lower()


# ---------------------------------------------------------------------------
# Transaction data (~50 transactions)
# ---------------------------------------------------------------------------

# Each dict has:
#   op_day, op_month, op_year  - operation date
#   ch_day, ch_month, ch_year  - charge/posting date
#   description                - merchant/concept
#   amount                     - positive float
#   is_credit                  - True for payments/credits (shown with || indicator)
#
# Optional:
#   foreign_currency, foreign_amount, exchange_rate  - for MONEDA EXTRANJERA lines

TRANSACTIONS: list[dict] = [
    # ---- Regular charges (Dec 2025 and Jan 2026) --------------------------------
    {
        "op_day": 16,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 17,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "OXXO TONALA JALISCO",
        "amount": 48.50,
    },
    {
        "op_day": 16,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 17,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "UBER EATS MX GUADALAJARA",
        "amount": 189.00,
    },
    {
        "op_day": 17,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 18,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "AMAZON MX MARKETPLACE",
        "amount": 1_299.00,
    },
    {
        "op_day": 18,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 19,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "COSTCO WHOLESALE GUADALAJARA",
        "amount": 4_567.89,
    },
    {
        "op_day": 19,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 20,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "SORIANA SUPER ZAPOPAN",
        "amount": 892.30,
    },
    {
        "op_day": 20,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 21,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "LIVERPOOL CENTRO GDL",
        "amount": 3_450.00,
    },
    {
        "op_day": 21,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 22,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "REST KIMODO POLANCO MEX",
        "amount": 1_250.00,
    },
    {
        "op_day": 22,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 23,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "FARMACIA GUADALAJARA SUC 415",
        "amount": 345.60,
    },
    {
        "op_day": 23,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 24,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "CHEDRAUI SELECTO GUADALAJARA",
        "amount": 1_567.45,
    },
    {
        "op_day": 24,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 25,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "HOME DEPOT MEXICO PERIFERICO",
        "amount": 2_890.00,
    },
    {
        "op_day": 25,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 26,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "CINEPOLIS VIP ANDARES",
        "amount": 456.00,
    },
    {
        "op_day": 26,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 27,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "TOTALPLAY TELECOMUNICACIONES",
        "amount": 799.00,
    },
    {
        "op_day": 27,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 28,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "TELMEX RECIBO TELEFONICO",
        "amount": 589.00,
    },
    {
        "op_day": 28,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 29,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "CFE SUMINISTRADOR BASICO",
        "amount": 1_234.56,
    },
    {
        "op_day": 29,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 30,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "GAS NATURAL DEL NOROESTE",
        "amount": 678.90,
    },
    {
        "op_day": 30,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 31,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "SAMS CLUB GUADALAJARA PATRIA",
        "amount": 3_210.00,
    },
    {
        "op_day": 31,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 31,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "RESTAURANTE LA TEQUILA GDL",
        "amount": 1_890.50,
    },
    {
        "op_day": 2,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 3,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "GASOLINERA PEMEX 3456",
        "amount": 1_200.00,
    },
    {
        "op_day": 3,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 4,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "STARBUCKS ANDARES GDL",
        "amount": 185.00,
    },
    {
        "op_day": 4,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 5,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SUPERAMA GUADALAJARA",
        "amount": 2_345.67,
    },
    {
        "op_day": 5,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 6,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "PALACIO DE HIERRO ANDARES",
        "amount": 5_670.00,
    },
    {
        "op_day": 5,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 6,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "UBER RIDES MX CIUDAD DE MEXICO",
        "amount": 234.50,
    },
    {
        "op_day": 6,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 7,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "RAPPI MX GUADALAJARA",
        "amount": 312.00,
    },
    {
        "op_day": 6,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 7,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "MERCADO LIBRE COMPRA MX",
        "amount": 1_489.00,
    },
    {
        "op_day": 7,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 8,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "OFFICE DEPOT GUADALAJARA",
        "amount": 1_567.80,
    },
    {
        "op_day": 7,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 8,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "LA COMER SUCURSAL CENTRO",
        "amount": 2_345.00,
    },
    {
        "op_day": 8,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 9,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SANBORNS RESTAURANT GDL",
        "amount": 456.90,
    },
    {
        "op_day": 8,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 9,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "PETCO GUADALAJARA AMERICAS",
        "amount": 890.50,
    },
    {
        "op_day": 9,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 10,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "BODEGA AURRERA ZAPOPAN",
        "amount": 1_345.00,
    },
    {
        "op_day": 9,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 10,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "WALMART SUPERCENTER GDL",
        "amount": 2_678.30,
    },
    {
        "op_day": 10,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 11,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "ELEKTRA CENTRO GUADALAJARA",
        "amount": 3_456.00,
    },
    {
        "op_day": 10,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 11,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "CLINICA DENTAL ABC GDL",
        "amount": 1_400.00,
    },
    {
        "op_day": 11,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 12,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "ZARA MEXICO ANDARES GDL",
        "amount": 2_345.00,
    },
    {
        "op_day": 11,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 12,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "HEB GUADALAJARA PROVIDENCIA",
        "amount": 1_567.80,
    },
    {
        "op_day": 12,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 12,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "MERPAGO*TIENDA ONLINE MEX",
        "amount": 892.78,
    },
    # ---- Payments (SUPAGO GRACIAS — credit/abono indicator) --------------------
    {
        "op_day": 20,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 20,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "SUPAGO GRACIAS",
        "amount": 15_000.00,
        "is_credit": True,
    },
    {
        "op_day": 5,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 5,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SUPAGO GRACIAS",
        "amount": 10_000.00,
        "is_credit": True,
    },
    {
        "op_day": 10,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 10,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SUPAGO GRACIAS",
        "amount": 8_500.00,
        "is_credit": True,
    },
    # ---- Foreign currency (MONEDA EXTRANJERA) ----------------------------------
    {
        "op_day": 18,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 18,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "DIGITALOCEAN.COM AMSTERDAM NL",
        "amount": 630.30,
        "foreign_currency": "USD",
        "foreign_amount": 35.45,
        "exchange_rate": 17.78282,
    },
    {
        "op_day": 22,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 22,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "SPOTIFY AB STOCKHOLM SE",
        "amount": 199.98,
        "foreign_currency": "USD",
        "foreign_amount": 11.24,
        "exchange_rate": 17.79182,
    },
    {
        "op_day": 3,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 3,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "NETFLIX.COM LOS GATOS US",
        "amount": 321.45,
        "foreign_currency": "USD",
        "foreign_amount": 18.09,
        "exchange_rate": 17.77000,
    },
    # ---- Fee (COMISION/ANUALIDAD) ----------------------------------------------
    {
        "op_day": 12,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 12,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "ANUALIDAD TARJETA HSBC",
        "amount": 2_500.00,
    },
    # ---- Interest --------------------------------------------------------------
    {
        "op_day": 12,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 12,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "INTERESES DEL PERIODO",
        "amount": 1_234.56,
    },
    # ---- Tax (IVA) — classified as CHARGE by parser ----------------------------
    {
        "op_day": 12,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 12,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "IVA SOBRE INTERESES",
        "amount": 197.53,
    },
    # ---- Credits / Refunds (abono indicator) -----------------------------------
    {
        "op_day": 28,
        "op_month": 12,
        "op_year": 2025,
        "ch_day": 29,
        "ch_month": 12,
        "ch_year": 2025,
        "description": "BONIFICACION CASHBACK HSBC",
        "amount": 350.00,
        "is_credit": True,
    },
    {
        "op_day": 8,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 9,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "DEVOLUCION AMAZON MX",
        "amount": 756.90,
        "is_credit": True,
    },
]


# ---------------------------------------------------------------------------
# Text rendering helpers
# ---------------------------------------------------------------------------


def _format_tx_line(tx: dict) -> str:
    """Format a regular transaction line matching HSBCParser.TX_RE.

    Pattern: DD-Mmm-YYYY DD-Mmm-YYYY DESCRIPTION $AMOUNT
    For credits: DD-Mmm-YYYY DD-Mmm-YYYY DESCRIPTION || $AMOUNT
    """
    op_date = _hsbc_date(tx["op_day"], tx["op_month"], tx["op_year"])
    ch_date = _hsbc_date(tx["ch_day"], tx["ch_month"], tx["ch_year"])
    desc = tx["description"]
    amt = format_amount(tx["amount"])

    if tx.get("is_credit"):
        # Use || indicator between description and amount (credit/abono)
        return f"{op_date} {ch_date} {desc} || ${amt}"
    return f"{op_date} {ch_date} {desc} ${amt}"


def _format_foreign_description_line(tx: dict) -> str:
    """Format the description line that precedes a MONEDA EXTRANJERA line."""
    return tx["description"]


def _format_foreign_tx_line(tx: dict) -> str:
    """Format a MONEDA EXTRANJERA line matching HSBCParser.FOREIGN_RE.

    Pattern: DD-Mmm-YYYY DD-Mmm-YYYY MONEDA EXTRANJERA: AMT CUR TC: RATE DEL DD DE MES + $MXN
    """
    op_date = _hsbc_date(tx["op_day"], tx["op_month"], tx["op_year"])
    ch_date = _hsbc_date(tx["ch_day"], tx["ch_month"], tx["ch_year"])
    foreign_amt = f"{tx['foreign_amount']:.2f}"
    currency = tx["foreign_currency"]
    rate = f"{tx['exchange_rate']:.5f}"
    mxn_amt = format_amount(tx["amount"])
    month_name = _full_month(tx["op_month"])
    day = tx["op_day"]

    return (
        f"{op_date} {ch_date} MONEDA EXTRANJERA: {foreign_amt} {currency} "
        f"TC: {rate} DEL {day} DE {month_name.upper()} + ${mxn_amt}"
    )


# ---------------------------------------------------------------------------
# Page content builder
# ---------------------------------------------------------------------------


def _build_page_lines() -> list[list[str]]:
    """Build all text lines organized into pages.

    Returns a list of pages, where each page is a list of text lines.
    """
    info = STATEMENT_INFO
    all_lines: list[str] = []

    # ── Page 1: Header / summary info ─────────────────────────────────────
    all_lines.append("HSBC")
    all_lines.append("HSBC Mexico S.A. Institucion de Banca Multiple")
    all_lines.append("Estado de Cuenta de Tarjeta de Credito")
    all_lines.append("")
    all_lines.append("TU PAGO REQUERIDO ESTE PERIODO")
    all_lines.append(info["cardholder"])
    all_lines.append("")
    all_lines.append(
        f"Periodo: {_hsbc_date(info['period_start_day'], info['period_start_month'], info['period_start_year'])}"
        f" al {_hsbc_date(info['period_end_day'], info['period_end_month'], info['period_end_year'])}"
    )
    all_lines.append("")
    all_lines.append(
        f"Fecha de corte: {_hsbc_date(info['cut_date_day'], info['cut_date_month'], info['cut_date_year'])}"
    )
    all_lines.append("")
    all_lines.append(f"NUMERO DE CUENTA: {info['account_display']}")
    all_lines.append("")
    all_lines.append(f"Adeudo del periodo anterior |= ${format_amount(info['previous_balance'])}")
    all_lines.append("")
    all_lines.append("HSBC Zero Categoria: Clasica")
    all_lines.append("")

    # ── Transaction section ───────────────────────────────────────────────
    all_lines.append("DESGLOSE DE MOVIMIENTOS")
    all_lines.append("")
    all_lines.append("c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)")
    all_lines.append(f"Tarjeta titular {info['account_number']}")
    all_lines.append("")

    # Column header (skipped by parser)
    all_lines.append("i. Fecha de la")
    all_lines.append("operacion")
    all_lines.append("")

    # Separate foreign from regular transactions
    regular_txs = [tx for tx in TRANSACTIONS if "foreign_currency" not in tx]
    foreign_txs = [tx for tx in TRANSACTIONS if "foreign_currency" in tx]

    # Write regular transactions
    for tx in regular_txs:
        all_lines.append(_format_tx_line(tx))

    # Write foreign currency transactions (description line + MONEDA EXTRANJERA line)
    for tx in foreign_txs:
        all_lines.append("")
        all_lines.append(_format_foreign_description_line(tx))
        all_lines.append(_format_foreign_tx_line(tx))

    # Totals
    all_lines.append("")
    all_lines.append("Total cargos $68,000.00")
    all_lines.append("Total abonos $34,606.90")

    # Split into pages
    pages: list[list[str]] = []
    idx = 0
    while idx < len(all_lines):
        page_lines = all_lines[idx : idx + MAX_LINES_PER_PAGE]
        pages.append(page_lines)
        idx += MAX_LINES_PER_PAGE

    return pages


# ---------------------------------------------------------------------------
# Image-based PDF generation
# ---------------------------------------------------------------------------


def _render_page_image(lines: list[str], tmp_dir: Path) -> Path:
    """Render a list of text lines onto a white image and save as PNG.

    Uses a large built-in font for clean OCR readability.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), color="white")
    draw = ImageDraw.Draw(img)

    # Try to load a clean monospace/sans font for best OCR results
    font = None
    # Try common system fonts that produce clean OCR output
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            font = ImageFont.truetype(fp, FONT_SIZE)
            break

    if font is None:
        # Fall back to default (very small but still OCR-readable at 150 DPI)
        font = ImageFont.load_default()

    y = TOP_MARGIN
    for line in lines:
        draw.text((LEFT_MARGIN, y), line, fill="black", font=font)
        y += LINE_HEIGHT

    # Save to a temporary PNG
    png_path = tmp_dir / f"page_{id(lines)}.png"
    img.save(str(png_path), "PNG")
    return png_path


def main() -> None:
    """Generate the HSBC image-based PDF fixture."""
    import tempfile as _tempfile

    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas as canvas_mod

    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    output = PDFS_DIR / "hsbc_jan_2026.pdf"

    pages = _build_page_lines()

    page_w = 8.5 * inch
    page_h = 11 * inch

    c = canvas_mod.Canvas(str(output), pagesize=(page_w, page_h))

    with _tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        for i, page_lines in enumerate(pages):
            if i > 0:
                c.showPage()

            # Render text onto an image
            png_path = _render_page_image(page_lines, tmp_path)

            # Embed the image into the PDF page (full page)
            c.drawImage(
                str(png_path),
                0,
                0,
                width=page_w,
                height=page_h,
                preserveAspectRatio=True,
            )

    c.save()
    print(f"Generated: {output}")
    print(f"  Pages: {len(pages)}")
    print(f"  Transactions: {len(TRANSACTIONS)}")


if __name__ == "__main__":
    main()
