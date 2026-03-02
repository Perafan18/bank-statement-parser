# Agregar un nuevo banco

Esta es una guia paso a paso. Usa el parser de BBVA (`src/bankparser/parsers/bbva.py`) como implementacion de referencia ya que es el ejemplo mas limpio.

## Paso 1: Estudiar el PDF

Antes de escribir codigo, extrae el texto del PDF de tu banco para entender su estructura:

```python
import pdfplumber

with pdfplumber.open("statement.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n{'='*60}")
        print(f"PAGE {i + 1}")
        print('='*60)
        print(page.extract_text())
```

Si pdfplumber devuelve texto ilegible (ej. caracteres `(cid:XX)`), el PDF usa fuentes CID-encoded y necesitaras OCR. Consulta el parser de HSBC para ver como manejarlo.

Identifica:
- **Identificadores del banco** en la primera pagina (para `can_parse()`)
- **Metadatos del estado de cuenta**: numero de cuenta, periodo, nombre del tarjetahabiente, saldos
- **Formato de transacciones**: que columnas existen, como se formatean las fechas, como se distinguen creditos vs cargos
- **Marcadores de seccion**: encabezados como "CARGOS Y ABONOS", lineas de totales, saltos de pagina
- **Transacciones especiales**: mensualidades MSI, moneda extranjera, comisiones, intereses

## Paso 2: Crear el archivo del parser

Crea `src/bankparser/parsers/mibanco.py`:

```python
"""Parser for MyBank Mexico credit card statements."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from bankparser.models import ParseResult, StatementInfo, Transaction, TransactionType
from bankparser.parsers.base import BaseParser


class MyBankParser(BaseParser):
    """Parses MyBank Mexico PDF statements."""

    bank_name = "mybank"

    # ── Deteccion ─────────────────────────────────────────────────────────

    def can_parse(self, pdf_path: Path) -> bool:
        """Verifica si este PDF pertenece a MyBank.

        Busca texto especifico del banco en la primera pagina. Usa multiples
        identificadores para evitar falsos positivos (ej. un estado de BBVA
        que menciona "amex" en una direccion).
        """
        text = self.extract_first_page_text(pdf_path).lower()
        return "mybank" in text or "my bank mexico" in text

    # ── Regexes ───────────────────────────────────────────────────────────

    # Define patrones regex como constantes compiladas a nivel de clase.
    # Usa re.compile() para rendimiento (se ejecutan en cada linea).
    #
    # Ejemplo: linea de transaccion "15/01/2026 OXXO TONALA $48.50"
    TX_RE = re.compile(
        r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+\$([\d,]+\.\d{2})\s*$'
    )

    # Lineas a ignorar (encabezados, totales, ruido)
    SKIP_PATTERNS = [
        re.compile(r'^FECHA\s+DESCRIPCION'),  # encabezado de tabla
        re.compile(r'^TOTAL'),                  # fila de totales
    ]

    # ── Parseo principal ──────────────────────────────────────────────────

    def parse(self, pdf_path: Path) -> ParseResult:
        pages_text = self.extract_text_from_pdf(pdf_path)
        warnings: list[str] = []

        full_text = "\n".join(pages_text)
        info = self._extract_info(full_text)

        # Recopilar todas las lineas de todas las paginas
        all_lines: list[str] = []
        for text in pages_text:
            all_lines.extend(text.split('\n'))

        transactions = self._parse_transactions(all_lines, warnings)

        # Propagar tarjetahabiente desde la info del estado de cuenta
        if info.cardholder:
            for tx in transactions:
                tx.cardholder = info.cardholder

        return ParseResult(info=info, transactions=transactions, warnings=warnings)

    # ── Extraccion de info ────────────────────────────────────────────────

    def _extract_info(self, text: str) -> StatementInfo:
        info = StatementInfo(bank=self.bank_name)
        # Extrae numero de cuenta, periodo, tarjetahabiente, etc. con regex
        # ...
        return info

    # ── Parseo de transacciones ───────────────────────────────────────────

    def _parse_transactions(
        self, lines: list[str], warnings: list[str],
    ) -> list[Transaction]:
        transactions: list[Transaction] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or self._should_skip(stripped):
                continue

            match = self.TX_RE.match(stripped)
            if not match:
                continue

            # Parsear campos del match
            date_str = match.group(1)
            description = match.group(2).strip()
            amount = self.parse_mx_amount(match.group(3))

            # Clasificar la transaccion
            tx_type = self._classify(description, is_credit=False)

            tx = Transaction(
                date=self._parse_date(date_str),
                description=description,
                amount=amount,
                currency="MXN",
                bank=self.bank_name,
                tx_type=tx_type,
            )
            transactions.append(tx)

        return transactions

    # ── Helpers ────────────────────────────────────────────────────────────

    def _classify(self, description: str, is_credit: bool) -> TransactionType:
        """Clasifica una transaccion segun su descripcion y signo."""
        desc = description.upper()
        if "PAGO" in desc:
            return TransactionType.PAYMENT
        if "INTERES" in desc:
            return TransactionType.INTEREST
        if "IVA" in desc:
            return TransactionType.TAX
        if "COMISION" in desc or "ANUALIDAD" in desc:
            return TransactionType.FEE
        if is_credit:
            return TransactionType.CREDIT
        return TransactionType.CHARGE

    def _should_skip(self, line: str) -> bool:
        """Verifica si una linea es encabezado, total, o ruido."""
        for pattern in self.SKIP_PATTERNS:
            if pattern.match(line):
                return True
        return False
```

