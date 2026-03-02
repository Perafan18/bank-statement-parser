"""Integration tests for BBVAParser using generated PDF fixture."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from bankparser.models import TransactionType
from bankparser.parsers.bbva import BBVAParser

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pdfs" / "bbva_jan_2026.pdf"

pytestmark = pytest.mark.skipif(
    not FIXTURE.exists(), reason="BBVA PDF fixture not generated"
)


@pytest.fixture(scope="module")
def result():
    parser = BBVAParser()
    return parser.parse(FIXTURE)


def test_bank_is_bbva(result):
    assert result.info.bank == "bbva"


def test_account_number(result):
    assert result.info.account_number == "4152313800123456"


def test_period_dates(result):
    assert result.info.period_start == date(2026, 1, 8)
    assert result.info.period_end == date(2026, 2, 7)


def test_cut_date(result):
    assert result.info.cut_date == date(2026, 2, 7)


def test_cardholder(result):
    assert result.info.cardholder == "PEDRO MARTINEZ GONZALEZ"


def test_previous_balance(result):
    assert result.info.previous_balance == 45000.0


def test_transaction_count(result):
    assert len(result.transactions) == 58


def test_no_warnings(result):
    assert len(result.warnings) == 0


def test_has_payments(result):
    payments = [tx for tx in result.transactions if tx.tx_type == TransactionType.PAYMENT]
    assert len(payments) >= 5
    assert all(tx.amount < 0 for tx in payments)


def test_has_charges(result):
    charges = [tx for tx in result.transactions if tx.tx_type == TransactionType.CHARGE]
    assert len(charges) >= 30
    assert all(tx.amount > 0 for tx in charges)


def test_has_foreign_currency(result):
    foreign = [tx for tx in result.transactions if tx.original_currency == "USD"]
    assert len(foreign) >= 3


def test_has_msi(result):
    msi = [tx for tx in result.transactions if tx.tx_type == TransactionType.MSI]
    assert len(msi) >= 10


def test_has_msi_adjustments(result):
    adjustments = [
        tx for tx in result.transactions if tx.tx_type == TransactionType.MSI_ADJUSTMENT
    ]
    assert len(adjustments) >= 2


def test_has_fee(result):
    fees = [tx for tx in result.transactions if tx.tx_type == TransactionType.FEE]
    assert len(fees) >= 1


def test_has_tax(result):
    taxes = [tx for tx in result.transactions if tx.tx_type == TransactionType.TAX]
    assert len(taxes) >= 1


def test_has_interest(result):
    interest = [tx for tx in result.transactions if tx.tx_type == TransactionType.INTEREST]
    assert len(interest) >= 1


def test_charges_are_positive(result):
    charges = [tx for tx in result.transactions if tx.tx_type == TransactionType.CHARGE]
    assert len(charges) > 0
    assert all(tx.amount > 0 for tx in charges)
