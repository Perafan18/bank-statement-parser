# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato esta basado en [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-03-01

### Agregado

- **Parsers:** Amex Mexico, BBVA Mexico TDC, HSBC Mexico TDC (basado en OCR)
- **Formatos de exportacion:** Generico (todos los campos), Sure/Maybe Finance, Monarch Money
- **Categorizacion:** Respaldada por SQLite con 22 categorias y 80+ reglas pre-configuradas
- **CLI:** Comandos `bankparse parse`, `categories`, `rules`, `info`
- **Soporte OCR:** PDFs de HSBC con fuentes CID-encoded via pytesseract + pdf2image
- **Multi-tarjetahabiente:** Estados de Amex distinguen titular vs adicionales
- **Moneda extranjera:** Monto original, codigo de divisa y tipo de cambio preservados
- **Seguimiento de MSI:** Info de mensualidades tanto "sin intereses" como "con intereses"
- **Filtros:** Por tarjetahabiente, tipo de transaccion, comisiones, MSI, solo cargos
