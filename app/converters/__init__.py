"""Converter package. Importing it registers all converters.

This is the single place that wires converters into the registry. To enable a
new format, replace its stub here with the real converter.
"""

from __future__ import annotations

from app.converters import registry, stubs


def register_all() -> None:
    """Register every converter. Idempotent (clears first)."""
    registry.clear()

    # Real, enabled converters. Imported lazily so a missing optional engine
    # dependency surfaces only when that format is actually used.
    from app.converters.pdf_text import PdfTextConverter

    registry.register(PdfTextConverter())

    # Planned formats, shown in the UI and returning a clear "coming soon".
    registry.register(stubs.DOCX)
    registry.register(stubs.XLSX)
    registry.register(stubs.PPTX)
    registry.register(stubs.HTML)


register_all()
