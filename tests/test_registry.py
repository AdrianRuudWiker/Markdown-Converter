"""Registry resolution and stub behavior."""

from __future__ import annotations

import pytest

import app.converters  # noqa: F401 - ensures converters are registered
from app.converters import registry
from app.converters.base import ConversionResult
from app.errors import NotImplementedConverterError


def test_resolve_pdf_by_extension():
    conv = registry.resolve("report.pdf", None)
    assert conv is not None
    assert conv.name == "pdf-text"
    assert conv.implemented is True


def test_resolve_pdf_by_mime_takes_precedence():
    # Misleading extension, correct MIME -> resolves by MIME.
    conv = registry.resolve("report.bin", "application/pdf")
    assert conv is not None
    assert conv.name == "pdf-text"


def test_resolve_unknown_returns_none():
    assert registry.resolve("notes.xyz", "application/octet-stream") is None


def test_docx_is_registered_but_stub():
    conv = registry.resolve("memo.docx", None)
    assert conv is not None
    assert conv.implemented is False
    with pytest.raises(NotImplementedConverterError):
        conv.convert(b"", "memo.docx")


def test_supported_catalog_shape():
    catalog = registry.supported()
    names = {c["name"] for c in catalog}
    assert "pdf-text" in names
    assert {"word", "excel", "powerpoint", "html"} <= names
    for entry in catalog:
        assert set(entry) == {"name", "extensions", "mime_types", "implemented"}


def test_accepted_extensions_implemented_only():
    assert ".pdf" in registry.accepted_extensions(implemented_only=True)
    assert ".docx" not in registry.accepted_extensions(implemented_only=True)
    assert ".docx" in registry.accepted_extensions(implemented_only=False)


def test_pdf_converter_returns_conversion_result(sample_pdf_bytes):
    conv = registry.resolve("sample_text.pdf", "application/pdf")
    result = conv.convert(sample_pdf_bytes, "sample_text.pdf")
    assert isinstance(result, ConversionResult)
    assert result.source_filename == "sample_text.pdf"
