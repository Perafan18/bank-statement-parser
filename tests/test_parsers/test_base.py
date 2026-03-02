"""Tests for BaseParser helper methods (extract_text_from_pdf, etc.)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from bankparser.parsers.base import BaseParser


class TestExtractTextFromPdf:
    def test_extracts_all_pages(self):
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 text"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = BaseParser.extract_text_from_pdf(Path("test.pdf"))

        assert result == ["Page 1 text", "Page 2 text"]

    def test_none_text_becomes_empty_string(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = BaseParser.extract_text_from_pdf(Path("test.pdf"))

        assert result == [""]

    def test_empty_pdf(self):
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = BaseParser.extract_text_from_pdf(Path("test.pdf"))

        assert result == []


class TestExtractFirstPageText:
    def test_returns_first_page(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "First page"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = BaseParser.extract_first_page_text(Path("test.pdf"))

        assert result == "First page"

    def test_empty_pdf_returns_empty(self):
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = BaseParser.extract_first_page_text(Path("test.pdf"))

        assert result == ""

    def test_none_text_returns_empty(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = BaseParser.extract_first_page_text(Path("test.pdf"))

        assert result == ""


class TestExtractTextWithOcr:
    def test_ocr_extraction(self):
        mock_img1 = MagicMock()
        mock_img2 = MagicMock()

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.side_effect = ["OCR page 1", "OCR page 2"]

        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path.return_value = [mock_img1, mock_img2]

        import sys

        with (
            patch.dict(sys.modules, {"pytesseract": mock_pytesseract, "pdf2image": mock_pdf2image}),
        ):
            result = BaseParser.extract_text_with_ocr(Path("test.pdf"))

        assert result == ["OCR page 1", "OCR page 2"]
