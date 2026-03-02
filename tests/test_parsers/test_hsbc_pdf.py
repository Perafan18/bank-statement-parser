"""Integration tests for HSBCParser using generated PDF fixture (OCR-based)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from bankparser.models import TransactionType
from bankparser.parsers.hsbc import HSBCParser

FIXTURE = Path(__file__).parent.parent / "fixtures" / "pdfs" / "hsbc_jan_2026.pdf"

# Skip the entire module if the PDF fixture is missing or OCR deps are unavailable.
_ocr_available = True
try:
    import pdf2image  # noqa: F401
    import pytesseract  # noqa: F401
except ImportError:
    _ocr_available = False

pytestmark = [
    pytest.mark.skipif(not FIXTURE.exists(), reason="HSBC PDF fixture not generated"),
    pytest.mark.skipif(not _ocr_available, reason="OCR deps (pytesseract/pdf2image) not available"),
]


@pytest.fixture(scope="module")
def result():
    parser = HSBCParser()
    return parser.parse(FIXTURE)


@pytest.fixture(scope="module")
def fixture_path():
    return FIXTURE


def test_bank_is_hsbc(result):
    assert result.info.bank == "hsbc"


def test_account_number(result):
    assert result.info.account_number == "4524123456789012"


def test_period_dates(result):
    assert result.info.period_start == date(2025, 12, 15)
    assert result.info.period_end == date(2026, 1, 12)


def test_cut_date(result):
    assert result.info.cut_date == date(2026, 1, 12)


def test_previous_balance(result):
    assert result.info.previous_balance == 29093.55


def test_transaction_count(result):
    assert len(result.transactions) == 46


def test_no_warnings(result):
    assert len(result.warnings) == 0


def test_has_payments(result):
    payments = [tx for tx in result.transactions if tx.tx_type == TransactionType.PAYMENT]
    assert len(payments) >= 3
    assert all(tx.amount < 0 for tx in payments)


def test_has_charges(result):
    charges = [tx for tx in result.transactions if tx.tx_type == TransactionType.CHARGE]
    assert len(charges) >= 30
    assert all(tx.amount > 0 for tx in charges)


def test_has_credits(result):
    credits = [tx for tx in result.transactions if tx.tx_type == TransactionType.CREDIT]
    assert len(credits) >= 2


def test_has_fee(result):
    fees = [tx for tx in result.transactions if tx.tx_type == TransactionType.FEE]
    assert len(fees) >= 1


def test_has_interest(result):
    interest = [tx for tx in result.transactions if tx.tx_type == TransactionType.INTEREST]
    assert len(interest) >= 1


def test_charges_are_positive(result):
    charges = [tx for tx in result.transactions if tx.tx_type == TransactionType.CHARGE]
    assert len(charges) > 0
    assert all(tx.amount > 0 for tx in charges)


def test_uses_ocr():
    """Verify the PDF is image-based (no extractable text)."""
    import pdfplumber

    with pdfplumber.open(FIXTURE) as pdf:
        text = "".join(p.extract_text() or "" for p in pdf.pages)
    assert text.strip() == "", "PDF should be image-based with no extractable text"
