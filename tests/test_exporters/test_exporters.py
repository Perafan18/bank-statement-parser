"""Tests for CSV exporters."""

import csv
from pathlib import Path

import pytest

from bankparser.exporters import available_formats, get_exporter
from bankparser.exporters.generic import GenericExporter
from bankparser.exporters.sure import SureExporter
from bankparser.exporters.monarch import MonarchExporter


class TestExporterRegistry:
    def test_available_formats(self):
        formats = available_formats()
        assert "generic" in formats
        assert "sure" in formats
        assert "monarch" in formats

    def test_get_exporter(self):
        assert isinstance(get_exporter("generic"), GenericExporter)
        assert isinstance(get_exporter("sure"), SureExporter)

    def test_get_unknown_exporter(self):
        with pytest.raises(ValueError):
            get_exporter("nonexistent")


class TestGenericExporter:
    def test_headers(self):
        exp = GenericExporter()
        headers = exp.get_headers()
        assert "date" in headers
        assert "amount" in headers
        assert "description" in headers

    def test_export_creates_file(self, sample_transactions, tmp_path):
        exp = GenericExporter()
        output = tmp_path / "test.csv"
        exp.export(sample_transactions, output)

        assert output.exists()
        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 7

    def test_export_amounts_correct(self, sample_transactions, tmp_path):
        exp = GenericExporter()
        output = tmp_path / "test.csv"
        exp.export(sample_transactions, output)

        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Payment should be negative
            payment_row = [r for r in rows if "PAGO" in r["description"]][0]
            assert float(payment_row["amount"]) < 0


class TestSureExporter:
    def test_headers(self):
        exp = SureExporter()
        assert "name" in exp.get_headers()
        assert "account" in exp.get_headers()

    def test_foreign_in_notes(self, sample_transactions, tmp_path):
        exp = SureExporter()
        output = tmp_path / "sure.csv"
        exp.export(sample_transactions, output)

        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            do_row = [r for r in rows if "DIGITALOCEAN" in r["name"]][0]
            assert "USD" in do_row["notes"]
            assert "35.45" in do_row["notes"]

    def test_installment_in_tags(self, sample_transactions, tmp_path):
        exp = SureExporter()
        output = tmp_path / "sure.csv"
        exp.export(sample_transactions, output)

        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            mac_row = [r for r in rows if "Macstore" in r["name"]][0]
            assert "msi:" in mac_row["tags"]


class TestMonarchExporter:
    def test_headers(self):
        exp = MonarchExporter()
        assert "Merchant" in exp.get_headers()
        assert "Original Currency" in exp.get_headers()

    def test_export(self, sample_transactions, tmp_path):
        exp = MonarchExporter()
        output = tmp_path / "monarch.csv"
        exp.export(sample_transactions, output)

        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 7

    def test_tags_column_uses_tags_not_cardholder(self, tmp_path):
        """Tags column should contain tx.tags, not tx.cardholder."""
        from bankparser.models import Transaction, TransactionType
        from datetime import date

        txs = [
            Transaction(
                date=date(2026, 1, 15),
                description="TEST MERCHANT",
                amount=100.00,
                bank="bbva",
                cardholder="JUAN GARCIA",
                tags=["msi:03/12", "foreign"],
            ),
        ]
        exp = MonarchExporter()
        output = tmp_path / "monarch_tags.csv"
        exp.export(txs, output)

        with open(output) as f:
            reader = csv.DictReader(f)
            row = list(reader)[0]
            assert row["Tags"] == "msi:03/12, foreign"
            assert "JUAN GARCIA" not in row["Tags"]
