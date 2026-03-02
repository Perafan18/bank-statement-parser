"""Transaction categorizer backed by SQLite rules."""

from __future__ import annotations

from bankparser.database import Database
from bankparser.models import Transaction, TransactionType

# Map transaction types to forced categories (these override rules)
TYPE_CATEGORY_MAP = {
    TransactionType.PAYMENT: "Payment",
    TransactionType.INTEREST: "Interest",
    TransactionType.FEE: "Fees",
    TransactionType.TAX: "Tax",
    TransactionType.MSI: "MSI Installment",
    TransactionType.MSI_ADJUSTMENT: "MSI Adjustment",
}


class Categorizer:
    """Assigns categories to transactions using SQLite-backed rules."""

    def __init__(self, db: Database):
        self.db = db

    def categorize(self, transaction: Transaction) -> str:
        """Determine the category for a single transaction.

        Priority:
        1. Forced category from transaction type (payments, fees, etc.)
        2. SQLite rule matching (pattern on description, bank-specific)
        3. Fallback to 'Uncategorized'
        """
        # 1. Type-based override
        forced = TYPE_CATEGORY_MAP.get(transaction.tx_type)
        if forced:
            return forced

        # 2. Rule-based matching
        return self.db.match_category(transaction.description, transaction.bank)

    def categorize_all(self, transactions: list[Transaction]) -> list[Transaction]:
        """Categorize all transactions in-place and return them."""
        for tx in transactions:
            tx.category = self.categorize(tx)
        return transactions

    def collect_uncategorized(
        self, transactions: list[Transaction]
    ) -> dict[str, list[Transaction]]:
        """Group uncategorized transactions by description."""
        groups: dict[str, list[Transaction]] = {}
        for tx in transactions:
            if tx.category == "Uncategorized":
                groups.setdefault(tx.description, []).append(tx)
        return groups

    def recategorize_uncategorized(self, transactions: list[Transaction]) -> None:
        """Re-categorize only transactions still marked 'Uncategorized'."""
        for tx in transactions:
            if tx.category == "Uncategorized":
                tx.category = self.categorize(tx)
