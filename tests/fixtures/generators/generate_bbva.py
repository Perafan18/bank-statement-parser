"""Generate a realistic BBVA Mexico TDC (credit card) statement PDF for testing.

The generated PDF is designed to be parseable by BBVAParser with zero mocks.
It covers: regular charges, payments, credits, MSI installments, foreign USD,
IVA (tax), interest, fees, MSI adjustments, MSI sin intereses section,
and MSI con intereses section.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a standalone script from the generators directory
_GENERATORS_DIR = Path(__file__).resolve().parent
if str(_GENERATORS_DIR) not in sys.path:
    sys.path.insert(0, str(_GENERATORS_DIR))

from _shared import MONTHS_ES_ABBR_LOWER, PDFS_DIR, format_amount  # noqa: E402

# ---------------------------------------------------------------------------
# Statement metadata
# ---------------------------------------------------------------------------

STATEMENT_INFO = {
    "card_number": "4152313800123456",  # digits only (parser regex captures \d+)
    "card_number_display": "4152 3138 0012 3456",
    "cardholder": "PEDRO MARTINEZ GONZALEZ",
    "period_start_day": 8,
    "period_start_month": 1,
    "period_start_year": 2026,
    "period_end_day": 7,
    "period_end_month": 2,
    "period_end_year": 2026,
    "cut_date_day": 7,
    "cut_date_month": 2,
    "cut_date_year": 2026,
    "previous_balance": 45000.00,
}


def _bbva_date(day: int, month: int, year: int) -> str:
    """Format a BBVA-style date: DD-mmm-YYYY with lowercase abbreviated month."""
    return f"{day:02d}-{MONTHS_ES_ABBR_LOWER[month]}-{year}"


# ---------------------------------------------------------------------------
# Transaction data
# ---------------------------------------------------------------------------

# Regular section transactions (parsed by TX_RE):
#   Each dict has: op_day, op_month, op_year, ch_day, ch_month, ch_year,
#   description, amount, sign ('+' or '-').
#   Optional: foreign_currency, foreign_amount, exchange_rate, installment_prefix.

REGULAR_TRANSACTIONS: list[dict] = [
    # ---- Regular charges (~35 charges) ----------------------------------------
    {
        "op_day": 10,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 11,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "OXXO TONALA JALISCO",
        "amount": 48.50,
        "sign": "+",
    },
    {
        "op_day": 10,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 11,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "UBER EATS MX GUADALAJARA",
        "amount": 189.00,
        "sign": "+",
    },
    {
        "op_day": 11,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 12,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "AMAZON MX MARKETPLACE",
        "amount": 1_299.00,
        "sign": "+",
    },
    {
        "op_day": 12,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 13,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "COSTCO WHOLESALE GUADALAJARA",
        "amount": 4_567.89,
        "sign": "+",
    },
    {
        "op_day": 13,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 14,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SORIANA SUPER ZAPOPAN",
        "amount": 892.30,
        "sign": "+",
    },
    {
        "op_day": 14,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 15,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "LIVERPOOL CENTRO GDL",
        "amount": 3_450.00,
        "sign": "+",
    },
    {
        "op_day": 15,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 16,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "REST KIMODO POLANCO",
        "amount": 1_250.00,
        "sign": "+",
    },
    {
        "op_day": 16,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 17,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "FARMACIA GUADALAJARA SUC 415",
        "amount": 345.60,
        "sign": "+",
    },
    {
        "op_day": 17,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 18,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "CHEDRAUI SELECTO GUADALAJARA",
        "amount": 1_567.45,
        "sign": "+",
    },
    {
        "op_day": 18,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 19,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "HOME DEPOT MEXICO PERIFERICO",
        "amount": 2_890.00,
        "sign": "+",
    },
    {
        "op_day": 19,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 20,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "CINEPOLIS VIP ANDARES",
        "amount": 456.00,
        "sign": "+",
    },
    {
        "op_day": 20,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 21,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "TOTALPLAY TELECOMUNICACIONES",
        "amount": 799.00,
        "sign": "+",
    },
    {
        "op_day": 21,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 22,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "TELMEX RECIBO TELEFONICO",
        "amount": 589.00,
        "sign": "+",
    },
    {
        "op_day": 22,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 23,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "CFE SUMINISTRADOR BASICO",
        "amount": 1_234.56,
        "sign": "+",
    },
    {
        "op_day": 23,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 24,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "GAS NATURAL DEL NOROESTE",
        "amount": 678.90,
        "sign": "+",
    },
    {
        "op_day": 24,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 25,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SAMS CLUB GUADALAJARA PATRIA",
        "amount": 3_210.00,
        "sign": "+",
    },
    {
        "op_day": 25,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 26,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "RESTAURANTE LA TEQUILA GDL",
        "amount": 1_890.50,
        "sign": "+",
    },
    {
        "op_day": 26,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 27,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "GASOLINERA PEMEX 3456",
        "amount": 1_200.00,
        "sign": "+",
    },
    {
        "op_day": 27,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 28,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "STARBUCKS ANDARES GDL",
        "amount": 185.00,
        "sign": "+",
    },
    {
        "op_day": 28,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 29,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SUPERAMA GUADALAJARA PROVIDENCIA",
        "amount": 2_345.67,
        "sign": "+",
    },
    {
        "op_day": 29,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 30,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "PALACIO DE HIERRO ANDARES",
        "amount": 5_670.00,
        "sign": "+",
    },
    {
        "op_day": 30,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 31,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "UBER RIDES MX CIUDAD DE MEXICO",
        "amount": 234.50,
        "sign": "+",
    },
    {
        "op_day": 31,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 1,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "RAPPI MX GUADALAJARA",
        "amount": 312.00,
        "sign": "+",
    },
    {
        "op_day": 1,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 2,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "MERCADO LIBRE COMPRA",
        "amount": 1_489.00,
        "sign": "+",
    },
    {
        "op_day": 2,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 3,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "OFFICE DEPOT GUADALAJARA",
        "amount": 1_567.80,
        "sign": "+",
    },
    {
        "op_day": 3,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 4,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "LA COMER SUCURSAL CENTRO",
        "amount": 2_345.00,
        "sign": "+",
    },
    {
        "op_day": 4,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 5,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "SANBORNS RESTAURANT GDL",
        "amount": 456.90,
        "sign": "+",
    },
    {
        "op_day": 5,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 6,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "PETCO GUADALAJARA AMERICAS",
        "amount": 890.50,
        "sign": "+",
    },
    {
        "op_day": 6,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 7,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "BODEGA AURRERA ZAPOPAN",
        "amount": 1_345.00,
        "sign": "+",
    },
    {
        "op_day": 6,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 7,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "WALMART SUPERCENTER GUADALAJARA",
        "amount": 2_678.30,
        "sign": "+",
    },
    {
        "op_day": 7,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 7,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "ELEKTRA CENTRO GUADALAJARA",
        "amount": 3_456.00,
        "sign": "+",
    },
    {
        "op_day": 8,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 9,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "CLINICA DENTAL ABC",
        "amount": 1_400.00,
        "sign": "+",
    },
    {
        "op_day": 9,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 10,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "ZARA MEXICO ANDARES GDL",
        "amount": 2_345.00,
        "sign": "+",
    },
    {
        "op_day": 9,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 10,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "HEB GUADALAJARA PROVIDENCIA",
        "amount": 1_567.80,
        "sign": "+",
    },
    {
        "op_day": 10,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 11,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SUBURBIA CENTRO GUADALAJARA",
        "amount": 890.50,
        "sign": "+",
    },
    # ---- Payments (BMOVIL.PAGO TDC, '-' sign) ---------------------------------
    {
        "op_day": 15,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 15,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "BMOVIL.PAGO TDC",
        "amount": 19_810.48,
        "sign": "-",
    },
    {
        "op_day": 28,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 28,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "BMOVIL.PAGO TDC",
        "amount": 15_000.00,
        "sign": "-",
    },
    {
        "op_day": 5,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 5,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "PAGO EN SUCURSAL BANCARIA",
        "amount": 5_000.00,
        "sign": "-",
    },
    # ---- Credits ('-' sign, not PAGO/BMOVIL) -----------------------------------
    {
        "op_day": 20,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 21,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "DEVOLUCION LIVERPOOL",
        "amount": 1_200.00,
        "sign": "-",
    },
    {
        "op_day": 3,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 4,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "DEVOLUCION AMAZON MX",
        "amount": 350.00,
        "sign": "-",
    },
    # ---- Foreign USD with continuation line ------------------------------------
    {
        "op_day": 11,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 12,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "DIGITALOCEAN.COM AMSTERDAM",
        "amount": 630.30,
        "sign": "+",
        "foreign_currency": "USD",
        "foreign_amount": 35.45,
        "exchange_rate": 17.78,
    },
    {
        "op_day": 14,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 15,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "SPOTIFY AB STOCKHOLM",
        "amount": 199.90,
        "sign": "+",
        "foreign_currency": "USD",
        "foreign_amount": 11.24,
        "exchange_rate": 17.78,
    },
    {
        "op_day": 22,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 23,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "NETFLIX.COM LOS GATOS",
        "amount": 321.45,
        "sign": "+",
        "foreign_currency": "USD",
        "foreign_amount": 18.09,
        "exchange_rate": 17.77,
    },
    # ---- IVA (tax) — description starts with "IVA" ----------------------------
    {
        "op_day": 7,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 7,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "IVA DE INTERESES ORDINARIOS",
        "amount": 44.67,
        "sign": "+",
    },
    # ---- Interest -------------------------------------------------------------
    {
        "op_day": 7,
        "op_month": 2,
        "op_year": 2026,
        "ch_day": 7,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "INTERES ORDINARIO",
        "amount": 279.17,
        "sign": "+",
    },
    # ---- Fee ------------------------------------------------------------------
    {
        "op_day": 31,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 3,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "CONTRATACION BENEFICIOS PREFERENTE",
        "amount": 647.35,
        "sign": "+",
    },
    # ---- MSI Adjustment (ABONO FINANC.) ----------------------------------------
    {
        "op_day": 31,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 3,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "ABONO FINANC. COMPRAS A MESES S/INT",
        "amount": 11_770.00,
        "sign": "-",
    },
    # ---- MSI Adjustment (ALTA PARA MESES S/INTERESES) --------------------------
    {
        "op_day": 31,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 3,
        "ch_month": 2,
        "ch_year": 2026,
        "description": "ALTA PARA MESES S/INTERESES",
        "amount": 11_770.00,
        "sign": "+",
    },
    # ---- Installment prefix transactions (XX DE YY ...) -------------------------
    {
        "op_day": 16,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 16,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "26 DE 36 EFECTIVO INMEDIATO 36",
        "amount": 196.22,
        "sign": "+",
    },
    {
        "op_day": 7,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 8,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "03 DE 03 TIENDA GRANDE",
        "amount": 4_090.87,
        "sign": "+",
    },
    {
        "op_day": 20,
        "op_month": 1,
        "op_year": 2026,
        "ch_day": 21,
        "ch_month": 1,
        "ch_year": 2026,
        "description": "12 DE 18 MUEBLERIA STANDARD",
        "amount": 1_500.00,
        "sign": "+",
    },
]

# MSI sin intereses section transactions
MSI_SIN_TRANSACTIONS: list[dict] = [
    {
        "op_day": 31,
        "op_month": 1,
        "op_year": 2026,
        "description": "COMPRA TIENDA GRANDE",
        "original": 11_770.00,
        "pending": 7_846.00,
        "monthly": 3_924.00,
        "installment": "1 de 3",
        "rate": "0.00%",
    },
    {
        "op_day": 15,
        "op_month": 1,
        "op_year": 2026,
        "description": "LIVERPOOL CENTRO MSI",
        "original": 18_000.00,
        "pending": 15_000.00,
        "monthly": 3_000.00,
        "installment": "1 de 6",
        "rate": "0.00%",
    },
    {
        "op_day": 20,
        "op_month": 12,
        "op_year": 2025,
        "description": "HOME DEPOT MEXICO MSI",
        "original": 24_000.00,
        "pending": 20_000.00,
        "monthly": 2_000.00,
        "installment": "2 de 12",
        "rate": "0.00%",
    },
    {
        "op_day": 5,
        "op_month": 1,
        "op_year": 2026,
        "description": "PALACIO HIERRO ANDARES",
        "original": 36_000.00,
        "pending": 34_000.00,
        "monthly": 2_000.00,
        "installment": "1 de 18",
        "rate": "0.00%",
    },
]

# MSI con intereses section transactions
MSI_CON_TRANSACTIONS: list[dict] = [
    {
        "op_day": 16,
        "op_month": 11,
        "op_year": 2023,
        "description": "EFECTIVO INMEDIATO",
        "original": 6_304.00,
        "pending": 2_412.96,
        "interest": 74.40,
        "iva": 10.61,
        "monthly": 279.79,
        "installment": "26 de 36",
        "rate": "33.00%",
    },
    {
        "op_day": 16,
        "op_month": 11,
        "op_year": 2023,
        "description": "EFECTIVO INMEDIATO",
        "original": 6_161.00,
        "pending": 2_358.33,
        "interest": 72.72,
        "iva": 10.37,
        "monthly": 273.44,
        "installment": "26 de 36",
        "rate": "33.00%",
    },
    {
        "op_day": 1,
        "op_month": 3,
        "op_year": 2024,
        "description": "CREDITO PERSONAL",
        "original": 10_000.00,
        "pending": 6_500.00,
        "interest": 120.50,
        "iva": 19.28,
        "monthly": 550.00,
        "installment": "12 de 24",
        "rate": "28.00%",
    },
]


# ---------------------------------------------------------------------------
# PDF generation helpers
# ---------------------------------------------------------------------------

LEFT = 50
HEADER_FONT_SIZE = 14
BODY_FONT_SIZE = 9
LINE_HEIGHT = 13


class PDFWriter:
    """Helper to write lines to a reportlab canvas with auto-pagination."""

    def __init__(self, canvas, page_width: float, page_height: float):
        self.c = canvas
        self.page_width = page_width
        self.page_height = page_height
        self.y = page_height - 50
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
    """Write the first page with BBVA header and statement metadata."""
    info = STATEMENT_INFO

    w.write_line("Descubre todo lo que tu TDC puede hacer por ti", font_size=HEADER_FONT_SIZE)
    w.write_line("Tu tarjeta de credito te abre un mundo de oportunidades")
    w.write_line("BBVA MEXICO, S.A., INSTITUCION DE BANCA MULTIPLE, GRUPO FINANCIERO BBVA MEXICO.")
    w.write_line("Pagina 1 de 7")
    w.skip_line()

    w.write_line("TU PAGO REQUERIDO ESTE PERIODO")
    w.write_line(info["cardholder"])
    w.write_line(
        f"Periodo: {_bbva_date(info['period_start_day'], info['period_start_month'], info['period_start_year'])}"
        f" al {_bbva_date(info['period_end_day'], info['period_end_month'], info['period_end_year'])}"
    )
    w.write_line("Calle: AV REFORMA 100 DEPTO 5")
    w.write_line(
        f"Colonia: CENTRO Fecha de corte: "
        f"{_bbva_date(info['cut_date_day'], info['cut_date_month'], info['cut_date_year'])}"
    )
    w.write_line("AFINIDAD UNAM BBVA (ORO) Pago para no generar intereses: $16,184.77")
    w.write_line(f"N\u00famero de tarjeta: {info['card_number']}")
    w.write_line("N\u00famero de cliente:K1234567")
    w.write_line("Pago m\u00ednimo: $3,342.50")
    w.write_line(f"Adeudo del periodo anterior ${format_amount(info['previous_balance'])}")
    w.skip_line()


def _format_regular_tx_line(tx: dict) -> str:
    """Format a regular transaction line matching TX_RE pattern.

    Pattern: DD-mmm-YYYY DD-mmm-YYYY DESCRIPTION +/- $AMOUNT
    """
    op_date = _bbva_date(tx["op_day"], tx["op_month"], tx["op_year"])
    ch_date = _bbva_date(tx["ch_day"], tx["ch_month"], tx["ch_year"])
    desc = tx["description"]
    sign = tx["sign"]
    amt = format_amount(tx["amount"])
    return f"{op_date} {ch_date} {desc} {sign} ${amt}"


def _format_foreign_continuation(tx: dict) -> str:
    """Format a foreign currency continuation line matching FOREIGN_RE.

    Pattern: USD $AMOUNT TIPO DE CAMBIO $RATE
    """
    currency = tx["foreign_currency"]
    foreign_amt = format_amount(tx["foreign_amount"])
    rate = format_amount(tx["exchange_rate"])
    return f"{currency} ${foreign_amt} TIPO DE CAMBIO ${rate}"


def _format_msi_sin_line(tx: dict) -> str:
    """Format an MSI sin intereses line matching MSI_SIN_RE.

    Pattern: DD-mmm-YYYY DESCRIPTION $ORIGINAL $PENDING $MONTHLY NN de NN RATE%
    """
    dt = _bbva_date(tx["op_day"], tx["op_month"], tx["op_year"])
    desc = tx["description"]
    orig = format_amount(tx["original"])
    pend = format_amount(tx["pending"])
    monthly = format_amount(tx["monthly"])
    inst = tx["installment"]
    rate = tx["rate"]
    return f"{dt} {desc} ${orig} ${pend} ${monthly} {inst} {rate}"


def _format_msi_con_line(tx: dict) -> str:
    """Format an MSI con intereses line matching MSI_CON_RE.

    Pattern: DD-mmm-YYYY DESCRIPTION $ORIGINAL $PENDING $INTEREST $IVA $MONTHLY NN de NN RATE%
    """
    dt = _bbva_date(tx["op_day"], tx["op_month"], tx["op_year"])
    desc = tx["description"]
    orig = format_amount(tx["original"])
    pend = format_amount(tx["pending"])
    interest = format_amount(tx["interest"])
    iva = format_amount(tx["iva"])
    monthly = format_amount(tx["monthly"])
    inst = tx["installment"]
    rate = tx["rate"]
    return f"{dt} {desc} ${orig} ${pend} ${interest} ${iva} ${monthly} {inst} {rate}"


def write_regular_section(w: PDFWriter) -> None:
    """Write the CARGOS,COMPRAS Y ABONOS REGULARES section."""
    # Section header (must match exactly what the parser expects)
    w.write_line("CARGOS,COMPRAS Y ABONOS REGULARES(NO A MESES) Tarjeta titular: XXXXXXXXXXXX3456")
    # Column headers (these are skipped by the parser SKIP_PATTERNS)
    w.write_line("Fecha")
    w.write_line("Fecha")
    w.write_line("de la Descripcion del movimiento Monto")
    w.write_line("de cargo")
    w.write_line("operacion")
    w.skip_line()

    for tx in REGULAR_TRANSACTIONS:
        if w.near_bottom:
            w.force_new_page()

        w.write_line(_format_regular_tx_line(tx))

        # Foreign currency continuation line
        if "foreign_currency" in tx:
            w.write_line(f"                        {_format_foreign_continuation(tx)}")

    w.skip_line()
    w.write_line("TOTAL CARGOS $88,000.00")
    w.write_line("TOTAL ABONOS -$53,130.48")


def write_msi_sin_section(w: PDFWriter) -> None:
    """Write the COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES section."""
    if w.near_bottom:
        w.force_new_page()

    w.skip_line()
    w.write_line(
        "COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES Tarjeta titular: XXXXXXXXXXXX3456"
    )
    # Column headers (skipped by parser since they don't match MSI_SIN_RE)
    w.write_line("Tasa de")
    w.write_line("Fecha de la Monto Saldo Pago Num. de")
    w.write_line("Descripcion interes")
    w.write_line("operacion original pendiente requerido pago")
    w.write_line("aplicable")

    for tx in MSI_SIN_TRANSACTIONS:
        if w.near_bottom:
            w.force_new_page()
        w.write_line(_format_msi_sin_line(tx))


def write_msi_con_section(w: PDFWriter) -> None:
    """Write the COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES section."""
    if w.near_bottom:
        w.force_new_page()

    w.skip_line()
    w.write_line(
        "COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES Tarjeta titular: XXXXXXXXXXXX3456"
    )
    # Column headers (skipped by parser since they don't match MSI_CON_RE)
    w.write_line("IVA de")
    w.write_line("Fecha de la Monto Saldo Interes del Pago Num. Tasa de")
    w.write_line("Descripcion interes del")
    w.write_line("operacion Original pendiente periodo requerido de pago interes")
    w.write_line("periodo")
    w.write_line("aplicable")

    for tx in MSI_CON_TRANSACTIONS:
        if w.near_bottom:
            w.force_new_page()
        w.write_line(_format_msi_con_line(tx))
        # Continuation line (e.g. "36 M.") that parser should skip
        w.write_line("36 M.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as canvas_mod

    PDFS_DIR.mkdir(exist_ok=True)
    output = PDFS_DIR / "bbva_jan_2026.pdf"

    page_w, page_h = letter
    c = canvas_mod.Canvas(str(output), pagesize=letter)

    w = PDFWriter(c, page_w, page_h)

    write_first_page(w)
    write_regular_section(w)
    write_msi_sin_section(w)
    write_msi_con_section(w)

    c.save()
    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
