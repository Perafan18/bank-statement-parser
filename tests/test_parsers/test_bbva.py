"""Tests for the BBVA Mexico TDC (credit card) parser.

These tests validate info extraction, date parsing, and regular
transaction parsing against text extracted from a real BBVA TDC PDF statement.
"""

from datetime import date

import pytest

from bankparser.models import TransactionType
from bankparser.parsers.bbva import BBVAParser

BBVA_INFO_TEXT = """Descubre todo lo que tu TDC puede hacer por ti
Tu tarjeta de crédito te abre un mundo de oportunidades
BBVA MEXICO, S.A., INSTITUCION DE BANCA MULTIPLE, GRUPO FINANCIERO BBVA MEXICO.
Página 1 de 7
TU PAGO REQUERIDO ESTE PERIODO
JUAN GARCIA LOPEZ
Periodo: 08-ene-2026 al 07-feb-2026
Calle: AV REFORMA 100 DEPTO 5
Colonia: CENTRO Fecha de corte: 07-feb-2026
AFINIDAD UNAM BBVA (ORO) Pago para no generar intereses: $16,184.77
Número de tarjeta: 4152313099991234
Número de cliente:K1234567
Pago mínimo: $3,342.50
Adeudo del periodo anterior $19,810.48"""


class TestBBVAParser:
    @pytest.fixture
    def parser(self):
        return BBVAParser()

    def test_bank_name(self, parser):
        assert parser.bank_name == "bbva"

    def test_parse_bbva_date(self, parser):
        assert parser._parse_bbva_date("08-ene-2026") == date(2026, 1, 8)
        assert parser._parse_bbva_date("16-nov-2023") == date(2023, 11, 16)

    def test_extract_info_period(self, parser):
        info = parser._extract_info(BBVA_INFO_TEXT)
        assert info.period_start == date(2026, 1, 8)
        assert info.period_end == date(2026, 2, 7)

    def test_extract_info_account(self, parser):
        info = parser._extract_info(BBVA_INFO_TEXT)
        assert info.account_number == "4152313099991234"

    def test_extract_info_cardholder(self, parser):
        info = parser._extract_info(BBVA_INFO_TEXT)
        assert info.cardholder == "JUAN GARCIA LOPEZ"

    def test_extract_info_cut_date(self, parser):
        info = parser._extract_info(BBVA_INFO_TEXT)
        assert info.cut_date == date(2026, 2, 7)

    def test_extract_info_previous_balance(self, parser):
        info = parser._extract_info(BBVA_INFO_TEXT)
        assert info.previous_balance == 19810.48


# ── Regular transaction section fixture ────────────────────────────────────

BBVA_REGULAR_SECTION_TEXT = """\
CARGOS,COMPRAS Y ABONOS REGULARES(NO A MESES) Tarjeta titular: XXXXXXXXXXXX1234
Fecha
Fecha
de la Descripción del movimiento Monto
de cargo
operación
11-ene-2026 12-ene-2026 TIENDA ONLINE ; Tarjeta Digital ***3121 + $1,807.41
                        USD $100.45 TIPO DE CAMBIO $17.99
12-ene-2026 13-ene-2026 OTRA TIENDA ONLINE ; Tarjeta Digital ***3121 + $1,858.55
                        USD $103.74 TIPO DE CAMBIO $17.92
16-ene-2026 16-ene-2026 26 DE 36 EFECTIVO INMEDIATO 36 + $196.22
16-ene-2026 16-ene-2026 * INTERESES EFI * + $71.09
10-ene-2026 12-ene-2026 OXXO TONALA + $48.50
15-ene-2026 15-ene-2026 BMOVIL.PAGO TDC - $19,810.48
IVA :$ 44.67 Interes: $ 0.00 Comisiones:$0.00 Capital:$19,765.81
Capital de promoción:$0.00 Pago excedente:$0.00
18-ene-2026 19-ene-2026 SUPERMERCADO CENTRO + $230.00
23-ene-2026 26-ene-2026 CLINICA DENTAL ABC + $1,400.00
31-ene-2026 03-feb-2026 ABONO FINANC. COMPRAS 00MSI - $11,770.00
31-ene-2026 03-feb-2026 ALTA PARA MESES S/INTERESES + $11,770.00
31-ene-2026 03-feb-2026 CONTRATACION BENEFICIOS 3MSI + $647.35
07-ene-2026 08-ene-2026 03 DE 03 TIENDA GRANDE + $4,090.87
TOTAL CARGOS $38,924.32
TOTAL ABONOS -$31,580.48"""


