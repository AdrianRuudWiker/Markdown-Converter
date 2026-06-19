"""Golden-file test for the text PDF converter."""

from __future__ import annotations

import pytest

from app.converters.pdf_text import PdfTextConverter
from app.errors import ConversionError


def _normalize(text: str) -> str:
    # Collapse trailing whitespace and blank-line differences so the golden
    # comparison isn't brittle to insignificant formatting.
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


def test_pdf_matches_golden(sample_pdf_bytes, expected_markdown):
    result = PdfTextConverter().convert(sample_pdf_bytes, "sample_text.pdf")
    assert _normalize(result.markdown) == _normalize(expected_markdown)


def test_pdf_contains_headings(sample_pdf_bytes):
    result = PdfTextConverter().convert(sample_pdf_bytes, "sample_text.pdf")
    assert "Markdown Converter Test Document" in result.markdown


def test_corrupt_pdf_raises_conversion_error():
    with pytest.raises(ConversionError):
        PdfTextConverter().convert(b"this is not a pdf", "broken.pdf")
