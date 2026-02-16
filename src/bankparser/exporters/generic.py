"""Generic CSV exporter with all available fields."""

from bankparser.exporters.base import BaseExporter
from bankparser.models import Transaction


class GenericExporter(BaseExporter):
    format_name = "generic"
    description = "All fields, maximum detail"

    def get_headers(self) -> list[str]:
        return [
            "date", "description", "amount", "currency", "bank", "cardholder",
            "type", "category", "installment", "reference",
            "original_amount", "original_currency", "exchange_rate", "tags",
        ]

    def format_row(self, tx: Transaction) -> list[str]:
        return [
            tx.date.isoformat(),
            tx.description,
            f"{tx.amount:.2f}",
            tx.currency,
            tx.bank,
            tx.cardholder,
            tx.tx_type.value,
            tx.category,
            tx.installment,
            tx.reference,
            f"{tx.original_amount:.2f}" if tx.original_amount else "",
            tx.original_currency or "",
            f"{tx.exchange_rate:.5f}" if tx.exchange_rate else "",
            "|".join(tx.tags),
        ]
