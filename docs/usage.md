# Uso

## Inicio rapido

```bash
# Parsear un estado de cuenta (auto-detecta el banco)
bankparse parse statement.pdf

# Especificar banco y formato
bankparse parse statement.pdf --bank amex --format sure

# Multiples archivos a la vez
bankparse parse *.pdf -f sure -o all_transactions.csv

# Solo compras reales (sin comisiones, intereses, MSI)
bankparse parse statement.pdf --charges-only

# Excluir comisiones e intereses pero mantener todo lo demas
bankparse parse statement.pdf --no-fees

# Excluir mensualidades MSI
bankparse parse statement.pdf --no-msi

# Filtrar por nombre de tarjetahabiente (busqueda parcial)
bankparse parse statement.pdf --cardholder garcia
```

## Gestion de categorias

Las categorias y reglas viven en una base de datos SQLite en `~/.bankparser/bankparser.db`. La base de datos se crea automaticamente en la primera ejecucion con ~22 categorias y ~80 reglas pre-configuradas.

```bash
# Listar todas las categorias
bankparse categories list

# Agregar una nueva categoria
bankparse categories add "Mascotas" --icon "🐕"

# Eliminar una categoria (tambien elimina sus reglas)
bankparse categories remove "Mascotas" --yes

# Listar todas las reglas (ordenadas por prioridad)
bankparse rules list

# Listar reglas para un banco especifico
bankparse rules list --bank bbva

# Agregar una regla personalizada (mayor prioridad = se revisa primero)
bankparse rules add "COSTCO" "Groceries"
bankparse rules add "VET" "Mascotas" --bank amex --priority 20

# Eliminar una regla por ID
bankparse rules remove 42

# Mostrar estadisticas de la base de datos
bankparse info
```

### Como funciona la categorizacion

Las transacciones se categorizan en este orden:

1. **Override por tipo**: Pagos, Intereses, Comisiones, Impuestos, MSI y Ajustes MSI se auto-categorizan por su `TransactionType` sin importar la descripcion
2. **Matching de reglas**: La descripcion se compara contra `category_rules` (busqueda case-insensitive por substring, ordenada por prioridad descendente, reglas especificas del banco junto con reglas wildcard `*`)
3. **Fallback**: Si ninguna regla coincide, la transaccion se categoriza como "Uncategorized"

## Formatos de exportacion

| Formato   | App                  | Columnas principales                                       |
|-----------|----------------------|------------------------------------------------------------|
| `generic` | Cualquiera / analisis | date, description, amount, currency, bank, cardholder, type, category, installment, reference, original_amount, original_currency, exchange_rate, tags |
| `sure`    | Sure / Maybe Finance | date, name, amount, currency, category, tags, account, notes |
| `monarch` | Monarch Money        | Date, Merchant, Amount, Category, Account, Tags, Notes, Original Currency |

### Convencion de montos

- **Cargos** son montos positivos (ej. `499.00`)
- **Pagos y creditos** son montos negativos (ej. `-10000.00`)
- Todos los montos estan en MXN a menos que `original_currency` este definido

## Depurar un estado de cuenta

Si un estado de cuenta no se parsea correctamente:

```python
import pdfplumber

with pdfplumber.open("statement.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n{'='*60}")
        print(f"PAGE {i + 1}")
        print('='*60)
        print(page.extract_text())
```

Si pdfplumber devuelve texto ilegible, prueba OCR:

```python
from bankparser.parsers.base import BaseParser

pages = BaseParser.extract_text_with_ocr(Path("statement.pdf"))
for i, text in enumerate(pages):
    print(f"\n=== PAGE {i + 1} ===")
    print(text)
```

Despues ajusta los patrones regex en el archivo del parser correspondiente.
