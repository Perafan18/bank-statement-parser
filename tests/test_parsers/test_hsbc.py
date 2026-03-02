"""Tests for the HSBC Mexico TDC (credit card) parser.

These tests validate info extraction, date parsing, OCR cleanup,
and transaction parsing against text that mimics OCR output from
a real HSBC TDC PDF statement (with anonymized data).
"""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from bankparser.models import TransactionType
from bankparser.parsers.hsbc import HSBCParser

# ── Info extraction fixture ──────────────────────────────────────────────────

HSBC_INFO_TEXT = """\
TU PAGO REQUERIDO ESTE PERIODO
JUAN GARCIA LOPEZ
€ MISION DE SAN CARLOS 8 3 a) Periodo: 15-Dic-2025 al 12-Ene-2026
COL CENTRO HISTORICO
45000 GUADALAJARA, JAL b) Fecha de corte: 12-Ene-2026
HSBC Zero Categoría: Clásica
NUMERO DE CUENTA: 4524 1234 5678 9012 INTERESES: ? $ 15,646.17
RFC: XAXX010101000 f) Pago mínimo + compras y $ 525.00
NÚMERO DE CUENTA CLABE: 021975212000000000 cargos diferidos a meses: *
a) Adeudo del periodo anterior |= $19,810.48 AU de intereses pagados"""


class TestHSBCParser:
    @pytest.fixture
    def parser(self):
        return HSBCParser()

    def test_bank_name(self, parser):
        assert parser.bank_name == "hsbc"

    def test_parse_hsbc_date(self, parser):
        assert parser._parse_hsbc_date("15-Dic-2025") == date(2025, 12, 15)
        assert parser._parse_hsbc_date("12-Ene-2026") == date(2026, 1, 12)

    def test_parse_hsbc_date_ocr_fix(self, parser):
        """OCR may produce O instead of 0 in day/year positions."""
        assert parser._parse_hsbc_date("O5-Feb-2026") == date(2026, 2, 5)

    def test_parse_hsbc_date_invalid(self, parser):
        with pytest.raises(ValueError):
            parser._parse_hsbc_date("invalid")

    def test_extract_info_period(self, parser):
        info = parser._extract_info(HSBC_INFO_TEXT)
        assert info.period_start == date(2025, 12, 15)
        assert info.period_end == date(2026, 1, 12)

    def test_extract_info_account(self, parser):
        info = parser._extract_info(HSBC_INFO_TEXT)
        assert info.account_number == "4524123456789012"

    def test_extract_info_cardholder(self, parser):
        info = parser._extract_info(HSBC_INFO_TEXT)
        assert info.cardholder == "JUAN GARCIA LOPEZ"

    def test_extract_info_cut_date(self, parser):
        info = parser._extract_info(HSBC_INFO_TEXT)
        assert info.cut_date == date(2026, 1, 12)

    def test_extract_info_previous_balance(self, parser):
        info = parser._extract_info(HSBC_INFO_TEXT)
        assert info.previous_balance == 19810.48

    def test_classify_payment(self, parser):
        assert parser._classify("SUPAGO GRACIAS", True) == TransactionType.PAYMENT

    def test_classify_charge(self, parser):
        assert parser._classify("TIENDA ONLINE MEX", False) == TransactionType.CHARGE

    def test_classify_fee(self, parser):
        assert parser._classify("COMISION POR SERVICIO", False) == TransactionType.FEE
        assert parser._classify("ANUALIDAD TARJETA", False) == TransactionType.FEE

    def test_classify_interest(self, parser):
        assert parser._classify("INTERESES DEL PERIODO", False) == TransactionType.INTEREST

    def test_classify_credit(self, parser):
        """Non-keyword credit should be classified as CREDIT."""
        assert parser._classify("TIENDA ONLINE MEX", True) == TransactionType.CREDIT

    def test_classify_merpago_not_payment(self, parser):
        """MERPAGO contains 'PAGO' but should NOT be classified as PAYMENT."""
        assert parser._classify("MERPAGO*TIENDA", False) == TransactionType.CHARGE


