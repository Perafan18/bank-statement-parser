"""Tests for the BBVA Mexico parser.

These tests validate parsing logic with synthetic data.
Integration tests with real PDFs should be added once sample
statements are available.
"""

from datetime import date

import pytest

from bankparser.parsers.bbva import BBVAParser


class TestBBVAParser:
    @pytest.fixture
    def parser(self):
        return BBVAParser()

    def test_bank_name(self, parser):
        assert parser.bank_name == "bbva"

    def test_resolve_month_abbrev(self, parser):
        assert parser._resolve_month("Ene") == 1
        assert parser._resolve_month("dic") == 12
        assert parser._resolve_month("FEB") == 2

    def test_resolve_month_numeric(self, parser):
        assert parser._resolve_month("01") == 1
        assert parser._resolve_month("12") == 12
        assert parser._resolve_month("00") is None
        assert parser._resolve_month("13") is None

    def test_classify_payment(self, parser):
        from bankparser.models import TransactionType
        assert parser._classify("PAGO DE TARJETA", False) == TransactionType.PAYMENT
        assert parser._classify("SU PAGO GRACIAS", False) == TransactionType.PAYMENT

    def test_classify_interest(self, parser):
        from bankparser.models import TransactionType
        assert parser._classify("INTERESES ORDINARIOS", False) == TransactionType.INTEREST

    def test_classify_charge(self, parser):
        from bankparser.models import TransactionType
        assert parser._classify("AMAZON MX", False) == TransactionType.CHARGE

    def test_is_credit_detection(self, parser):
        assert parser._is_credit("DEVOLUCION AMAZON") is True
        assert parser._is_credit("PAGO RECIBIDO") is True
        assert parser._is_credit("COMPRA OXXO") is False

    def test_try_parse_transaction_abbrev_month(self, parser):
        tx = parser._try_parse_transaction("15/Ene AMAZON MX MARKETPLACE CDMX 499.00", 2026)
        assert tx is not None
        assert tx.date == date(2026, 1, 15)
        assert tx.amount == 499.0
        assert "AMAZON" in tx.description

    def test_try_parse_transaction_numeric_month(self, parser):
        tx = parser._try_parse_transaction("03/02 SPOTIFY MEXICO 189.00", 2026)
        assert tx is not None
        assert tx.date == date(2026, 2, 3)
        assert tx.amount == 189.0

    def test_try_parse_garbage_line(self, parser):
        tx = parser._try_parse_transaction("This is not a transaction", 2026)
        assert tx is None

    def test_try_parse_header_line(self, parser):
        tx = parser._try_parse_transaction("Fecha Concepto Cargo Abono", 2026)
        assert tx is None
