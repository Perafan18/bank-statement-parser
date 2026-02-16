"""Sure / Maybe Finance compatible CSV exporter."""

from bankparser.exporters.base import BaseExporter
from bankparser.models import Transaction


class SureExporter(BaseExporter):
    format_name = "sure"
    description = "Sure / Maybe Finance import format"

    def get_headers(self) -> list[str]:
        return ["date", "name", "amount", "currency", "category", "tags", "account", "notes"]

    def format_row(self, tx: Transaction) -> list[str]:
        # Build tags
        tags = list(tx.tags)
        if tx.installment:
            tags.append(f"msi:{tx.installment.replace(' ', '')}")
        if tx.is_foreign:
            tags.append("foreign")

        # Build notes
        notes_parts = []
        if tx.original_amount and tx.original_currency and tx.exchange_rate:
            notes_parts.append(
                f"{tx.original_currency} {tx.original_amount:.2f} @ {tx.exchange_rate:.5f}"
            )
        if tx.installment:
            notes_parts.append(f"Cargo {tx.installment}")

        # Account name
        bank_label = tx.bank.upper() if tx.bank else "Card"
        account = f"{bank_label} - {tx.cardholder}" if tx.cardholder else bank_label

        return [
            tx.date.isoformat(),
            tx.description,
            f"{tx.amount:.2f}",
            tx.currency,
            tx.category,
            "|".join(tags),
            account,
            "; ".join(notes_parts),
        ]
