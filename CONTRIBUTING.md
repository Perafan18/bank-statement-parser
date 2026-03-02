# Contribuir a Bank Statement Parser

Gracias por tu interés en contribuir. Este proyecto busca cubrir la mayor cantidad de bancos mexicanos posible, y toda ayuda es bienvenida.

## Cómo contribuir

### Agregar un nuevo banco

Esta es la contribución más valiosa. Si tienes estados de cuenta de un banco que no está soportado (Banorte, Santander, Citibanamex, etc.), puedes agregar un parser.

**Resumen rápido:**

1. Extrae el texto del PDF con pdfplumber para entender la estructura
2. Crea `src/bankparser/parsers/tubanco.py` extendiendo `BaseParser`
3. Implementa `can_parse()` y `parse()`
4. Regístralo en `src/bankparser/parsers/__init__.py`
5. Escribe tests con fixtures inline en `tests/test_parsers/test_tubanco.py`
6. (Opcional) Agrega reglas de categorización en `database.py`

El README tiene una [guía paso a paso completa](README.md#adding-a-new-bank-parser) con código de referencia. Usa `BBVAParser` como ejemplo — es el parser más limpio.

### Agregar un formato de exportación

Si usas una app de finanzas que no está soportada (YNAB, Copilot Money, Fintual, etc.):

1. Crea `src/bankparser/exporters/tuformato.py` extendiendo `BaseExporter`
2. Implementa `get_headers()` y `format_row()`
3. Regístralo en `src/bankparser/exporters/__init__.py`

### Mejorar un parser existente

Los parsers actuales no cubren todos los edge cases. Si encuentras transacciones que no se parsean o fechas incorrectas:

1. Extrae el texto del PDF problemático (redactando datos sensibles)
2. Abre un issue con el texto relevante y el resultado esperado
3. O mejor aún, agrega un test que reproduzca el bug y manda un PR con el fix

## Setup de desarrollo

```bash
git clone https://github.com/Perafan18/bank-statement-parser.git
cd bank-statement-parser
pip install -e ".[dev]"
```

Para HSBC (requiere OCR):
```bash
pip install -e ".[ocr]"
sudo apt install tesseract-ocr tesseract-ocr-spa poppler-utils  # Ubuntu/Debian
```

## Tests

```bash
pytest                                    # suite completa
pytest tests/test_parsers/test_bbva.py -v # un archivo
pytest -k "test_classify_payment"         # un test específico
ruff check src/ tests/                    # lint
```

Los tests usan fixtures inline (texto hardcodeado), no PDFs reales. Esto permite que cualquiera los ejecute sin archivos privados. También hay tests de integración con PDFs generados programáticamente en `tests/fixtures/`.

## Convenciones

- Python 3.10+, `from __future__ import annotations`
- Type hints en APIs públicas
- Regex como constantes compiladas a nivel de clase (`TX_RE = re.compile(...)`)
- Ruff para lint/format (line length: 100)
- Commits en inglés, convención: `feat:`, `fix:`, `test:`, `chore:`, `docs:`

## Notas sobre datos sensibles

**Nunca** incluyas estados de cuenta reales en PRs o issues. Redacta nombres, números de cuenta y montos antes de compartir texto extraído de PDFs.

## Bancos que faltan

Si quieres contribuir pero no sabes por dónde empezar, estos bancos son los más solicitados:

- Banorte
- Santander México
- Citibanamex
- Scotiabank México
- Formatos de cuenta de débito (actualmente solo TDC/crédito)