class TestBBVARegularSection:
    """Tests for parsing the CARGOS,COMPRAS Y ABONOS REGULARES section."""

    @pytest.fixture
    def parser(self):
        return BBVAParser()

    @pytest.fixture
    def transactions(self, parser):
        lines = BBVA_REGULAR_SECTION_TEXT.split("\n")
        return parser._parse_regular_section(lines)

    def test_parse_regular_section_count(self, transactions):
        """Should parse exactly 12 transactions, skipping headers/totals/breakdowns."""
        assert len(transactions) == 12

    def test_parse_regular_charge(self, transactions):
        """OXXO TONALA should be a CHARGE with correct amount and date."""
        oxxo = [tx for tx in transactions if "OXXO" in tx.description][0]
        assert oxxo.amount == 48.50
        assert oxxo.tx_type == TransactionType.CHARGE
        assert oxxo.date == date(2026, 1, 10)

    def test_parse_regular_payment(self, transactions):
        """BMOVIL.PAGO TDC should be a PAYMENT with negative amount."""
        pago = [tx for tx in transactions if "BMOVIL" in tx.description][0]
        assert pago.amount == -19810.48
        assert pago.tx_type == TransactionType.PAYMENT

    def test_parse_regular_foreign_currency(self, transactions):
        """First TIENDA ONLINE should have foreign currency info."""
        tienda = [tx for tx in transactions if "TIENDA ONLINE" in tx.description][0]
        assert tienda.original_amount == 100.45
        assert tienda.original_currency == "USD"
        assert tienda.exchange_rate == 17.99

    def test_parse_regular_msi_installment(self, transactions):
        """26 DE 36 EFECTIVO INMEDIATO should be MSI with installment info."""
        msi = [tx for tx in transactions if "EFECTIVO INMEDIATO" in tx.description][0]
        assert msi.tx_type == TransactionType.MSI
        assert msi.installment == "26 DE 36"

    def test_parse_regular_interest(self, transactions):
        """* INTERESES EFI * should be classified as INTEREST."""
        interest = [tx for tx in transactions if "INTERESES" in tx.description][0]
        assert interest.tx_type == TransactionType.INTEREST

    def test_parse_regular_fee(self, transactions):
        """CONTRATACION BENEFICIOS should be classified as FEE."""
        fee = [tx for tx in transactions if "CONTRATACION BENEFICIOS" in tx.description][0]
        assert fee.tx_type == TransactionType.FEE

    def test_parse_regular_msi_adjustment(self, transactions):
        """ABONO FINANC. COMPRAS 00MSI should be MSI_ADJUSTMENT with negative amount."""
        adj = [tx for tx in transactions if "ABONO FINANC" in tx.description][0]
        assert adj.tx_type == TransactionType.MSI_ADJUSTMENT
        assert adj.amount < 0

    def test_parse_regular_alta_msi(self, transactions):
        """ALTA PARA MESES S/INTERESES should be MSI_ADJUSTMENT."""
        alta = [tx for tx in transactions if "ALTA PARA MESES" in tx.description][0]
        assert alta.tx_type == TransactionType.MSI_ADJUSTMENT

    def test_parse_regular_installment_prefix(self, transactions):
        """03 DE 03 TIENDA GRANDE should be MSI with installment info."""
        inst = [tx for tx in transactions if "TIENDA GRANDE" in tx.description][0]
        assert inst.tx_type == TransactionType.MSI
        assert inst.installment == "03 DE 03"

    def test_classify_iva_as_tax(self, parser):
        """IVA description should be classified as TAX."""
        assert parser._classify("IVA APLICABLE", False) == TransactionType.TAX
        assert parser._classify("IVA DE INTERESES", False) == TransactionType.TAX

    def test_classify_interest_not_iva(self, parser):
        """INTERESES should still be INTEREST when not starting with IVA."""
        assert parser._classify("* INTERESES EFI *", False) == TransactionType.INTEREST


