"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import date

import pytest

from bankparser.database import Database
from bankparser.models import Transaction, TransactionType


@pytest.fixture
def tmp_db(tmp_path) -> Database:
    """Provide a temporary database for testing."""
    db = Database(db_path=tmp_path / "test.db")
    db.initialize()
    yield db
    db.close()


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    """A set of sample transactions for testing exporters and categorizer."""
    return [
        Transaction(
            date=date(2026, 1, 15),
            description="GRACIAS POR SU PAGO EN LINEA",
            amount=-10000.00,
            bank="amex",
            cardholder="JUAN GARCIA",
            tx_type=TransactionType.PAYMENT,
        ),
        Transaction(
            date=date(2026, 1, 16),
            description="AMAZON MX MARKETPLACE*A MEXICO CITY",
            amount=499.00,
            bank="amex",
            cardholder="JUAN GARCIA",
            tx_type=TransactionType.CHARGE,
            reference="RFCANE140618P37 /REFabc123",
        ),
        Transaction(
            date=date(2026, 1, 17),
            description="REST KIMODO GUADALAJARA",
            amount=1610.00,
            bank="amex",
            cardholder="JUAN GARCIA",
            tx_type=TransactionType.CHARGE,
        ),
        Transaction(
            date=date(2026, 1, 18),
            description="DIGITALOCEAN.COM BROOMFIELD",
            amount=629.79,
            bank="amex",
            cardholder="JUAN GARCIA",
            tx_type=TransactionType.CHARGE,
            original_amount=35.45,
            original_currency="USD",
            exchange_rate=17.76559,
        ),
        Transaction(
            date=date(2026, 1, 20),
            description="Macstore Web MSI Mexico",
            amount=4749.84,
            bank="amex",
            tx_type=TransactionType.CHARGE,
            installment="03 DE 12",
        ),
        Transaction(
            date=date(2026, 2, 8),
            description="INTERÉS FINANCIERO",
            amount=5355.07,
            bank="amex",
            tx_type=TransactionType.INTEREST,
        ),
        Transaction(
            date=date(2026, 2, 8),
            description="IVA APLICABLE",
            amount=197.33,
            bank="amex",
            tx_type=TransactionType.TAX,
        ),
    ]
