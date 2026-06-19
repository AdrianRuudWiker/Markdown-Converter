"""Converter package. Importing it registers all converters.

This is the single place that wires converters into the registry. To enable a
new format, add its converter here.
"""

from __future__ import annotations

from app.converters import generic, registry


def register_all() -> None:
    """Register every converter. Idempotent (clears first)."""
    registry.clear()

    # PDF: text extraction with automatic OCR fallback for scanned files.
    # Imported lazily so a missing optional engine dependency surfaces only
    # when that format is actually used.
    from app.converters.pdf_text import PdfTextConverter

    registry.register(PdfTextConverter())

    # Office and web formats, all via MarkItDown.
    registry.register(generic.word_converter())
    registry.register(generic.excel_converter())
    registry.register(generic.powerpoint_converter())
    registry.register(generic.html_converter())


register_all()
