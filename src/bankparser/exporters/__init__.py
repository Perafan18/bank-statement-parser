"""Exporter registry."""

from __future__ import annotations

from bankparser.exporters.base import BaseExporter
from bankparser.exporters.generic import GenericExporter
from bankparser.exporters.monarch import MonarchExporter
from bankparser.exporters.sure import SureExporter

_EXPORTERS: dict[str, BaseExporter] = {
    "generic": GenericExporter(),
    "sure": SureExporter(),
    "monarch": MonarchExporter(),
}


def get_exporter(name: str) -> BaseExporter:
    """Get an exporter by name."""
    exp = _EXPORTERS.get(name)
    if exp is None:
        available = ", ".join(_EXPORTERS.keys())
        raise ValueError(f"Unknown export format '{name}'. Available: {available}")
    return exp


def available_formats() -> list[str]:
    """List available export format names."""
    return list(_EXPORTERS.keys())


def register_exporter(exporter: BaseExporter) -> None:
    """Register a custom exporter."""
    _EXPORTERS[exporter.format_name] = exporter
