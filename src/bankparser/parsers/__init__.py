"""Parser registry — auto-detects which bank a PDF belongs to."""

from __future__ import annotations

from pathlib import Path

from bankparser.models import ParseResult
from bankparser.parsers.base import BaseParser


class ParserRegistry:
    """Registry of all available bank parsers.

    Usage:
        registry = ParserRegistry()
        registry.register(AmexParser())
        registry.register(BBVAParser())

        result = registry.parse("statement.pdf")  # auto-detect
        result = registry.parse("statement.pdf", bank="amex")  # explicit
    """

    def __init__(self) -> None:
        self._parsers: dict[str, BaseParser] = {}

    def register(self, parser: BaseParser) -> None:
        """Register a parser instance."""
        self._parsers[parser.bank_name] = parser

    def get_parser(self, bank_name: str) -> BaseParser | None:
        """Get a parser by bank name."""
        return self._parsers.get(bank_name)

    def detect_bank(self, pdf_path: Path) -> str | None:
        """Auto-detect which bank a PDF belongs to."""
        for name, parser in self._parsers.items():
            try:
                if parser.can_parse(pdf_path):
                    return name
            except Exception:
                continue
        return None

    def parse(self, pdf_path: str | Path, bank: str | None = None) -> ParseResult:
        """Parse a statement, auto-detecting the bank if not specified."""
        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file, got: {path.suffix}")

        if bank:
            parser = self.get_parser(bank)
            if parser is None:
                available = ", ".join(self._parsers.keys())
                raise ValueError(f"Unknown bank '{bank}'. Available: {available}")
        else:
            detected = self.detect_bank(path)
            if detected is None:
                available = ", ".join(self._parsers.keys())
                raise ValueError(
                    f"Could not detect bank for '{path.name}'. "
                    f"Specify --bank explicitly. Available: {available}"
                )
            parser = self._parsers[detected]

        return parser.parse(path)

    @property
    def available_banks(self) -> list[str]:
        return list(self._parsers.keys())


def create_default_registry() -> ParserRegistry:
    """Create a registry with all built-in parsers."""
    from bankparser.parsers.amex import AmexParser
    from bankparser.parsers.bbva import BBVAParser
    from bankparser.parsers.hsbc import HSBCParser

    registry = ParserRegistry()
    registry.register(AmexParser())
    registry.register(BBVAParser())
    registry.register(HSBCParser())
    return registry
