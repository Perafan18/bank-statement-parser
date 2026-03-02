"""Tests for the Amex Mexico parser."""

from datetime import date
from pathlib import Path

import pytest

from bankparser.models import TransactionType
from bankparser.parsers.amex import AmexParser
from bankparser.parsers.base import BaseParser


class TestBaseParserHelpers:
    """Test shared helper methods from BaseParser."""

    def test_parse_spanish_date(self):
        d = BaseParser.parse_spanish_date(15, "Enero", 2026)
        assert d == date(2026, 1, 15)

    def test_parse_spanish_date_lowercase(self):
        d = BaseParser.parse_spanish_date(8, "febrero", 2026)
        assert d == date(2026, 2, 8)

    def test_parse_spanish_date_invalid_month(self):
        with pytest.raises(ValueError):
            BaseParser.parse_spanish_date(1, "Foobar", 2026)

    def test_parse_mx_amount(self):
        assert BaseParser.parse_mx_amount("1,234.56") == 1234.56
        assert BaseParser.parse_mx_amount("99.00") == 99.0
        assert BaseParser.parse_mx_amount("10,972.15") == 10972.15

    def test_parse_mx_amount_with_dollar_sign(self):
        assert BaseParser.parse_mx_amount("$1,500.00") == 1500.0

    def test_parse_mx_amount_bad_input(self):
        """OCR artifacts or empty strings should raise ValueError with context."""
        with pytest.raises(ValueError, match="Cannot parse amount"):
            BaseParser.parse_mx_amount("")

    def test_parse_mx_amount_ocr_artifact(self):
        """Letter O instead of digit 0 should raise ValueError with context."""
        with pytest.raises(ValueError, match="Cannot parse amount"):
            BaseParser.parse_mx_amount("1O4.50")


class TestAmexParser:
    """Test Amex parser with the actual uploaded statement."""

    @pytest.fixture
    def parser(self):
        return AmexParser()

    @pytest.fixture
    def pdf_path(self):
        """Path to the uploaded Amex statement (if available)."""
        path = Path("/mnt/user-data/uploads/9_ene_2026_-_8_feb_2026.pdf")
        if not path.exists():
            pytest.skip("Amex statement PDF not available")
        return path

    def test_can_parse_amex(self, parser, pdf_path):
        assert parser.can_parse(pdf_path) is True

    def test_parse_returns_transactions(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        assert result.transaction_count > 0

    def test_parse_transaction_count(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        # Known: 89 transactions in this statement
        assert result.transaction_count == 89

    def test_parse_totals(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        charges = sum(tx.amount for tx in result.transactions if tx.amount > 0)
        assert abs(charges - 89020.11) < 1.0  # Allow small float rounding

    def test_parse_payments(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        payments = [tx for tx in result.transactions if tx.tx_type == TransactionType.PAYMENT]
        assert len(payments) == 3
        total_paid = sum(abs(tx.amount) for tx in payments)
        assert abs(total_paid - 48992.36) < 0.01

    def test_parse_foreign_transactions(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        foreign = [tx for tx in result.transactions if tx.is_foreign]
        assert len(foreign) > 0

        # Check a known foreign transaction (DigitalOcean)
        do_tx = [tx for tx in foreign if "DIGITALOCEAN" in tx.description]
        assert len(do_tx) == 1
        assert do_tx[0].original_currency == "USD"
        assert do_tx[0].original_amount == 35.45

    def test_parse_installments(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        msi = [tx for tx in result.transactions if tx.installment]
        assert len(msi) > 0

        # Macstore should be 03 DE 12
        macstore = [tx for tx in msi if "Macstore" in tx.description]
        assert len(macstore) == 1
        assert "03 DE 12" in macstore[0].installment

    def test_parse_credits(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        credits = [tx for tx in result.transactions if tx.tx_type == TransactionType.CREDIT]
        assert len(credits) > 0

    def test_parse_fees_and_interest(self, parser, pdf_path):
        result = parser.parse(pdf_path)

        fees = [tx for tx in result.transactions if tx.tx_type == TransactionType.FEE]
        assert len(fees) >= 1  # At least annual fee

        interest = [tx for tx in result.transactions if tx.tx_type == TransactionType.INTEREST]
        assert len(interest) == 1
        assert interest[0].amount == 5355.07

    def test_parse_cardholders(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        cardholders = {tx.cardholder for tx in result.transactions}
        # Should have at least 2 distinct cardholders
        assert len(cardholders) >= 2

    def test_parse_statement_info(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        assert result.info.bank == "amex"
        assert result.info.account_number != ""

    def test_all_dates_in_range(self, parser, pdf_path):
        result = parser.parse(pdf_path)
        for tx in result.transactions:
            assert date(2026, 1, 1) <= tx.date <= date(2026, 2, 28)
