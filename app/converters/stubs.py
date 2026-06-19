"""Registered-but-not-yet-enabled converters.

These make planned formats visible in the UI (with a "planned" badge) and
return a clear "coming soon" message (HTTP 501) instead of a generic failure.
Enabling a format later is a small change: write a real converter (typically a
thin MarkItDown wrapper), register it in place of the stub, and add the
relevant MarkItDown extra to the dependencies.
"""

from __future__ import annotations

from app.converters.base import ConversionResult
from app.errors import NotImplementedConverterError


class StubConverter:
    """A placeholder converter for a known-but-not-yet-enabled format."""

    implemented = False

    def __init__(
        self,
        name: str,
        extensions: tuple[str, ...],
        mime_types: tuple[str, ...],
    ) -> None:
        self.name = name
        self.extensions = extensions
        self.mime_types = mime_types

    def convert(self, data: bytes, filename: str) -> ConversionResult:
        raise NotImplementedConverterError(
            f"Converting '{self.name}' files is planned but not yet available."
        )


# Planned formats. Each becomes a real converter when enabled.
DOCX = StubConverter(
    "word",
    (".docx", ".doc"),
    (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ),
)
XLSX = StubConverter(
    "excel",
    (".xlsx", ".xls"),
    (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ),
)
PPTX = StubConverter(
    "powerpoint",
    (".pptx", ".ppt"),
    (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-powerpoint",
    ),
)
HTML = StubConverter(
    "html",
    (".html", ".htm"),
    ("text/html",),
)
PDF_OCR = StubConverter(
    "pdf-ocr",
    (),  # shares .pdf; only reachable once the text converter detects no text
    (),
)
