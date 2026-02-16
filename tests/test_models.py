"""Tests for core data models."""

from datetime import date

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType


class TestTransaction:
    def test_charge_is_positive(self):
        tx = Transaction(date=date(2026, 1, 10), description="Test", amount=100.0)
        assert tx.amount > 0
        assert not tx.is_credit

    def test_credit_is_negative(self):
        tx = Transaction(date=date(2026, 1, 10), description="Test", amount=-100.0)
        assert tx.is_credit

    def test_abs_amount(self):
        tx = Transaction(date=date(2026, 1, 10), description="Test", amount=-500.50)
        assert tx.abs_amount == 500.50

    def test_is_foreign(self):
        tx = Transaction(
            date=date(2026, 1, 10), description="Test", amount=629.79,
            original_amount=35.45, original_currency="USD", exchange_rate=17.76,
        )
        assert tx.is_foreign

    def test_not_foreign(self):
        tx = Transaction(date=date(2026, 1, 10), description="Test", amount=100.0)
        assert not tx.is_foreign

    def test_to_dict(self):
        tx = Transaction(
            date=date(2026, 1, 10), description="AMAZON", amount=499.0,
            bank="amex", tx_type=TransactionType.CHARGE,
        )
        d = tx.to_dict()
        assert d["date"] == "2026-01-10"
        assert d["description"] == "AMAZON"
        assert d["amount"] == 499.0
        assert d["type"] == "charge"
        assert d["bank"] == "amex"

    def test_default_values(self):
        tx = Transaction(date=date(2026, 1, 1), description="X", amount=1.0)
        assert tx.currency == "MXN"
        assert tx.tx_type == TransactionType.CHARGE
        assert tx.tags == []
        assert tx.category == ""


class TestParseResult:
    def test_totals(self, sample_transactions):
        result = ParseResult(
            info=StatementInfo(),
            transactions=sample_transactions,
        )
        assert result.total_charges > 0
        assert result.total_credits < 0
        assert result.transaction_count == 7

    def test_empty(self):
        result = ParseResult(info=StatementInfo(), transactions=[])
        assert result.total_charges == 0.0
        assert result.total_credits == 0.0
        assert result.transaction_count == 0