# ── MSI sin intereses section fixture ─────────────────────────────────────

BBVA_MSI_SIN_TEXT = """\
COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES Tarjeta titular: XXXXXXXXXXXX1234
Tasa de
Fecha de la Monto Saldo Pago Núm. de
Descripción interés
operación original pendiente requerido pago
aplicable
31-ene-2026 COMPRA TIENDA GRANDE $11,770.00 $7,846.00 $3,924.00 1 de 3 0.00%"""


# ── MSI con intereses section fixture ─────────────────────────────────────

BBVA_MSI_CON_TEXT = """\
COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES Tarjeta titular: XXXXXXXXXXXX1234
IVA de
Fecha de la Monto Saldo Interes del Pago Num. Tasa de
Descripción interes del
operación Original pendiente periodo requerido de pago interes
periodo
aplicable
16-nov-2023 EFECTIVO INMEDIATO $6,304.00 $2,412.96 $74.40 $10.61 $279.79 26 de 36 33.00%
36 M.
16-nov-2023 EFECTIVO INMEDIATO $6,161.00 $2,358.33 $72.72 $10.37 $273.44 26 de 36 33.00%
36 M."""


class TestBBVAMSISinIntereses:
    """Tests for parsing the COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES section."""

    @pytest.fixture
    def parser(self):
        return BBVAParser()

    @pytest.fixture
    def transactions(self, parser):
        lines = BBVA_MSI_SIN_TEXT.split("\n")
        return parser._parse_msi_section(lines)

    def test_parse_msi_sin_intereses_count(self, transactions):
        """Should parse exactly 1 transaction from MSI sin intereses section."""
        assert len(transactions) == 1

    def test_parse_msi_sin_intereses_fields(self, transactions):
        """Should correctly extract date, amount, installment, and type."""
        tx = transactions[0]
        assert tx.date == date(2026, 1, 31)
        assert tx.amount == 11770.00
        assert tx.installment == "1 de 3"
        assert tx.tx_type == TransactionType.MSI


class TestBBVAMSIConIntereses:
    """Tests for parsing the COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES section."""

    @pytest.fixture
    def parser(self):
        return BBVAParser()

    @pytest.fixture
    def transactions(self, parser):
        lines = BBVA_MSI_CON_TEXT.split("\n")
        return parser._parse_msi_section(lines)

    def test_parse_msi_con_intereses_count(self, transactions):
        """Should parse exactly 2 transactions from MSI con intereses section."""
        assert len(transactions) == 2

    def test_parse_msi_con_intereses_fields(self, transactions):
        """First transaction should have correct date, amount, installment, and type."""
        tx = transactions[0]
        assert tx.date == date(2023, 11, 16)
        assert tx.amount == 6304.00
        assert tx.installment == "26 de 36"
        assert tx.tx_type == TransactionType.MSI

    def test_parse_msi_con_skips_continuation(self, transactions):
        """The '36 M.' continuation lines should not produce transactions."""
        # If continuation lines were parsed, we'd have more than 2 transactions
        assert len(transactions) == 2
        # Also verify none of the descriptions contain just "M."
        for tx in transactions:
            assert tx.description != "M."
            assert tx.description != "36 M."
