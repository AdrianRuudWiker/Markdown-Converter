"""Offline OCR for scanned / image-only PDFs.

Uses Tesseract (via ``pytesseract``) and Poppler (via ``pdf2image``) — both run
entirely on the local machine, so scanned documents are handled without any
network access. The default language set is Norwegian + English (``nor+eng``),
appropriate for Ministry of Finance documents; override with ``MDC_OCR_LANG``.

If the required system tools are not installed, :func:`ocr_pdf` raises a
:class:`ConversionError` with a clear, actionable message instead of crashing.
"""

from __future__ import annotations

from app.config import settings
from app.errors import ConversionError

_INSTALL_HINT = (
    "OCR for scanned PDFs needs Tesseract and Poppler installed. In a "
    "Codespace, rebuild the container (Command Palette -> 'Codespaces: Rebuild "
    "Container'); locally, install 'tesseract-ocr', the 'tesseract-ocr-nor'/"
    "'tesseract-ocr-eng' language packs, and 'poppler-utils'."
)


def is_available() -> bool:
    """Return True if both Tesseract and Poppler appear to be usable."""
    import shutil

    return bool(shutil.which("tesseract") and shutil.which("pdftoppm"))


def ocr_pdf(data: bytes, filename: str, lang: str | None = None) -> str:
    """Run OCR over every page of a PDF and return the combined text.

    Raises:
        ConversionError: if OCR tooling is missing or no text is recognized.
    """
    if not is_available():
        raise ConversionError(_INSTALL_HINT)

    try:
        import pytesseract
        from pdf2image import convert_from_bytes
    except ImportError as exc:  # pragma: no cover - guarded by is_available too
        raise ConversionError(_INSTALL_HINT) from exc

    language = lang or settings.ocr_lang
    try:
        images = convert_from_bytes(data, dpi=settings.ocr_dpi)
        pages = [pytesseract.image_to_string(img, lang=language) for img in images]
    except Exception as exc:  # noqa: BLE001 - normalize OCR/render errors
        raise ConversionError(
            f"OCR failed for '{filename}': {exc}"
        ) from exc

    text = "\n\n".join(page.strip() for page in pages if page.strip()).strip()
    if not text:
        raise ConversionError(
            f"OCR could not recognize any text in '{filename}'."
        )
    return text
