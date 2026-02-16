"""Base class for all bank statement parsers."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path

from bankparser.models import ParseResult, StatementInfo, Transaction


# Spanish month name → month number
MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


class BaseParser(ABC):
    """Abstract base class for bank statement parsers.

    Every parser must:
    - Set `bank_name` (e.g. "amex", "bbva", "hsbc")
    - Implement `parse()` which returns a `ParseResult`
    - Implement `can_parse()` which detects if a PDF belongs to this bank
    """

    bank_name: str = ""

    @abstractmethod
    def parse(self, pdf_path: Path) -> ParseResult:
        """Parse a PDF statement and return structured data."""
        ...

    @abstractmethod
    def can_parse(self, pdf_path: Path) -> bool:
        """Check if this parser can handle the given PDF.

        Typically checks the first page for bank-specific identifiers.
        """
        ...

    # ── Helpers available to all parsers ──────────────────────────────────────

    @staticmethod
    def parse_spanish_date(day: int, month_name: str, year: int) -> date:
        """Convert a Spanish date (e.g. 15, 'Enero', 2026) to a date object."""
        month_name_clean = month_name.lower().strip()
        month = MONTHS_ES.get(month_name_clean)
        if month is None:
            raise ValueError(f"Unknown Spanish month: '{month_name}'")
        return date(year, month, day)

    @staticmethod
    def parse_mx_amount(amount_str: str) -> float:
        """Parse a Mexican-format amount string (e.g. '1,234.56') to float."""
        cleaned = amount_str.replace(',', '').replace('$', '').strip()
        return float(cleaned)

    @staticmethod
    def extract_text_from_pdf(pdf_path: Path) -> list[str]:
        """Extract text from all pages of a PDF, returning a list of page texts."""
        import pdfplumber

        pages = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)
        return pages

    @staticmethod
    def extract_first_page_text(pdf_path: Path) -> str:
        """Extract text from just the first page (for detection)."""
        import pdfplumber

        with pdfplumber.open(str(pdf_path)) as pdf:
            if pdf.pages:
                return pdf.pages[0].extract_text() or ""
        return ""

    @staticmethod
    def extract_text_with_ocr(
        pdf_path: Path, dpi: int = 300, psm: int = 6,
    ) -> list[str]:
        """Extract text from a PDF using OCR (pytesseract + pdf2image).

        Use this when pdfplumber cannot decode the PDF fonts (e.g. CID-encoded).
        Requires system packages: tesseract-ocr, tesseract-ocr-spa, poppler-utils.

        Args:
            pdf_path: Path to the PDF file.
            dpi: Resolution for PDF-to-image conversion.
            psm: Tesseract page segmentation mode (6 = uniform block, best
                 for tabular bank statements).
        """
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(str(pdf_path), dpi=dpi)
        pages = []
        for img in images:
            text = pytesseract.image_to_string(
                img, lang="spa", config=f"--psm {psm}",
            )
            pages.append(text)
        return pages