## Paso 3: Registrar el parser

En `src/bankparser/parsers/__init__.py`, agrega tu parser a `create_default_registry()`:

```python
def create_default_registry() -> ParserRegistry:
    from bankparser.parsers.amex import AmexParser
    from bankparser.parsers.bbva import BBVAParser
    from bankparser.parsers.hsbc import HSBCParser
    from bankparser.parsers.mybank import MyBankParser  # agregar import

    registry = ParserRegistry()
    registry.register(AmexParser())
    registry.register(BBVAParser())
    registry.register(HSBCParser())
    registry.register(MyBankParser())  # registrarlo
    return registry
```

## Paso 4: Agregar reglas de categorizacion del banco

En `src/bankparser/database.py`, agrega reglas a `DEFAULT_RULES`:

```python
DEFAULT_RULES = [
    # ... reglas existentes ...

    # Especificas de MyBank
    ("PAGO DOMICILIADO", "Payment", "mybank", 100),
    ("COMISION MENSUAL", "Fees", "mybank", 100),
]
```

Nota: estas solo aplican a bases de datos nuevas. Usuarios existentes deben agregar reglas manualmente via CLI.

## Paso 5: Escribir tests

Crea `tests/test_parsers/test_mybank.py`. Usa fixtures inline (no PDFs reales) para que los tests corran en cualquier lado:

```python
"""Tests for the MyBank parser."""

from datetime import date
import pytest
from bankparser.models import TransactionType
from bankparser.parsers.mybank import MyBankParser


# Usa texto real extraido de un estado de cuenta (redactado)
MYBANK_INFO_TEXT = """MyBank Mexico S.A.
Numero de cuenta: 1234567890
Periodo: 01/01/2026 al 31/01/2026
JUAN GARCIA LOPEZ
"""

MYBANK_TRANSACTIONS_TEXT = """\
FECHA DESCRIPCION MONTO
15/01/2026 OXXO TONALA $48.50
16/01/2026 PAGO RECIBIDO -$10,000.00
TOTAL $48.50
"""


class TestMyBankParser:
    @pytest.fixture
    def parser(self):
        return MyBankParser()

    def test_bank_name(self, parser):
        assert parser.bank_name == "mybank"

    def test_extract_info(self, parser):
        info = parser._extract_info(MYBANK_INFO_TEXT)
        assert info.bank == "mybank"
        # assert info.account_number == "1234567890"
        # assert info.cardholder == "JUAN GARCIA LOPEZ"

    def test_parse_transactions(self, parser):
        lines = MYBANK_TRANSACTIONS_TEXT.split("\n")
        transactions = parser._parse_transactions(lines, [])
        assert len(transactions) >= 1

    def test_classify_payment(self, parser):
        assert parser._classify("PAGO RECIBIDO", True) == TransactionType.PAYMENT

    def test_classify_charge(self, parser):
        assert parser._classify("OXXO TONALA", False) == TransactionType.CHARGE
```

Ejecuta tests: `pytest tests/test_parsers/test_mybank.py -v`

## Paso 6: Probar con un PDF real

Pon un estado de cuenta real (redactado) en `samples/mybank/` (excluido de git por `*.pdf` en `.gitignore`):

```bash
bankparse parse samples/mybank/statement.pdf --bank mybank
```

## Helpers de BaseParser disponibles para todos los parsers

| Helper | Descripcion |
|--------|-------------|
| `parse_spanish_date(day, month_name, year)` | Nombres completos de meses en espanol: "Enero", "Febrero", etc. |
| `parse_mx_amount(amount_str)` | Formato mexicano: `"$1,234.56"` -> `1234.56`. Lanza `ValueError` con contexto si el input es invalido. |
| `extract_text_from_pdf(pdf_path)` | Devuelve `list[str]` (un string por pagina) via pdfplumber |
| `extract_first_page_text(pdf_path)` | Devuelve solo el texto de la primera pagina (rapido, para deteccion) |
| `extract_text_with_ocr(pdf_path, dpi, psm)` | OCR via pytesseract + pdf2image. Requiere extras `[ocr]` + paquetes del sistema. |

## Patrones comunes en estados de cuenta mexicanos

- **Fechas**: `DD de Mes` (Amex), `DD-mmm-YYYY` (BBVA/HSBC), `DD/MM/YYYY`
- **Montos**: Siempre formato `$X,XXX.XX` con coma como separador de miles
- **Creditos/pagos**: Indicados por signo `-`, sufijo `CR`, o columna separada
- **MSI**: Mensualidades "sin intereses", usualmente en seccion separada
- **Moneda extranjera**: Linea de continuacion con monto original, codigo de divisa y tipo de cambio
- **IVA**: Impuesto sobre comisiones/intereses, usualmente en linea separada
