"""Core data models for bank statement parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    """Classification of a transaction."""
    CHARGE = "charge"
    PAYMENT = "payment"
    CREDIT = "credit"           # Refund / chargeback
    FEE = "fee"                 # Annual fee, late fee, etc.
    INTEREST = "interest"
    TAX = "tax"                 # IVA on fees/interest
    MSI = "msi"                 # Meses sin intereses installment
    MSI_ADJUSTMENT = "msi_adjustment"  # Deferred amount (MONTO A DIFERIR)
    TRANSFER = "transfer"


@dataclass
class Transaction:
    """A single transaction from a bank statement.

    This is the universal model that every parser produces
    and every exporter consumes.
    """
    date: date
    description: str
    amount: float                          # Positive = charge, negative = credit/payment
    currency: str = "MXN"
    bank: str = ""                         # amex, bbva, hsbc
    cardholder: str = ""
    tx_type: TransactionType = TransactionType.CHARGE
    category: str = ""                     # Auto-assigned or empty
    installment: str = ""                  # e.g. "03 DE 12"
    reference: str = ""                    # RFC / REF / authorization
    original_amount: Optional[float] = None   # Foreign currency original
    original_currency: Optional[str] = None   # e.g. "USD"
    exchange_rate: Optional[float] = None
    tags: list[str] = field(default_factory=list)

    @property
    def is_credit(self) -> bool:
        return self.amount < 0

    @property
    def is_foreign(self) -> bool:
        return self.original_currency is not None

    @property
    def abs_amount(self) -> float:
        return abs(self.amount)

    def to_dict(self) -> dict:
        """Convert to a flat dictionary for CSV export."""
        return {
            "date": self.date.isoformat(),
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "bank": self.bank,
            "cardholder": self.cardholder,
            "type": self.tx_type.value,
            "category": self.category,
            "installment": self.installment,
            "reference": self.reference,
            "original_amount": self.original_amount,
            "original_currency": self.original_currency or "",
            "exchange_rate": self.exchange_rate,
            "tags": "|".join(self.tags),
        }


@dataclass
class StatementInfo:
    """Metadata extracted from a bank statement."""
    bank: str = ""
    account_number: str = ""
    cardholder: str = ""
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    cut_date: Optional[date] = None
    previous_balance: float = 0.0
    payments_total: float = 0.0
    new_charges_total: float = 0.0
    current_balance: float = 0.0
    minimum_payment: float = 0.0
    credit_limit: float = 0.0
    annual_rate: float = 0.0


@dataclass
class ParseResult:
    """Complete result of parsing a statement file."""
    info: StatementInfo
    transactions: list[Transaction]
    warnings: list[str] = field(default_factory=list)

    @property
    def total_charges(self) -> float:
        return sum(tx.amount for tx in self.transactions if tx.amount > 0)

    @property
    def total_credits(self) -> float:
        return sum(tx.amount for tx in self.transactions if tx.amount < 0)

    @property
    def transaction_count(self) -> int:
        return len(self.transactions)