# ── OCR cleanup tests ────────────────────────────────────────────────────────


class TestHSBCOCRCleanup:
    @pytest.fixture
    def parser(self):
        return HSBCParser()

    def test_clean_description_leading_pipe(self, parser):
        assert parser._clean_description("|TIENDA ONLINE MEX") == "TIENDA ONLINE MEX"

    def test_clean_description_leading_underscore_pipe(self, parser):
        assert parser._clean_description("_ |TIENDA ONLINE MEX") == "TIENDA ONLINE MEX"

    def test_clean_description_trailing_underscore(self, parser):
        assert parser._clean_description("TIENDA_MEX__") == "TIENDA_MEX"

    def test_clean_description_underscore_before_space(self, parser):
        """OCR table border: 'RAPPI_ CIU' → 'RAPPI CIU'."""
        assert parser._clean_description("DLOCAL*REST RAPPI_ CIU") == "DLOCAL*REST RAPPI CIU"

    def test_clean_description_underscore_after_space(self, parser):
        """OCR table border: 'ISIDRO _ZAP' → 'ISIDRO ZAP'."""
        assert (
            parser._clean_description("COSTCO GDL SAN ISIDRO _ZAP") == "COSTCO GDL SAN ISIDRO ZAP"
        )

    def test_clean_description_internal_underscore_preserved(self, parser):
        """Internal underscores like TIENDA_MEX should not be removed."""
        assert parser._clean_description("TIENDA_MEX ONLINE") == "TIENDA_MEX ONLINE"

    def test_clean_description_collapse_spaces(self, parser):
        assert parser._clean_description("TIENDA   ONLINE   MEX") == "TIENDA ONLINE MEX"

    def test_fix_ocr_digits(self, parser):
        assert parser._fix_ocr_digits("O5-Feb-2O26") == "05-Feb-2026"
        assert parser._fix_ocr_digits("OSAKA JP") == "OSAKA JP"  # O not adjacent to digit


# ── Transaction section fixture ──────────────────────────────────────────────

HSBC_SECTION_TEXT = """\
DESGLOSE DE MOVIMIENTOS
c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
Tarjeta titular 4524123456789012

i. Fecha de la
operación

17-Dic-2025 17-Dic-2025 _|SUPAGO GRACIAS || $19,810.48
29-Dic-2025 31-Dic-2025 _ |ABC 910715UB9 SUPERMERCADO CENTRO _GDL $714.00

c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
Tarjeta adicional 4524123400001111

12-Dic-2025 15-Dic-2025 _ |TRA 150604TW1 TIENDA ONLINE_ MEX 1+1$510.10
13-Dic-2025 15-Dic-2025 XYZ 200220LK5 SERVICIO DELIVERY MEX $840.08
17-Dic-2025 17-Dic-2025 DEF 2105031W3 MERPAGO*TIENDA MEX $292.78
23-Dic-2025 24-Dic-2025 _ |TRA 150604TW1 TIENDA ONLINE_ MEX |-] $30.00
09-Ene-2026 12-Ene-2026 _|PQR 980114PI2 SERVICIO AUTO MEX $304.00

Total cargos |+|$15,676.17
Total abonos |- | $19,840.48"""


