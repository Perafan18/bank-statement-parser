"""Base class for CSV exporters."""

from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from pathlib import Path

from bankparser.models import Transaction


class BaseExporter(ABC):
    """Abstract base class for CSV exporters."""

    format_name: str = ""
    description: str = ""

    @abstractmethod
    def get_headers(self) -> list[str]:
        """Return CSV column headers."""
        ...

    @abstractmethod
    def format_row(self, tx: Transaction) -> list[str]:
        """Format a single transaction as a CSV row."""
        ...

    def export(self, transactions: list[Transaction], output_path: str | Path) -> None:
        """Export transactions to a CSV file."""
        path = Path(output_path)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.get_headers())
            for tx in transactions:
                writer.writerow(self.format_row(tx))
