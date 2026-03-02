"""Monarch Money compatible CSV exporter."""

from bankparser.exporters.base import BaseExporter
from bankparser.models import Transaction


class MonarchExporter(BaseExporter):
    format_name = "monarch"
    description = "Monarch Money import format"

    def get_headers(self) -> list[str]:
        return [
            "Date",
            "Merchant",
            "Amount",
            "Category",
            "Account",
            "Tags",
            "Notes",
            "Original Currency",
        ]

    def format_row(self, tx: Transaction) -> list[str]:
        bank_label = tx.bank.upper() if tx.bank else "Card"

        return [
            tx.date.isoformat(),
            tx.description,
            f"{tx.amount:.2f}",
            tx.category,
            bank_label,
            ", ".join(tx.tags) if tx.tags else "",
            f"{tx.original_currency} {tx.original_amount:.2f}" if tx.original_amount else "",
            tx.original_currency or tx.currency,
        ]
