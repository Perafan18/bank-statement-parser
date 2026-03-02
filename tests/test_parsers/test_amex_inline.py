"""Tests for AmexParser using inline text fixtures (no PDF required)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from bankparser.models import TransactionType
from bankparser.parsers.amex import AmexParser

# ── Inline text fixtures ──────────────────────────────────────────────────────

AMEX_FIRST_PAGE = """\
Estado de Cuenta
American Express
Número de Cuenta 3717-123456-12345
Tarjetahabiente 3717
JUAN GARCIA LOPEZ

08-Feb-2026

Del 9 de Enero al 8 de Febrero de 2026

Saldo anterior $50,000.00
"""

AMEX_TX_PAGE = """\
15 deEnero OXXO TONALA JALISCO 48.50
RFCOXO123456789 /REF12345
16 deEnero GRACIAS POR SU PAGO EN LINEA 10,000.00
CR
17 deEnero AMAZON MX MARKETPLACE MEXICO 499.00
CARGO 03 DE 12
RFCANE140618P37 /REFabc123
18 deEnero DIGITALOCEAN.COM BROOMFIELD 629.79
Dólar U.S.A. 35.45 TC:17.76559
20 deEnero CUOTA ANUAL 1,500.00
21 deEnero IVA APLICABLE 240.00
22 deEnero INTERÉS FINANCIERO 5,355.07
23 deEnero MONTO A DIFERIR COMPRA MSI 1,000.00
24 deEnero MESES EN AUTOMÁTICO TIENDA 2,000.00
25 deEnero DEVOLUCION TIENDA MX 300.00
CR
Total de las transacciones en $ de JUAN GARCIA LOPEZ 19,272.36
26 deEnero COMPRA ADICIONAL TIENDA 150.00
Total de las transacciones en $ de MARIA GARCIA 150.00
Total de Transacciones en Moneda Extranjera de
"""


class TestAmexCanParse:
    @pytest.fixture
    def parser(self):
        return AmexParser()

    def test_can_parse_amex_text(self, parser):
        with patch.object(parser, "extract_first_page_text", return_value=AMEX_FIRST_PAGE):
            assert parser.can_parse(Path("test.pdf")) is True

    def test_can_parse_non_amex(self, parser):
        with patch.object(parser, "extract_first_page_text", return_value="BBVA Mexico"):
            assert parser.can_parse(Path("test.pdf")) is False

    def test_can_parse_amex_prefix(self, parser):
        with patch.object(parser, "extract_first_page_text", return_value="Cuenta 3717-123"):
            assert parser.can_parse(Path("test.pdf")) is True


class TestAmexExtractInfo:
    @pytest.fixture
    def parser(self):
        return AmexParser()

    def test_extract_account_number(self, parser):
        info = parser._extract_info(AMEX_FIRST_PAGE)
        assert info.account_number == "3717-123456-12345"

    def test_extract_period(self, parser):
        info = parser._extract_info(AMEX_FIRST_PAGE)
        assert info.period_start == date(2026, 1, 9)
        assert info.period_end == date(2026, 2, 8)

    def test_extract_cut_date(self, parser):
        info = parser._extract_info(AMEX_FIRST_PAGE)
        assert info.cut_date == date(2026, 2, 8)

    def test_extract_cut_date_full_month(self, parser):
        page = AMEX_FIRST_PAGE.replace("08-Feb-2026", "08-Febrero-2026")
        info = parser._extract_info(page)
        assert info.cut_date == date(2026, 2, 8)

    def test_extract_cardholder(self, parser):
        info = parser._extract_info(AMEX_FIRST_PAGE)
        assert info.cardholder == "JUAN GARCIA LOPEZ"

    def test_extract_bank_name(self, parser):
        info = parser._extract_info(AMEX_FIRST_PAGE)
        assert info.bank == "amex"


class TestAmexParse:
    @pytest.fixture
    def parser(self):
        return AmexParser()

    @pytest.fixture
    def result(self, parser):
        with patch.object(
            parser,
            "extract_text_from_pdf",
            return_value=[AMEX_FIRST_PAGE, AMEX_TX_PAGE],
        ):
            return parser.parse(Path("test.pdf"))

    def test_transaction_count(self, result):
        assert result.transaction_count >= 10

    def test_bank_is_amex(self, result):
        assert result.info.bank == "amex"

    def test_regular_charge(self, result):
        oxxo = [tx for tx in result.transactions if "OXXO" in tx.description]
        assert len(oxxo) == 1
        assert oxxo[0].amount == 48.50
        assert oxxo[0].tx_type == TransactionType.CHARGE

    def test_payment_is_negative(self, result):
        payments = [tx for tx in result.transactions if tx.tx_type == TransactionType.PAYMENT]
        assert len(payments) >= 1
        assert payments[0].amount < 0

    def test_foreign_transaction(self, result):
        foreign = [tx for tx in result.transactions if tx.is_foreign]
        assert len(foreign) >= 1
        do_tx = foreign[0]
        assert do_tx.original_currency == "USD"
        assert do_tx.original_amount == 35.45
        assert do_tx.exchange_rate == 17.76559

    def test_installment(self, result):
        msi = [tx for tx in result.transactions if tx.installment]
        assert len(msi) >= 1
        assert "03 DE 12" in msi[0].installment

    def test_reference(self, result):
        with_ref = [tx for tx in result.transactions if tx.reference]
        assert len(with_ref) >= 1

    def test_fee(self, result):
        fees = [tx for tx in result.transactions if tx.tx_type == TransactionType.FEE]
        assert len(fees) >= 1
        assert fees[0].amount == 1500.00

    def test_tax(self, result):
        taxes = [tx for tx in result.transactions if tx.tx_type == TransactionType.TAX]
        assert len(taxes) >= 1

    def test_interest(self, result):
        interest = [tx for tx in result.transactions if tx.tx_type == TransactionType.INTEREST]
        assert len(interest) >= 1
        assert interest[0].amount == 5355.07

    def test_msi_adjustment(self, result):
        adj = [tx for tx in result.transactions if tx.tx_type == TransactionType.MSI_ADJUSTMENT]
        assert len(adj) >= 1

    def test_msi_auto(self, result):
        msi = [tx for tx in result.transactions if tx.tx_type == TransactionType.MSI]
        assert len(msi) >= 1

    def test_credit(self, result):
        credits = [tx for tx in result.transactions if tx.tx_type == TransactionType.CREDIT]
        assert len(credits) >= 1
        assert credits[0].amount < 0

    def test_cardholder_resolution(self, result):
        cardholders = {tx.cardholder for tx in result.transactions}
        assert len(cardholders) >= 2
        assert "MARIA GARCIA" in cardholders


class TestAmexClassify:
    @pytest.fixture
    def parser(self):
        return AmexParser()

    def test_classify_payment(self, parser):
        assert parser._classify("GRACIAS POR SU PAGO EN LINEA", False) == TransactionType.PAYMENT

    def test_classify_msi_adjustment(self, parser):
        assert parser._classify("MONTO A DIFERIR COMPRA", False) == TransactionType.MSI_ADJUSTMENT

    def test_classify_msi(self, parser):
        assert parser._classify("MESES EN AUTOMÁTICO TIENDA", False) == TransactionType.MSI

    def test_classify_fee(self, parser):
        assert parser._classify("CUOTA ANUAL", False) == TransactionType.FEE

    def test_classify_tax(self, parser):
        assert parser._classify("IVA APLICABLE", False) == TransactionType.TAX

    def test_classify_interest(self, parser):
        assert parser._classify("INTERÉS FINANCIERO", False) == TransactionType.INTEREST

    def test_classify_interest_no_accent(self, parser):
        assert parser._classify("INTERES FINANCIERO", False) == TransactionType.INTEREST

    def test_classify_credit(self, parser):
        assert parser._classify("SOME STORE", True) == TransactionType.CREDIT

    def test_classify_charge(self, parser):
        assert parser._classify("OXXO TONALA", False) == TransactionType.CHARGE


class TestAmexShouldSkip:
    @pytest.fixture
    def parser(self):
        return AmexParser()

    def test_skip_estado_cuenta(self, parser):
        assert parser._should_skip("Estado de Cuenta") is True

    def test_skip_total_nuevos_cargos(self, parser):
        assert parser._should_skip("Total Nuevos Cargos") is True

    def test_no_skip_transaction(self, parser):
        assert parser._should_skip("15 deEnero OXXO 48.50") is False


class TestAmexParseEdgeCases:
    @pytest.fixture
    def parser(self):
        return AmexParser()

    def test_parse_empty_pdf(self, parser):
        """Parse with empty pages should return empty result."""
        with patch.object(parser, "extract_text_from_pdf", return_value=[""]):
            result = parser.parse(Path("test.pdf"))
            assert result.transaction_count == 0

    def test_parse_bad_date_generates_warning(self, parser):
        """Invalid month name should generate a warning, not crash."""
        bad_page = "15 deXyzabc STORE NAME 100.00\n"
        with patch.object(
            parser,
            "extract_text_from_pdf",
            return_value=[AMEX_FIRST_PAGE, bad_page],
        ):
            result = parser.parse(Path("test.pdf"))
            assert any("Could not parse date" in w for w in result.warnings)


# ── Fixtures for Dec-Jan split-date tests ────────────────────────────────────

AMEX_FIRST_PAGE_DEC_JAN = """\
Estado de Cuenta
American Express
Número de Cuenta 3717-123456-12345
Tarjetahabiente 3717
JUAN GARCIA LOPEZ

