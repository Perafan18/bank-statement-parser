"""Generate a realistic American Express Mexico statement PDF for testing.

The generated PDF is designed to be parseable by AmexParser with zero mocks.
It covers: regular charges, payments, credits, MSI, foreign USD, fees, tax,
interest, MSI adjustments, split-date transactions, and orphan transactions.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a standalone script from the generators directory
_GENERATORS_DIR = Path(__file__).resolve().parent
if str(_GENERATORS_DIR) not in sys.path:
    sys.path.insert(0, str(_GENERATORS_DIR))

from _shared import MONTHS_ES_FULL, PDFS_DIR, format_amount  # noqa: E402

# ---------------------------------------------------------------------------
# Statement metadata
# ---------------------------------------------------------------------------

STATEMENT_INFO = {
    "account": "3717-123456-12345",
    "cardholder": "PEDRO MARTINEZ GONZALEZ",
    "additional_cardholder": "MARIA LOPEZ HERNANDEZ",
    "period_start_day": 9,
    "period_start_month": 12,
    "period_start_year": 2025,
    "period_end_day": 8,
    "period_end_month": 1,
    "period_end_year": 2026,
    "cut_date_day": 8,
    "cut_date_month": 1,
    "cut_date_year": 2026,
}

# ---------------------------------------------------------------------------
# Transaction data (~60 transactions)
# ---------------------------------------------------------------------------

TRANSACTIONS: list[dict] = [
    # ---- Regular charges (Pedro, December 2025) ----------------------------
    {"day": 10, "month": 12, "year": 2025, "description": "OXXO TONALA JALISCO", "amount": 48.50},
    {"day": 10, "month": 12, "year": 2025, "description": "UBER EATS MX", "amount": 189.00},
    {
        "day": 11,
        "month": 12,
        "year": 2025,
        "description": "AMAZON MX MARKETPLACE",
        "amount": 1_299.00,
    },
    {"day": 12, "month": 12, "year": 2025, "description": "LIVERPOOL CENTRO", "amount": 3_450.00},
    {
        "day": 13,
        "month": 12,
        "year": 2025,
        "description": "COSTCO WHOLESALE GUADALAJARA",
        "amount": 4_567.89,
    },
    {
        "day": 14,
        "month": 12,
        "year": 2025,
        "description": "REST KIMODO POLANCO",
        "amount": 1_250.00,
    },
    {
        "day": 15,
        "month": 12,
        "year": 2025,
        "description": "FARMACIA GUADALAJARA SUC 415",
        "amount": 345.60,
    },
    {
        "day": 16,
        "month": 12,
        "year": 2025,
        "description": "SORIANA SUPER ZAPOPAN",
        "amount": 892.30,
    },
    {
        "day": 17,
        "month": 12,
        "year": 2025,
        "description": "CHEDRAUI SELECTO GUADALAJARA",
        "amount": 1_567.45,
    },
    {
        "day": 18,
        "month": 12,
        "year": 2025,
        "description": "HOME DEPOT MEXICO PERIFERICO",
        "amount": 2_890.00,
    },
    {
        "day": 19,
        "month": 12,
        "year": 2025,
        "description": "CINEPOLIS VIP ANDARES",
        "amount": 456.00,
    },
    {
        "day": 20,
        "month": 12,
        "year": 2025,
        "description": "TOTALPLAY TELECOMUNICACIONES",
        "amount": 799.00,
    },
    {
        "day": 21,
        "month": 12,
        "year": 2025,
        "description": "TELMEX RECIBO TELEFONICO",
        "amount": 589.00,
    },
    {
        "day": 22,
        "month": 12,
        "year": 2025,
        "description": "CFE SUMINISTRADOR DE SERVICIOS",
        "amount": 1_234.56,
    },
    {
        "day": 23,
        "month": 12,
        "year": 2025,
        "description": "GAS NATURAL DEL NOROESTE",
        "amount": 678.90,
    },
    {
        "day": 24,
        "month": 12,
        "year": 2025,
        "description": "SAMS CLUB GUADALAJARA PATRIA",
        "amount": 3_210.00,
    },
    {
        "day": 26,
        "month": 12,
        "year": 2025,
        "description": "RESTAURANTE LA TEQUILA GDL",
        "amount": 1_890.50,
    },
    {
        "day": 27,
        "month": 12,
        "year": 2025,
        "description": "GASOLINERA PEMEX 3456",
        "amount": 1_200.00,
    },
    {
        "day": 28,
        "month": 12,
        "year": 2025,
        "description": "STARBUCKS ANDARES GDL",
        "amount": 185.00,
    },
    {
        "day": 29,
        "month": 12,
        "year": 2025,
        "description": "SUPERAMA GUADALAJARA PROVIDENCIA",
        "amount": 2_345.67,
    },
    {
        "day": 30,
        "month": 12,
        "year": 2025,
        "description": "PALACIO DE HIERRO ANDARES",
        "amount": 5_670.00,
    },
    # ---- Regular charges (Pedro, January 2026) ----------------------------
    {
        "day": 2,
        "month": 1,
        "year": 2026,
        "description": "UBER RIDES MX CIUDAD DE MEXICO",
        "amount": 234.50,
    },
    {"day": 3, "month": 1, "year": 2026, "description": "RAPPI MX GUADALAJARA", "amount": 312.00},
    {"day": 4, "month": 1, "year": 2026, "description": "AMAZON MX MARKETPLACE", "amount": 756.90},
    {"day": 5, "month": 1, "year": 2026, "description": "MERCADO LIBRE COMPRA", "amount": 1_489.00},
    {"day": 5, "month": 1, "year": 2026, "description": "OXXO GAS ZAPOPAN JAL", "amount": 65.00},
    {
        "day": 6,
        "month": 1,
        "year": 2026,
        "description": "OFFICE DEPOT GUADALAJARA",
        "amount": 1_567.80,
    },
    {
        "day": 7,
        "month": 1,
        "year": 2026,
        "description": "LA COMER SUCURSAL CENTRO",
        "amount": 2_345.00,
    },
    {
        "day": 7,
        "month": 1,
        "year": 2026,
        "description": "SANBORNS RESTAURANT GDL",
        "amount": 456.90,
    },
    {
        "day": 8,
        "month": 1,
        "year": 2026,
        "description": "PETCO GUADALAJARA AMERICAS",
        "amount": 890.50,
    },
    {
        "day": 25,
        "month": 12,
        "year": 2025,
        "description": "BODEGA AURRERA ZAPOPAN",
        "amount": 1_345.00,
    },
    {
        "day": 31,
        "month": 12,
        "year": 2025,
        "description": "WALMART SUPERCENTER GUADALAJARA",
        "amount": 2_678.30,
    },
    {
        "day": 6,
        "month": 1,
        "year": 2026,
        "description": "ELEKTRA CENTRO GUADALAJARA",
        "amount": 3_456.00,
    },
    # ---- Payments (is_credit=True, split-date) ----------------------------
    {
        "day": 18,
        "month": 12,
        "year": 2025,
        "description": "GRACIAS POR SU PAGO EN LINEA",
        "amount": 6_005.17,
        "is_credit": True,
        "split_date": True,
    },
    {
        "day": 2,
        "month": 1,
        "year": 2026,
        "description": "GRACIAS POR SU PAGO EN LINEA",
        "amount": 15_000.00,
        "is_credit": True,
        "split_date": True,
    },
    # ---- Credits / Refunds (is_credit=True) --------------------------------
    {
        "day": 20,
        "month": 12,
        "year": 2025,
        "description": "DEVOLUCION LIVERPOOL",
        "amount": 1_200.00,
        "is_credit": True,
    },
    {
        "day": 5,
        "month": 1,
        "year": 2026,
        "description": "DEVOLUCION AMAZON MX",
        "amount": 350.00,
        "is_credit": True,
    },
    {
        "day": 28,
        "month": 12,
        "year": 2025,
        "description": "BONIFICACION AMEX CASHBACK",
        "amount": 250.00,
        "is_credit": True,
        "split_date": True,
    },
    {
        "day": 6,
        "month": 1,
        "year": 2026,
        "description": "GRACIAS POR SU PAGO SUCURSAL",
        "amount": 8_500.00,
        "is_credit": True,
        "split_date": True,
    },
    # ---- MSI (installments) -----------------------------------------------
    {
        "day": 12,
        "month": 12,
        "year": 2025,
        "description": "LIVERPOOL CENTRO MSI",
        "amount": 1_500.00,
        "installment": "03 DE 12",
    },
    {
        "day": 15,
        "month": 12,
        "year": 2025,
        "description": "HOME DEPOT MEXICO MSI",
        "amount": 2_500.00,
        "installment": "01 DE 06",
    },
    {
        "day": 3,
        "month": 1,
        "year": 2026,
        "description": "PALACIO DE HIERRO ANDARES MSI",
        "amount": 4_200.00,
        "installment": "06 DE 18",
    },
    # ---- Foreign USD -------------------------------------------------------
    {
        "day": 11,
        "month": 12,
        "year": 2025,
        "description": "DIGITALOCEAN.COM AMSTERDAM",
        "amount": 630.30,
        "foreign_usd": 35.45,
        "exchange_rate": 17.76559,
    },
    {
        "day": 14,
        "month": 12,
        "year": 2025,
        "description": "SPOTIFY AB STOCKHOLM",
        "amount": 199.90,
        "foreign_usd": 11.24,
        "exchange_rate": 17.78000,
    },
    {
        "day": 22,
        "month": 12,
        "year": 2025,
        "description": "NETFLIX.COM LOS GATOS",
        "amount": 321.45,
        "foreign_usd": 18.09,
        "exchange_rate": 17.77000,
    },
    # ---- Fee (CUOTA ANUAL) -------------------------------------------------
    {
        "day": 8,
        "month": 1,
        "year": 2026,
        "description": "CUOTA ANUAL TARJETA PLATINO",
        "amount": 3_500.00,
    },
    # ---- Tax (IVA) ---------------------------------------------------------
    {
        "day": 8,
        "month": 1,
        "year": 2026,
        "description": "IVA APLICABLE A COMISIONES",
        "amount": 560.00,
    },
    # ---- Interest ----------------------------------------------------------
    {
        "day": 8,
        "month": 1,
        "year": 2026,
        "description": "INTERES FINANCIERO ORDINARIO",
        "amount": 1_234.56,
    },
    {
        "day": 8,
        "month": 1,
        "year": 2026,
        "description": "INTERES FINANCIERO MORATORIO",
        "amount": 456.78,
    },
    # ---- MSI Adjustment (MONTO A DIFERIR) ----------------------------------
    {
        "day": 8,
        "month": 1,
        "year": 2026,
        "description": "MONTO A DIFERIR COMPRA MSI",
        "amount": 7_200.00,
        "is_credit": True,
    },
    # ---- MSI Auto (MESES EN AUTOMATICO) ------------------------------------
    {
        "day": 6,
        "month": 1,
        "year": 2026,
        "description": "MESES EN AUTOM\u00c1TICO TIENDA LIVERPOOL",
        "amount": 2_800.00,
    },
    # ---- Additional cardholder (Maria) ------------------------------------
    {
        "day": 11,
        "month": 12,
        "year": 2025,
        "description": "ZARA MEXICO ANDARES GDL",
        "amount": 2_345.00,
        "cardholder": "additional",
    },
    {
        "day": 13,
        "month": 12,
        "year": 2025,
        "description": "SEPHORA ANDARES GUADALAJARA",
        "amount": 1_890.00,
        "cardholder": "additional",
    },
    {
        "day": 16,
        "month": 12,
        "year": 2025,
        "description": "HEB GUADALAJARA PROVIDENCIA",
        "amount": 1_567.80,
        "cardholder": "additional",
    },
    {
        "day": 20,
        "month": 12,
        "year": 2025,
        "description": "SUBURBIA CENTRO GUADALAJARA",
        "amount": 890.50,
        "cardholder": "additional",
    },
    {
        "day": 25,
        "month": 12,
        "year": 2025,
        "description": "COPPEL ZAPOPAN JALISCO",
        "amount": 1_234.00,
        "cardholder": "additional",
    },
    {
        "day": 3,
        "month": 1,
        "year": 2026,
        "description": "FARMACIA SAN PABLO MEXICO",
        "amount": 456.90,
        "cardholder": "additional",
    },
    {
        "day": 5,
        "month": 1,
        "year": 2026,
        "description": "MINISO GUADALAJARA CENTRO",
        "amount": 234.50,
        "cardholder": "additional",
    },
    {
        "day": 7,
        "month": 1,
        "year": 2026,
        "description": "FOREVER 21 ANDARES GDL",
        "amount": 678.00,
        "cardholder": "additional",
    },
    # ---- Orphan transactions (no date prefix) -----------------------------
    {
        "day": 24,
        "month": 12,
        "year": 2025,
        "description": "PAYPAL *UBRPAGOSMEX 4029357733",
        "amount": 56.95,
        "orphan": True,
    },
    {
        "day": 6,
        "month": 1,
        "year": 2026,
        "description": "RAPPI *TIENDAS 8837261",
        "amount": 189.50,
        "orphan": True,
    },
]


# ---------------------------------------------------------------------------
# PDF generation helpers
# ---------------------------------------------------------------------------

LEFT = 50
HEADER_FONT_SIZE = 14
BODY_FONT_SIZE = 10
LINE_HEIGHT = 14


def _month_name(month: int) -> str:
    """Return full Spanish month name (title case)."""
    return MONTHS_ES_FULL[month]


def _month_abbr_title(month: int) -> str:
    """Return abbreviated Spanish month name for cut date, e.g. 'Ene'."""
    abbrs = {
        1: "Ene",
        2: "Feb",
        3: "Mar",
        4: "Abr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dic",
    }
    return abbrs[month]


class PDFWriter:
    """Helper to write lines to a reportlab canvas with auto-pagination."""

    def __init__(self, canvas, page_width: float, page_height: float):
        self.c = canvas
        self.page_width = page_width
        self.page_height = page_height
        self.y = page_height - 50  # start near top
        self.page_num = 1

    def set_font(self, name: str = "Helvetica", size: int = BODY_FONT_SIZE):
        self.c.setFont(name, size)

    def write_line(self, text: str, x: float = LEFT, font_size: int = BODY_FONT_SIZE):
        """Write a single line at the current Y position, advancing down."""
        if self.y < 50:
            self._new_page()
        self.c.setFont("Helvetica", font_size)
        self.c.drawString(x, self.y, text)
        self.y -= LINE_HEIGHT

    def skip_line(self):
        self.y -= LINE_HEIGHT

    def force_new_page(self):
        self._new_page()

    def _new_page(self):
        self.c.showPage()
        self.page_num += 1
        self.y = self.page_height - 50

    @property
    def near_bottom(self) -> bool:
        return self.y < 80


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------


def write_first_page(w: PDFWriter) -> None:
    """Write the first page (summary) with statement metadata."""
    info = STATEMENT_INFO

    w.write_line("Estado de Cuenta", font_size=HEADER_FONT_SIZE)
    w.skip_line()
    w.write_line("American Express")
    w.skip_line()
    w.write_line(f"Numero de Cuenta {info['account']}")
    w.skip_line()
    w.write_line(f"Tarjetahabiente {info['account'][:4]}")
    w.write_line(info["cardholder"])
    w.skip_line()

    # Cut date: "08-Ene-2026"
    cut_day = f"{info['cut_date_day']:02d}"
    cut_month = _month_abbr_title(info["cut_date_month"])
    cut_year = info["cut_date_year"]
    w.write_line(f"{cut_day}-{cut_month}-{cut_year}")
    w.skip_line()

    # Period line with pdfplumber-style spacing artifacts
    # "Del 9 deDiciembre al8 deEnero de2026"
    ps_day = info["period_start_day"]
    ps_month = _month_name(info["period_start_month"])
    pe_day = info["period_end_day"]
    pe_month = _month_name(info["period_end_month"])
    pe_year = info["period_end_year"]
    period_line = f"Del {ps_day} de{ps_month} al{pe_day} de{pe_month} de{pe_year}"
    w.write_line(period_line)
    w.skip_line()

    w.write_line("Saldo anterior $50,000.00")
    w.skip_line()


def _format_tx_date_line(tx: dict) -> str:
    """Build the main transaction line: 'DD deMes DESCRIPTION AMOUNT'."""
    day = tx["day"]
    month = _month_name(tx["month"])
    desc = tx["description"]
    amt = format_amount(tx["amount"])
    # No space between 'de' and month name to match pdfplumber extraction
    return f"{day} de{month} {desc} {amt}"


def _format_split_date_line1(tx: dict) -> str:
    """For split-date: 'DD de DESCRIPTION AMOUNT' (no real month on this line).

    The TX_DATE_RE will capture the first word of description as the "month".
    Since it's not a valid month, the parser looks at the next line.
    """
    day = tx["day"]
    desc = tx["description"]
    amt = format_amount(tx["amount"])
    # "18 de GRACIAS POR SU PAGO EN LINEA 6,005.17"
    # The regex will match: day=18, fake_month="GRACIAS", rest="POR SU PAGO EN LINEA", amount=6005.17
    return f"{day} de {desc} {amt}"


def _format_split_date_line2(tx: dict) -> str:
    """The continuation line with the real month (and optional CR).

    e.g. "Diciembre CR" or "Diciembre"
    """
    month = _month_name(tx["month"])
    if tx.get("is_credit"):
        return f"{month} CR"
    return month


def _format_orphan_line(tx: dict) -> str:
    """Orphan transaction: 'DESCRIPTION AMOUNT' (no date prefix)."""
    desc = tx["description"]
    amt = format_amount(tx["amount"])
    return f"{desc} {amt}"


def write_transactions(
    w: PDFWriter, transactions: list[dict], cardholder_filter: str | None
) -> float:
    """Write transaction lines for a given cardholder group.

    Returns the sum of amounts (positive for charges, respecting is_credit).
    """
    total = 0.0
    orphan_queue: list[dict] = []
    regular_txs: list[dict] = []

    # Separate orphans from regular
    for tx in transactions:
        ch = tx.get("cardholder", "titular")
        if cardholder_filter == "additional" and ch != "additional":
            continue
        if cardholder_filter == "titular" and ch == "additional":
            continue

        if tx.get("orphan"):
            orphan_queue.append(tx)
        else:
            regular_txs.append(tx)

    orphan_idx = 0

    for _tx_i, tx in enumerate(regular_txs):
        # Place orphans right after a page break
        if w.near_bottom:
            w.force_new_page()
            # Insert orphan(s) at top of new page
            while orphan_idx < len(orphan_queue):
                otx = orphan_queue[orphan_idx]
                orphan_idx += 1
                w.write_line(_format_orphan_line(otx))
                # Orphan metadata
                if otx.get("is_credit"):
                    w.write_line("CR")
                if otx.get("rfc"):
                    w.write_line(otx["rfc"])
                total += -otx["amount"] if otx.get("is_credit") else otx["amount"]

        is_split = tx.get("split_date", False)

        if is_split:
            w.write_line(_format_split_date_line1(tx))
            w.write_line(_format_split_date_line2(tx))
        else:
            w.write_line(_format_tx_date_line(tx))

        # Metadata lines
        if tx.get("is_credit") and not is_split:
            w.write_line("CR")

        if tx.get("rfc"):
            w.write_line(tx["rfc"])

        if tx.get("installment"):
            w.write_line(f"CARGO {tx['installment']}")

        if tx.get("foreign_usd"):
            usd = tx["foreign_usd"]
            rate = tx["exchange_rate"]
            w.write_line(f"D\u00f3lar U.S.A. {format_amount(usd)} TC:{rate}")

        if tx.get("is_credit"):
            total -= tx["amount"]
        else:
            total += tx["amount"]

    # Write any remaining orphans
    while orphan_idx < len(orphan_queue):
        otx = orphan_queue[orphan_idx]
        orphan_idx += 1
        w.write_line(_format_orphan_line(otx))
        if otx.get("is_credit"):
            w.write_line("CR")
        if otx.get("rfc"):
            w.write_line(otx["rfc"])
        total += -otx["amount"] if otx.get("is_credit") else otx["amount"]

    return total


def write_transaction_pages(w: PDFWriter) -> None:
    """Write all transaction pages (page 2+)."""
    w.force_new_page()
    info = STATEMENT_INFO

    # Header for transaction pages
    w.write_line("Fecha y Detalle de sus Transacciones", font_size=HEADER_FONT_SIZE)
    w.skip_line()

    # Pedro's transactions
    pedro_total = write_transactions(w, TRANSACTIONS, "titular")
    w.skip_line()
    w.write_line(
        f"Total de las transacciones en $ de {info['cardholder']} {format_amount(abs(pedro_total))}"
    )
    w.skip_line()

    # Maria's transactions
    maria_total = write_transactions(w, TRANSACTIONS, "additional")
    w.skip_line()
    w.write_line(
        f"Total de las transacciones en $ de {info['additional_cardholder']} {format_amount(abs(maria_total))}"
    )
    w.skip_line()

    # Foreign total marker
    w.write_line("Total de Transacciones en Moneda Extranjera de")
    w.skip_line()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as canvas_mod

    PDFS_DIR.mkdir(exist_ok=True)
    output = PDFS_DIR / "amex_dec_jan_2026.pdf"

    page_w, page_h = letter
    c = canvas_mod.Canvas(str(output), pagesize=letter)

    w = PDFWriter(c, page_w, page_h)

    write_first_page(w)
    write_transaction_pages(w)

    c.save()
    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