class TestHSBCTransactionSection:
    """Tests for parsing the CARGOS, ABONOS Y COMPRAS REGULARES section."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    @pytest.fixture
    def transactions(self, parser):
        lines = HSBC_SECTION_TEXT.split("\n")
        warnings: list[str] = []
        return parser._parse_transactions(lines, warnings)

    def test_parse_section_count(self, transactions):
        """Should parse 7 transactions from both cardholder sections."""
        assert len(transactions) == 7

    def test_parse_payment(self, transactions):
        """SUPAGO GRACIAS should be a PAYMENT with negative amount."""
        supago = [tx for tx in transactions if "SUPAGO" in tx.description][0]
        assert supago.amount == -19810.48
        assert supago.tx_type == TransactionType.PAYMENT

    def test_parse_charge(self, transactions):
        """Regular charge should have positive amount."""
        abc = [tx for tx in transactions if "SUPERMERCADO" in tx.description][0]
        assert abc.amount == 714.00
        assert abc.tx_type == TransactionType.CHARGE
        assert abc.date == date(2025, 12, 29)

    def test_parse_charge_with_plus_indicator(self, transactions):
        """Charge with 1+1$ OCR artifact should have correct amount."""
        tienda = [tx for tx in transactions if "TIENDA ONLINE" in tx.description and tx.amount > 0][
            0
        ]
        assert tienda.amount == 510.10
        assert tienda.tx_type == TransactionType.CHARGE

    def test_parse_credit_with_minus_indicator(self, transactions):
        """Transaction with |-] indicator should be negative (credit)."""
        credit = [tx for tx in transactions if tx.amount == -30.00][0]
        assert credit.tx_type == TransactionType.CREDIT
        assert credit.amount == -30.00

    def test_parse_merpago_as_charge(self, transactions):
        """MERPAGO*TIENDA should be CHARGE, not PAYMENT."""
        mp = [tx for tx in transactions if "MERPAGO" in tx.description][0]
        assert mp.tx_type == TransactionType.CHARGE
        assert mp.amount == 292.78

    def test_descriptions_cleaned(self, transactions):
        """OCR artifacts should be removed from descriptions."""
        for tx in transactions:
            assert not tx.description.startswith("|")
            assert not tx.description.startswith("_")


# ── Foreign currency fixture ─────────────────────────────────────────────────

HSBC_FOREIGN_TEXT = """\
c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
Tarjeta adicional 4524123400001111

09-Ene-2026 12-Ene-2026 _|PQR 980114PI2 SERVICIO AUTO MEX $304.00

APPSTORE DIGITAL TOKYO JP
12-Ene-2026 12-Ene-2026 MONEDA EXTRANJERA: 9.98 USD TC: 17.99699 DEL 12 DE ENERO + $179.51

Total cargos |+|$483.51"""


class TestHSBCForeignCurrency:
    """Tests for parsing MONEDA EXTRANJERA (foreign currency) transactions."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    @pytest.fixture
    def transactions(self, parser):
        lines = HSBC_FOREIGN_TEXT.split("\n")
        warnings: list[str] = []
        return parser._parse_transactions(lines, warnings)

    def test_foreign_tx_count(self, transactions):
        """Should parse 2 transactions: 1 regular + 1 foreign."""
        assert len(transactions) == 2

    def test_foreign_tx_description(self, transactions):
        """Foreign transaction should use pending description from previous line."""
        foreign = [tx for tx in transactions if tx.original_currency][0]
        assert foreign.description == "APPSTORE DIGITAL TOKYO JP"

    def test_foreign_tx_currency_info(self, transactions):
        """Foreign transaction should have original amount, currency, and exchange rate."""
        foreign = [tx for tx in transactions if tx.original_currency][0]
        assert foreign.original_amount == 9.98
        assert foreign.original_currency == "USD"
        assert foreign.exchange_rate == 17.99699

    def test_foreign_tx_mxn_amount(self, transactions):
        """Foreign transaction should have correct MXN amount."""
        foreign = [tx for tx in transactions if tx.original_currency][0]
        assert foreign.amount == 179.51

    def test_foreign_tx_date(self, transactions):
        """Foreign transaction should have the correct date."""
        foreign = [tx for tx in transactions if tx.original_currency][0]
        assert foreign.date == date(2026, 1, 12)


# ── Foreign currency OCR sanity check ────────────────────────────────────────

HSBC_FOREIGN_GARBLED_TEXT = """\
c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
Tarjeta adicional 4524123400001111

APPSTORE DIGITAL TOKYO JP
12-Ene-2026 12-Ene-2026 MONEDA EXTRANJERA: 9.98 USD TC: 17.99699 DEL 12 DE ENERO + [5179.51

Total cargos |+|$179.61"""


