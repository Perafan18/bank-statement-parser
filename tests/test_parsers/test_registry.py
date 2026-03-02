"""Tests for the ParserRegistry."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType
from bankparser.parsers import ParserRegistry, create_default_registry
from bankparser.parsers.base import BaseParser


class MockParser(BaseParser):
    """A minimal parser for testing the registry."""

    bank_name = "mockbank"

    def __init__(self, can_parse_result: bool = True):
        self._can_parse_result = can_parse_result

    def can_parse(self, pdf_path: Path) -> bool:
        return self._can_parse_result

    def parse(self, pdf_path: Path) -> ParseResult:
        return ParseResult(
            info=StatementInfo(bank=self.bank_name),
            transactions=[
                Transaction(
                    date=date(2026, 1, 1),
                    description="TEST TX",
                    amount=100.0,
                    bank=self.bank_name,
                    tx_type=TransactionType.CHARGE,
                ),
            ],
            warnings=[],
        )


class TestParserRegistry:
    @pytest.fixture
    def registry(self):
        return ParserRegistry()

    def test_register_and_get_parser(self, registry):
        parser = MockParser()
        registry.register(parser)
        assert registry.get_parser("mockbank") is parser

    def test_get_unknown_parser(self, registry):
        assert registry.get_parser("unknown") is None

    def test_available_banks(self, registry):
        registry.register(MockParser())
        assert "mockbank" in registry.available_banks

    def test_available_banks_empty(self, registry):
        assert registry.available_banks == []

    def test_detect_bank(self, registry, tmp_path):
        parser = MockParser(can_parse_result=True)
        registry.register(parser)

        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF fake")

        assert registry.detect_bank(pdf) == "mockbank"

    def test_detect_bank_none(self, registry, tmp_path):
        parser = MockParser(can_parse_result=False)
        registry.register(parser)

        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF fake")

        assert registry.detect_bank(pdf) is None

    def test_detect_bank_exception_skips(self, registry, tmp_path):
        """If can_parse raises, the parser is skipped."""
        parser = MagicMock(spec=BaseParser)
        parser.bank_name = "errbank"
        parser.can_parse.side_effect = RuntimeError("boom")
        registry.register(parser)

        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF fake")

        assert registry.detect_bank(pdf) is None

    def test_parse_auto_detect(self, registry, tmp_path):
        registry.register(MockParser(can_parse_result=True))

        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF fake")

        result = registry.parse(pdf)
        assert result.info.bank == "mockbank"
        assert result.transaction_count == 1

    def test_parse_explicit_bank(self, registry, tmp_path):
        registry.register(MockParser())

        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF fake")

        result = registry.parse(pdf, bank="mockbank")
        assert result.info.bank == "mockbank"

    def test_parse_unknown_bank_raises(self, registry, tmp_path):
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF fake")

        with pytest.raises(ValueError, match="Unknown bank"):
            registry.parse(pdf, bank="noexiste")

    def test_parse_undetectable_raises(self, registry, tmp_path):
        registry.register(MockParser(can_parse_result=False))

        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF fake")

        with pytest.raises(ValueError, match="Could not detect bank"):
            registry.parse(pdf)

    def test_parse_file_not_found(self, registry):
        with pytest.raises(FileNotFoundError):
            registry.parse("/nonexistent/file.pdf")

    def test_parse_not_pdf(self, registry, tmp_path):
        txt = tmp_path / "file.txt"
        txt.write_text("hello")
        with pytest.raises(ValueError, match="Expected a PDF"):
            registry.parse(txt)

    def test_parse_string_path(self, registry, tmp_path):
        registry.register(MockParser(can_parse_result=True))
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF fake")

        result = registry.parse(str(pdf))
        assert result.transaction_count == 1


class TestCreateDefaultRegistry:
    def test_creates_registry_with_all_banks(self):
        registry = create_default_registry()
        assert "amex" in registry.available_banks
        assert "bbva" in registry.available_banks
        assert "hsbc" in registry.available_banks
        assert len(registry.available_banks) == 3
