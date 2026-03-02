# Agregar un nuevo formato de exportacion

## Paso 1: Crear el exporter

Crea `src/bankparser/exporters/miformato.py`:

```python
"""MyFormat CSV exporter."""

from bankparser.exporters.base import BaseExporter
from bankparser.models import Transaction


class MyFormatExporter(BaseExporter):
    format_name = "myformat"
    description = "MyFormat import compatible"

    def get_headers(self) -> list[str]:
        return ["Date", "Description", "Amount", "Category"]

    def format_row(self, tx: Transaction) -> list[str]:
        return [
            tx.date.isoformat(),
            tx.description,
            f"{tx.amount:.2f}",
            tx.category,
        ]
```

## Paso 2: Registrarlo

En `src/bankparser/exporters/__init__.py`:

```python
from bankparser.exporters.myformat import MyFormatExporter

_EXPORTERS: dict[str, BaseExporter] = {
    "generic": GenericExporter(),
    "sure": SureExporter(),
    "monarch": MonarchExporter(),
    "myformat": MyFormatExporter(),  # agregar aqui
}
```

Aparecera automaticamente en las opciones de `bankparse parse --format`.
