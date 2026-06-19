"""Registry resolution and converter wiring."""

from __future__ import annotations

import app.converters  # noqa: F401 - ensures converters are registered
from app.converters import registry
from app.converters.base import ConversionResult


def test_resolve_pdf_by_extension():
    conv = registry.resolve("report.pdf", None)
    assert conv is not None
    assert conv.name == "pdf"
    assert conv.implemented is True


def test_resolve_pdf_by_mime_takes_precedence():
    # Misleading extension, correct MIME -> resolves by MIME.
    conv = registry.resolve("report.bin", "application/pdf")
    assert conv is not None
    assert conv.name == "pdf"


def test_resolve_unknown_returns_none():
    assert registry.resolve("notes.xyz", "application/octet-stream") is None


def test_office_formats_are_implemented():
    for filename, expected in [
        ("memo.docx", "word"),
        ("budget.xlsx", "excel"),
        ("deck.pptx", "powerpoint"),
        ("page.html", "html"),
    ]:
        conv = registry.resolve(filename, None)
        assert conv is not None, filename
        assert conv.name == expected
        assert conv.implemented is True


def test_supported_catalog_shape():
    catalog = registry.supported()
    names = {c["name"] for c in catalog}
    assert {"pdf", "word", "excel", "powerpoint", "html"} <= names
    for entry in catalog:
        assert set(entry) == {"name", "extensions", "mime_types", "implemented"}
        assert entry["implemented"] is True


def test_accepted_extensions_include_office():
    exts = registry.accepted_extensions(implemented_only=True)
    assert {".pdf", ".docx", ".xlsx", ".pptx", ".html"} <= set(exts)


def test_pdf_converter_returns_conversion_result(sample_pdf_bytes):
    conv = registry.resolve("sample_text.pdf", "application/pdf")
    result = conv.convert(sample_pdf_bytes, "sample_text.pdf")
    assert isinstance(result, ConversionResult)
    assert result.source_filename == "sample_text.pdf"