class TestHSBCForeignGarbled:
    """Tests for OCR-garbled foreign currency amounts."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    @pytest.fixture
    def transactions(self, parser):
        lines = HSBC_FOREIGN_GARBLED_TEXT.split("\n")
        warnings: list[str] = []
        return parser._parse_transactions(lines, warnings)

    def test_garbled_amount_uses_calculated(self, transactions):
        """When OCR garbles $179.51 into [5179.51, use calculated value."""
        foreign = [tx for tx in transactions if tx.original_currency][0]
        # 9.98 * 17.99699 ≈ 179.61
        expected = round(9.98 * 17.99699, 2)
        assert foreign.amount == expected


# ── OCR date fix in transactions ─────────────────────────────────────────────

HSBC_OCR_DATE_FIX_TEXT = """\
c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
Tarjeta titular 4524123456789012

O2-Ene-2026 O5-Ene-2026 _ |XYZ 200220LK5 SERVICIO DELIVERY MEX $558.03

Total cargos |+|$558.03"""


class TestHSBCOCRDateFix:
    """Tests for OCR digit fix in date positions."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    @pytest.fixture
    def transactions(self, parser):
        lines = HSBC_OCR_DATE_FIX_TEXT.split("\n")
        warnings: list[str] = []
        return parser._parse_transactions(lines, warnings)

    def test_ocr_o_to_zero_in_dates(self, transactions):
        """O in date position should be treated as 0."""
        assert len(transactions) == 1
        assert transactions[0].date == date(2026, 1, 2)
        assert transactions[0].amount == 558.03


class TestHSBCOCRDependency:
    """Tests for OCR dependency guard."""

    def test_parse_raises_without_ocr(self, monkeypatch):
        """parse() should raise RuntimeError if OCR deps are missing."""
        import bankparser.parsers.hsbc as hsbc_mod

        monkeypatch.setattr(hsbc_mod, "_OCR_AVAILABLE", False)
        parser = HSBCParser()
        with pytest.raises(RuntimeError, match="pip install"):
            parser.parse(Path("/fake/file.pdf"))

    def test_can_parse_returns_false_without_ocr(self, monkeypatch, tmp_path):
        """can_parse() should return False gracefully if OCR deps are missing."""
        import bankparser.parsers.hsbc as hsbc_mod

        monkeypatch.setattr(hsbc_mod, "_OCR_AVAILABLE", False)
        # Create a dummy PDF that pdfplumber can't identify as HSBC
        dummy = tmp_path / "test.pdf"
        dummy.write_bytes(b"%PDF-1.4 fake")
        parser = HSBCParser()
        # Should not raise, just return False
        assert parser.can_parse(dummy) is False


class TestHSBCCanParse:
    """Tests for can_parse() with pdfplumber detection."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    def test_can_parse_hsbc_text(self, parser):
        with patch.object(parser, "extract_first_page_text", return_value="HSBC Mexico"):
            assert parser.can_parse(Path("test.pdf")) is True

    def test_can_parse_non_hsbc(self, parser):
        with patch.object(parser, "extract_first_page_text", return_value="BBVA Mexico"):
            assert parser.can_parse(Path("test.pdf")) is False

    def test_can_parse_ocr_fallback(self, parser, monkeypatch):
        """When pdfplumber fails, fall back to OCR if available."""
        import bankparser.parsers.hsbc as hsbc_mod

        monkeypatch.setattr(hsbc_mod, "_OCR_AVAILABLE", True)
        with (
            patch.object(parser, "extract_first_page_text", return_value="garbled cid text"),
            patch.object(parser, "extract_text_with_ocr", return_value=["HSBC Mexico"]),
        ):
            assert parser.can_parse(Path("test.pdf")) is True


class TestHSBCParseIntegration:
    """Tests for parse() with mocked OCR output."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    def test_parse_with_mock_ocr(self, parser, monkeypatch):
        import bankparser.parsers.hsbc as hsbc_mod

        monkeypatch.setattr(hsbc_mod, "_OCR_AVAILABLE", True)

        ocr_pages = [HSBC_INFO_TEXT, HSBC_SECTION_TEXT]
        with patch.object(parser, "extract_text_with_ocr", return_value=ocr_pages):
            result = parser.parse(Path("test.pdf"))

        assert result.info.bank == "hsbc"
        assert result.info.cardholder == "JUAN GARCIA LOPEZ"
        assert result.transaction_count >= 5
        # Cardholder should be propagated
        for tx in result.transactions:
            assert tx.cardholder == "JUAN GARCIA LOPEZ"


class TestHSBCOCRSplitAmount:
    """Tests for transaction lines where OCR splits the amount to a separate line."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    def test_split_amount_line(self, parser):
        """When TX_NO_AMOUNT_RE matches and next line has amount."""
        text = """\
c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
Tarjeta titular 4524123456789012

15-Ene-2026 15-Ene-2026 TIENDA GRANDE MEX
$1,234.56

Total cargos |+|$1,234.56"""
        lines = text.split("\n")
        txs = parser._parse_transactions(lines, [])
        assert len(txs) == 1
        assert txs[0].amount == 1234.56
        assert "TIENDA GRANDE" in txs[0].description

    def test_split_amount_payment(self, parser):
        """PAGO in description without amount should be detected as payment."""
        text = """\
c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
Tarjeta titular 4524123456789012

15-Ene-2026 15-Ene-2026 SUPAGO GRACIAS
$5,000.00

Total cargos |+|$5,000.00"""
        lines = text.split("\n")
        txs = parser._parse_transactions(lines, [])
        assert len(txs) == 1
        assert txs[0].tx_type == TransactionType.PAYMENT
        assert txs[0].amount < 0

    def test_no_amount_stores_pending(self, parser):
        """TX without amount and no following amount line stores pending description."""
        text = """\
c) CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
Tarjeta titular 4524123456789012

