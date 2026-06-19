"""OCR fallback for scanned / image-only PDFs.

These tests need Tesseract + Poppler installed (the dev container installs them).
If they are missing, the tests are skipped rather than failing.
"""

from __future__ import annotations

import pytest

from app.converters import ocr
from app.converters.pdf_text import PdfTextConverter

requires_ocr = pytest.mark.skipif(
    not ocr.is_available(), reason="Tesseract/Poppler not installed"
)


@requires_ocr
def test_scanned_pdf_falls_back_to_ocr(scanned_pdf_bytes):
    result = PdfTextConverter().convert(scanned_pdf_bytes, "scanned.pdf")
    # OCR should recover the rendered text.
    assert "Quarterly Report" in result.markdown
    # ...and the user is told OCR was used.
    assert any("OCR" in w for w in result.warnings)


@requires_ocr
def test_ocr_helper_direct(scanned_pdf_bytes):
    text = ocr.ocr_pdf(scanned_pdf_bytes, "scanned.pdf", lang="eng")
    assert "Quarterly Report" in text


def test_ocr_unavailable_gives_clear_error(monkeypatch):
    monkeypatch.setattr(ocr, "is_available", lambda: False)
    with pytest.raises(Exception) as excinfo:
        ocr.ocr_pdf(b"%PDF-1.4", "x.pdf")
    assert "Tesseract" in str(excinfo.value)
