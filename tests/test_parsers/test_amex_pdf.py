"""Integration tests for AmexParser using generated PDF fixture."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from bankparser.models import TransactionType
from bankparser.parsers.amex import AmexParser

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pdfs" / "amex_dec_jan_2026.pdf"

pytestmark = pytest.mark.skipif(not FIXTURE.exists(), reason="Amex PDF fixture not generated")


@pytest.fixture(scope="module")
def result():
    parser = AmexParser()
    return parser.parse(FIXTURE)


def test_bank_is_amex(result):
    assert result.info.bank == "amex"


def test_account_number(result):
    assert result.info.account_number.startswith("3717")


def test_period_crosses_year(result):
    assert result.info.period_start is not None
    assert result.info.period_end is not None
    assert result.info.period_start.month == 12
    assert result.info.period_start.year == 2025
    assert result.info.period_end.month == 1
    assert result.info.period_end.year == 2026


def test_cut_date(result):
    assert result.info.cut_date == date(2026, 1, 8)


def test_cardholder(result):
    assert result.info.cardholder == "PEDRO MARTINEZ GONZALEZ"


def test_transaction_count(result):
    assert len(result.transactions) == 61


def test_no_warnings(result):
    assert len(result.warnings) == 0


def test_december_dates_are_2025(result):
    dec_txs = [tx for tx in result.transactions if tx.date.month == 12]
    assert len(dec_txs) > 0
    assert all(tx.date.year == 2025 for tx in dec_txs)


def test_january_dates_are_2026(result):
    jan_txs = [tx for tx in result.transactions if tx.date.month == 1]
    assert len(jan_txs) > 0
    assert all(tx.date.year == 2026 for tx in jan_txs)


def test_has_payments(result):
    payments = [tx for tx in result.transactions if tx.tx_type == TransactionType.PAYMENT]
    assert len(payments) >= 2
    assert all(tx.amount < 0 for tx in payments)


def test_has_credits(result):
    credits = [tx for tx in result.transactions if tx.tx_type == TransactionType.CREDIT]
    assert len(credits) >= 2
    assert all(tx.amount < 0 for tx in credits)


def test_has_foreign_currency(result):
    foreign = [tx for tx in result.transactions if tx.original_currency == "USD"]
    assert len(foreign) >= 3


def test_has_installments(result):
    with_installment = [tx for tx in result.transactions if tx.installment]
    assert len(with_installment) >= 2


def test_has_fee(result):
    fees = [tx for tx in result.transactions if tx.tx_type == TransactionType.FEE]
    assert len(fees) >= 1


def test_has_tax(result):
    taxes = [tx for tx in result.transactions if tx.tx_type == TransactionType.TAX]
    assert len(taxes) >= 1


def test_has_interest(result):
    interest = [tx for tx in result.transactions if tx.tx_type == TransactionType.INTEREST]
    assert len(interest) >= 1


def test_has_multiple_cardholders(result):
    cardholders = {tx.cardholder for tx in result.transactions}
    assert len(cardholders) >= 2


def test_charges_are_positive(result):
    charges = [tx for tx in result.transactions if tx.tx_type == TransactionType.CHARGE]
    assert len(charges) > 0
    assert all(tx.amount > 0 for tx in charges)