15-Ene-2026 15-Ene-2026 TIENDA GRANDE MEX

APPSTORE DIGITAL TOKYO JP
12-Ene-2026 12-Ene-2026 MONEDA EXTRANJERA: 9.98 USD TC: 17.99699 DEL 12 DE ENERO + $179.51

Total cargos |+|$179.51"""
        lines = text.split("\n")
        txs = parser._parse_transactions(lines, [])
        foreign = [tx for tx in txs if tx.original_currency]
        assert len(foreign) == 1
        assert foreign[0].description == "APPSTORE DIGITAL TOKYO JP"


class TestHSBCBuildTransactionManual:
    """Tests for _build_transaction_manual."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    def test_valid_transaction(self, parser):
        tx = parser._build_transaction_manual("15-Ene-2026", "TIENDA", 100.0, False)
        assert tx is not None
        assert tx.amount == 100.0
        assert tx.tx_type == TransactionType.CHARGE

    def test_credit_transaction(self, parser):
        tx = parser._build_transaction_manual("15-Ene-2026", "TIENDA", 100.0, True)
        assert tx is not None
        assert tx.amount == -100.0

    def test_invalid_date_returns_none(self, parser):
        tx = parser._build_transaction_manual("invalid", "TIENDA", 100.0, False)
        assert tx is None


class TestHSBCForeignNoAmount:
    """Test foreign tx when MXN amount is missing."""

    @pytest.fixture
    def parser(self):
        return HSBCParser()

    def test_no_mxn_amount_uses_calculated(self, parser):
        """When no MXN amount found, use calculated value."""
        line = "12-Ene-2026 12-Ene-2026 MONEDA EXTRANJERA: 10.00 USD TC: 20.00000 DEL 12 DE ENERO"
        tx = parser._parse_foreign_tx(line, "STORE NAME")
        assert tx is not None
        assert tx.amount == 200.00

    def test_no_foreign_match_returns_none(self, parser):
        tx = parser._parse_foreign_tx("some random line", None)
        assert tx is None

    def test_no_date_returns_none(self, parser):
        line = "MONEDA EXTRANJERA: 10.00 USD TC: 20.00000"
        tx = parser._parse_foreign_tx(line, "STORE")
        assert tx is None
