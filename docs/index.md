# Bank Statement Parser

Convierte estados de cuenta bancarios mexicanos en PDF (American Express, BBVA, HSBC) a archivos CSV
compatibles con apps de finanzas personales como [Sure](https://github.com/we-promise/sure),
Monarch Money, y otras.

## Funcionalidades

- **Soporte multi-banco**: Amex, BBVA, HSBC Mexico con auto-deteccion
- **Categorizacion inteligente**: Reglas en SQLite con prioridad, patrones por banco, y ~80 reglas pre-configuradas
- **Multiples formatos de exportacion**: Generico (todos los campos), Sure/Maybe Finance, Monarch Money
- **Seguimiento de MSI**: Info de mensualidades preservada (cargo X de Y), tanto "sin intereses" como "con intereses"
- **Moneda extranjera**: Monto original, codigo de divisa y tipo de cambio preservados
- **Multi-tarjetahabiente**: Distingue titular vs adicionales (Amex)
- **Filtros**: Por tarjetahabiente, tipo de transaccion, comisiones, MSI, solo cargos
- **OCR de respaldo**: Estados de cuenta HSBC con fuentes CID-encoded se parsean via Tesseract OCR

## Instalacion

```bash
git clone https://github.com/Perafan18/bank-statement-parser.git
cd bank-statement-parser
pip install -e ".[dev]"
```

### Soporte OCR (requerido para HSBC)

Los estados de cuenta de HSBC Mexico usan fuentes CID-encoded que pdfplumber no puede decodificar. Para parsear estados de HSBC, instala las dependencias de OCR:

```bash
# Paquetes de Python
pip install -e ".[ocr]"

# Paquetes del sistema (Ubuntu/Debian)
sudo apt install tesseract-ocr tesseract-ocr-spa poppler-utils

# macOS
brew install tesseract poppler
```

Sin estos paquetes, los estados de BBVA y Amex funcionan normalmente, pero el parseo de HSBC mostrara un mensaje de error claro con instrucciones de instalacion.

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

---

Consulta [Uso](usage.md) para la referencia completa del CLI, y [Arquitectura](architecture.md) para los detalles internos del proyecto.
