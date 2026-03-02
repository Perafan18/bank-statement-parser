# Arquitectura

```
PDF ──→ Parser (auto-detect) ──→ ParseResult ──→ Categorizer ──→ Exporter ──→ CSV
         │                         │                │
         │ can_parse()             │ StatementInfo   │ Reglas SQLite
         │ parse()                 │ Transaction[]   │ (ordenadas por prioridad)
         │                         │ warnings[]      │
         ▼                         ▼                 ▼
    ParserRegistry            models.py          database.py
```

## Modelos principales (`models.py`)

| Modelo | Proposito |
|--------|-----------|
| `Transaction` | Una transaccion individual. Cada parser las produce, cada exporter las consume. Campos: date, description, amount, currency, bank, cardholder, tx_type, category, installment, reference, original_amount, original_currency, exchange_rate, tags |
| `TransactionType` | Enum: `CHARGE`, `PAYMENT`, `CREDIT`, `FEE`, `INTEREST`, `TAX`, `MSI`, `MSI_ADJUSTMENT`, `TRANSFER` |
| `StatementInfo` | Metadatos del estado de cuenta: bank, account_number, cardholder, fechas del periodo, saldos |
| `ParseResult` | Contenedor: `info` (StatementInfo) + `transactions` (lista) + `warnings` (lista) |

## Parsers (`parsers/`)

Patron registry con auto-deteccion. Cada parser extiende `BaseParser`:

| Parser | Banco | Extraccion de texto | Notas |
|--------|-------|---------------------|-------|
| `AmexParser` | American Express Mexico | pdfplumber | Multi-tarjetahabiente, MSI, moneda extranjera (USD), referencias RFC |
| `BBVAParser` | BBVA Mexico (Bancomer) TDC | pdfplumber | Parseo en dos secciones (regular + MSI sin/con intereses), convencion de signo `+/-` |
| `HSBCParser` | HSBC Mexico TDC | OCR (pytesseract) | Fuentes CID-encoded requieren OCR, limpieza extensiva de artefactos |

## Exporters (`exporters/`)

Patron registry. Cada exporter extiende `BaseExporter`:

| Exporter | Formato | App destino |
|----------|---------|-------------|
| `GenericExporter` | 14 campos completos | Analisis raw |
| `SureExporter` | 8 campos con tags/notas | Sure / Maybe Finance |
| `MonarchExporter` | 8 campos con label de cuenta | Monarch Money |

## Base de datos (`database.py`)

SQLite en `~/.bankparser/bankparser.db` con dos tablas:

- **`categories`**: name (unico), parent_name, icon
- **`category_rules`**: pattern, category_name, bank (`*` = todos), priority (mayor = se revisa primero)

Se inicializa en la primera ejecucion con ~22 categorias (Shopping, Food & Dining, Groceries, Transportation, Subscriptions, etc.) y ~80 reglas para comercios mexicanos comunes y patrones especificos por banco.

## Estructura del proyecto

```
bank-statement-parser/
├── src/bankparser/
│   ├── __init__.py          # Version del paquete
│   ├── cli.py               # CLI con Click: parse, categories, rules, info
│   ├── models.py            # Transaction, StatementInfo, ParseResult, TransactionType
│   ├── database.py          # Schema SQLite, datos semilla, CRUD, matching de reglas
│   ├── categorizer.py       # Overrides por tipo → matching de reglas → "Uncategorized"
│   ├── parsers/
│   │   ├── __init__.py      # ParserRegistry + create_default_registry()
│   │   ├── base.py          # BaseParser: interfaz abstracta + helpers compartidos
│   │   ├── amex.py          # American Express Mexico
│   │   ├── bbva.py          # BBVA Mexico (Bancomer) TDC
│   │   └── hsbc.py          # HSBC Mexico TDC (basado en OCR)
│   └── exporters/
│       ├── __init__.py      # Registry de exporters
│       ├── base.py          # BaseExporter: interfaz abstracta + escritura CSV
│       ├── generic.py       # Exportacion de todos los campos
│       ├── sure.py          # Formato Sure / Maybe Finance
│       └── monarch.py       # Formato Monarch Money
├── tests/
│   ├── conftest.py          # Fixtures compartidos: tmp_db, sample_transactions
│   ├── test_models.py       # Tests de Transaction, ParseResult
│   ├── test_categorizer.py  # Tests de Database + Categorizer
│   ├── test_parsers/
│   │   ├── test_amex.py     # Tests del parser Amex + helpers de BaseParser
│   │   ├── test_bbva.py     # Tests del parser BBVA (fixtures inline)
│   │   └── test_hsbc.py     # Tests del parser HSBC (fixtures inline)
│   └── test_exporters/
│       └── test_exporters.py  # Tests de todos los exporters
├── pyproject.toml
├── CLAUDE.md                # Instrucciones para asistente AI
└── README.md
```