08-Ene-2026

Del 9 deDiciembre al8 deEnero de2026

Saldo anterior $50,000.00
"""

AMEX_SPLIT_DATE_PAGE = """\
18 de GRACIAS POR SU PAGO EN LINEA 6,005.17
Diciembre CR
20 de AMAZON MX MARKETPLACE MEXICO 1,234.56
Diciembre
RFCANE140618P37
22 de UBER EATS MX CDMX 345.00
Diciembre
CARGO 01 DE 03
5 deEnero OXXO TONALA JALISCO 48.50
7 de PAYPAL *SPOTIFY 115.00
Enero
PAYPAL *UBRPAGOSMEX 4029357733 56.95
Total de las transacciones en $ de JUAN GARCIA LOPEZ 99,999.99
"""


class TestAmexSplitDate:
    @pytest.fixture
    def parser(self):
        return AmexParser()

    @pytest.fixture
    def result(self, parser):
        with patch.object(
            parser,
            "extract_text_from_pdf",
            return_value=[AMEX_FIRST_PAGE_DEC_JAN, AMEX_SPLIT_DATE_PAGE],
        ):
            return parser.parse(Path("test.pdf"))

    def test_split_date_count(self, result):
        """All transactions should parse: 3 split-date Dec + 1 single-line Jan + 1 split Jan + 1 orphan."""
        assert result.transaction_count == 6

    def test_split_date_payment_cr(self, result):
        """GRACIAS POR SU PAGO with CR on month line should be negative."""
        payments = [tx for tx in result.transactions if tx.tx_type == TransactionType.PAYMENT]
        assert len(payments) == 1
        assert payments[0].amount < 0
        assert payments[0].amount == -6005.17

    def test_split_date_december_year(self, result):
        """December dates should have year 2025 (before period end Jan 8 2026)."""
        dec_txs = [tx for tx in result.transactions if tx.date.month == 12]
        assert len(dec_txs) >= 3
        for tx in dec_txs:
            assert tx.date.year == 2025

    def test_split_date_january_year(self, result):
        """January dates should have year 2026."""
        jan_txs = [tx for tx in result.transactions if tx.date.month == 1]
        assert len(jan_txs) >= 2
        for tx in jan_txs:
            assert tx.date.year == 2026

    def test_split_date_description(self, result):
        """Description should be reconstructed from false month + original description."""
        payments = [tx for tx in result.transactions if tx.tx_type == TransactionType.PAYMENT]
        assert len(payments) == 1
        assert "GRACIAS POR SU PAGO EN LINEA" in payments[0].description

    def test_split_date_rfc_on_next_line(self, result):
        """RFC on line after month continuation should be captured as reference."""
        amazon = [tx for tx in result.transactions if "AMAZON" in tx.description]
        assert len(amazon) == 1
        assert "RFC" in amazon[0].reference

    def test_split_date_installment(self, result):
        """CARGO line after split-date transaction should set installment."""
        uber = [tx for tx in result.transactions if "UBER" in tx.description]
        assert len(uber) == 1
        assert "01 DE 03" in uber[0].installment

    def test_single_line_still_works(self, result):
        """Normal single-line format '5 deEnero OXXO...' should still parse."""
        oxxo = [tx for tx in result.transactions if "OXXO" in tx.description]
        assert len(oxxo) == 1
        assert oxxo[0].date == date(2026, 1, 5)

    def test_orphan_parsed(self, result):
        """Orphan transaction (no date prefix) should be parsed."""
        paypal_ubr = [tx for tx in result.transactions if "UBRPAGOSMEX" in tx.description]
        assert len(paypal_ubr) == 1

    def test_orphan_uses_last_date(self, result):
        """Orphan transaction should use date from previous transaction."""
        paypal_ubr = [tx for tx in result.transactions if "UBRPAGOSMEX" in tx.description]
        assert len(paypal_ubr) == 1
        # Previous tx is "7 de Enero" split → Jan 7 2026
        assert paypal_ubr[0].date == date(2026, 1, 7)


class TestAmexPeriodDecJan:
    @pytest.fixture
    def parser(self):
        return AmexParser()

    def test_period_dec_jan(self, parser):
        """Period with no-space 'deDiciembre' should parse with year boundary."""
        info = parser._extract_info(AMEX_FIRST_PAGE_DEC_JAN)
        assert info.period_start == date(2025, 12, 9)
        assert info.period_end == date(2026, 1, 8)

    def test_abbreviated_month_cut_date(self, parser):
        """Cut date with abbreviated month (Ene) should parse."""
        info = parser._extract_info(AMEX_FIRST_PAGE_DEC_JAN)
        assert info.cut_date == date(2026, 1, 8)
