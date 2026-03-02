"""Tests for the CLI interface."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from bankparser.cli import main
from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_parse_result():
    """A minimal ParseResult for mocking registry.parse()."""
    info = StatementInfo(bank="amex")
    txs = [
        Transaction(
            date=__import__("datetime").date(2026, 1, 15),
            description="OXXO TONALA",
            amount=48.50,
            bank="amex",
            tx_type=TransactionType.CHARGE,
        ),
        Transaction(
            date=__import__("datetime").date(2026, 1, 16),
            description="GRACIAS POR SU PAGO",
            amount=-10000.00,
            bank="amex",
            tx_type=TransactionType.PAYMENT,
        ),
        Transaction(
            date=__import__("datetime").date(2026, 1, 17),
            description="INTERÉS FINANCIERO",
            amount=500.00,
            bank="amex",
            tx_type=TransactionType.INTEREST,
        ),
        Transaction(
            date=__import__("datetime").date(2026, 1, 18),
            description="IVA APLICABLE",
            amount=80.00,
            bank="amex",
            tx_type=TransactionType.TAX,
        ),
        Transaction(
            date=__import__("datetime").date(2026, 1, 19),
            description="MACSTORE MSI",
            amount=1000.00,
            bank="amex",
            tx_type=TransactionType.MSI,
            installment="01 DE 12",
        ),
    ]
    return ParseResult(info=info, transactions=txs, warnings=["Test warning"])


class TestMainGroup:
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "bankparse" in result.output

    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Parse Mexican bank statement PDFs" in result.output


class TestParseCommand:
    def test_parse_file_not_found(self, runner, tmp_path):
        result = runner.invoke(main, ["parse", str(tmp_path / "nonexistent.pdf")])
        assert result.exit_code != 0

    def test_parse_non_pdf(self, runner, tmp_path):
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("hello")
        result = runner.invoke(main, ["parse", str(txt_file)])
        assert result.exit_code != 0

    def test_parse_success(self, runner, tmp_path, mock_parse_result):
        pdf = tmp_path / "statement.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.return_value = mock_parse_result
            mock_reg.return_value = mock_registry

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            out = tmp_path / "out.csv"
            result = runner.invoke(main, ["parse", str(pdf), "-o", str(out)])
            assert result.exit_code == 0
            assert out.exists()

    def test_parse_with_format(self, runner, tmp_path, mock_parse_result):
        pdf = tmp_path / "stmt.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.return_value = mock_parse_result
            mock_reg.return_value = mock_registry
            mock_get_db.return_value = MagicMock()

            out = tmp_path / "out.csv"
            result = runner.invoke(main, ["parse", str(pdf), "-f", "sure", "-o", str(out)])
            assert result.exit_code == 0
            assert out.exists()

    def test_parse_with_filters(self, runner, tmp_path, mock_parse_result):
        pdf = tmp_path / "stmt.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.return_value = mock_parse_result
            mock_reg.return_value = mock_registry
            mock_get_db.return_value = MagicMock()

            out = tmp_path / "out.csv"
            result = runner.invoke(main, ["parse", str(pdf), "--no-fees", "-o", str(out)])
            assert result.exit_code == 0

    def test_parse_charges_only(self, runner, tmp_path, mock_parse_result):
        pdf = tmp_path / "stmt.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.return_value = mock_parse_result
            mock_reg.return_value = mock_registry
            mock_get_db.return_value = MagicMock()

            out = tmp_path / "out.csv"
            result = runner.invoke(main, ["parse", str(pdf), "--charges-only", "-o", str(out)])
            assert result.exit_code == 0

    def test_parse_no_msi(self, runner, tmp_path, mock_parse_result):
        pdf = tmp_path / "stmt.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.return_value = mock_parse_result
            mock_reg.return_value = mock_registry
            mock_get_db.return_value = MagicMock()

            out = tmp_path / "out.csv"
            result = runner.invoke(main, ["parse", str(pdf), "--no-msi", "-o", str(out)])
            assert result.exit_code == 0

    def test_parse_cardholder_filter(self, runner, tmp_path, mock_parse_result):
        pdf = tmp_path / "stmt.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        # Give transactions a cardholder
        for tx in mock_parse_result.transactions:
            tx.cardholder = "JUAN GARCIA"

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.return_value = mock_parse_result
            mock_reg.return_value = mock_registry
            mock_get_db.return_value = MagicMock()

            out = tmp_path / "out.csv"
            result = runner.invoke(
                main, ["parse", str(pdf), "--cardholder", "JUAN", "-o", str(out)]
            )
            assert result.exit_code == 0

    def test_parse_error_in_parser(self, runner, tmp_path):
        pdf = tmp_path / "bad.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.side_effect = ValueError("Cannot detect bank")
            mock_reg.return_value = mock_registry
            mock_get_db.return_value = MagicMock()

            result = runner.invoke(main, ["parse", str(pdf)])
            assert result.exit_code != 0

    def test_parse_no_ask(self, runner, tmp_path, mock_parse_result):
        pdf = tmp_path / "stmt.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
            patch("bankparser.cli.prompt_categorize") as mock_prompt,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.return_value = mock_parse_result
            mock_reg.return_value = mock_registry
            mock_get_db.return_value = MagicMock()

            out = tmp_path / "out.csv"
            result = runner.invoke(main, ["parse", str(pdf), "--no-ask", "-o", str(out)])
            assert result.exit_code == 0
            mock_prompt.assert_not_called()

    def test_parse_multiple_files(self, runner, tmp_path, mock_parse_result):
        pdf1 = tmp_path / "a.pdf"
        pdf2 = tmp_path / "b.pdf"
        pdf1.write_bytes(b"%PDF-1.4 fake")
        pdf2.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("bankparser.cli.create_default_registry") as mock_reg,
            patch("bankparser.cli.get_db") as mock_get_db,
        ):
            mock_registry = MagicMock()
            mock_registry.parse.return_value = mock_parse_result
            mock_reg.return_value = mock_registry
            mock_get_db.return_value = MagicMock()

            out = tmp_path / "all.csv"
            result = runner.invoke(main, ["parse", str(pdf1), str(pdf2), "-o", str(out)])
            assert result.exit_code == 0
            assert out.exists()


class TestCategoriesCommands:
    def test_categories_list(self, runner, tmp_path):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.list_categories.return_value = [
                {"name": "Shopping", "parent_name": None, "icon": "🛍️"},
                {"name": "Food", "parent_name": None, "icon": "🍔"},
            ]
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["categories", "list"])
            assert result.exit_code == 0
            assert "Shopping" in result.output
            assert "2 categories total" in result.output

    def test_categories_add(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["categories", "add", "Pets", "--icon", "🐕"])
            assert result.exit_code == 0
            assert "Added category" in result.output
            mock_db.add_category.assert_called_once_with("Pets", None, "🐕")

    def test_categories_add_with_parent(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["categories", "add", "Fast Food", "--parent", "Food"])
            assert result.exit_code == 0
            mock_db.add_category.assert_called_once_with("Fast Food", "Food", "")

    def test_categories_add_error(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.add_category.side_effect = Exception("duplicate")
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["categories", "add", "Shopping"])
            assert "duplicate" in result.output

    def test_categories_remove(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["categories", "remove", "Pets", "--yes"])
            assert result.exit_code == 0
            assert "Removed category" in result.output


class TestRulesCommands:
    def test_rules_list(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.list_rules.return_value = [
                {
                    "id": 1,
                    "priority": 10,
                    "bank": "*",
                    "pattern": "OXXO",
                    "category_name": "Shopping",
                },
            ]
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["rules", "list"])
            assert result.exit_code == 0
            assert "OXXO" in result.output
            assert "1 rules total" in result.output

    def test_rules_list_by_bank(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.list_rules.return_value = []
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["rules", "list", "--bank", "bbva"])
            assert result.exit_code == 0
            mock_db.list_rules.assert_called_once_with("bbva")

    def test_rules_add(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["rules", "add", "COSTCO", "Groceries"])
            assert result.exit_code == 0
            assert "COSTCO" in result.output
            mock_db.add_rule.assert_called_once_with("COSTCO", "Groceries", "*", 10)

    def test_rules_add_with_options(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = runner.invoke(
                main,
                ["rules", "add", "VET", "Pets", "--bank", "amex", "--priority", "20"],
            )
            assert result.exit_code == 0
            mock_db.add_rule.assert_called_once_with("VET", "Pets", "amex", 20)

    def test_rules_remove(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["rules", "remove", "42"])
            assert result.exit_code == 0
            assert "Removed rule #42" in result.output
            mock_db.remove_rule.assert_called_once_with(42)


class TestInfoCommand:
    def test_info(self, runner):
        with patch("bankparser.cli.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.db_path = "/tmp/test.db"
            mock_db.category_count.return_value = 22
            mock_db.rule_count.return_value = 80
            mock_get_db.return_value = mock_db

            result = runner.invoke(main, ["info"])
            assert result.exit_code == 0
            assert "22" in result.output
            assert "80" in result.output
