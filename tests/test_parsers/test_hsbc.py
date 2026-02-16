"""Tests for the HSBC Mexico parser."""

from datetime import date

import pytest

from bankparser.parsers.hsbc import HSBCParser


class TestHSBCParser:
    @pytest.fixture
    def parser(self):
        return HSBCParser()

    def test_bank_name(self, parser):
        assert parser.bank_name == "hsbc"

    def test_resolve_month(self, parser):
        assert parser._resolve_month("Ene") == 1
        assert parser._resolve_month("dic") == 12
        assert parser._resolve_month("01") == 1
        assert parser._resolve_month("13") is None

    def test_classify_payment(self, parser):
        from bankparser.models import TransactionType
        assert parser._classify("PAGO TARJETA", False) == TransactionType.PAYMENT

    def test_classify_fee(self, parser):
        from bankparser.models import TransactionType
        assert parser._classify("COMISION POR SERVICIO", False) == TransactionType.FEE
        assert parser._classify("ANUALIDAD TARJETA", False) == TransactionType.FEE

    def test_try_parse_with_posting_date(self, parser):
        line = "15 Ene AMAZON MX MARKETPLACE 16 Ene 1,234.56"
        tx = parser._try_parse_transaction(line, 2026)
        assert tx is not None
        assert tx.date == date(2026, 1, 15)
        assert tx.amount == 1234.56

    def test_try_parse_simple_format(self, parser):
        line = "22/Feb NETFLIX MEXICO 329.00"
        tx = parser._try_parse_transaction(line, 2026)
        assert tx is not None
        assert tx.date == date(2026, 2, 22)

    def test_try_parse_full_date(self, parser):
        line = "05/01/2026 WALMART MEXICO 2,500.00"
        tx = parser._try_parse_transaction(line, 2026)
        assert tx is not None
        assert tx.date == date(2026, 1, 5)
        assert tx.amount == 2500.0

    def test_try_parse_invalid_line(self, parser):
        assert parser._try_parse_transaction("not a transaction", 2026) is None
