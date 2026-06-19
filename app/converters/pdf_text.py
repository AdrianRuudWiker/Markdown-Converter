"""PDF -> Markdown converter, backed by Microsoft MarkItDown.

MarkItDown is MIT-licensed and runs fully locally for text documents. We
deliberately construct it with **no LLM client and no API key**, so there is
never any network egress during conversion — a hard requirement for sensitive
Ministry of Finance documents.

If a PDF has no selectable text (i.e. it is scanned / image-only), this
converter automatically falls back to local OCR (see :mod:`app.converters.ocr`)
so the user still gets Markdown back without doing anything special.
"""

from __future__ import annotations

import io

from app.converters import ocr
from app.converters.base import ConversionResult
from app.errors import ConversionError


class PdfTextConverter:
    name = "pdf"
    extensions = (".pdf",)
    mime_types = ("application/pdf",)
    implemented = True

    def __init__(self) -> None:
        # Import lazily so the module can be inspected (and stubs registered)
        # even if the optional MarkItDown dependency is missing.
        from markitdown import MarkItDown

        # No llm_client / no llm_model => no outbound calls, ever.
        self._engine = MarkItDown(enable_plugins=False)

    def convert(self, data: bytes, filename: str) -> ConversionResult:
        warnings: list[str] = []

        # Validate the PDF magic header. MarkItDown otherwise silently falls
        # back to plain-text extraction for non-PDF bytes, which would hide a
        # genuinely wrong/corrupt file behind a misleading "success".
        if not data[:1024].lstrip().startswith(b"%PDF-"):
            raise ConversionError(
                f"'{filename}' is not a valid PDF file."
            )

        try:
            result = self._engine.convert_stream(
                io.BytesIO(data),
                file_extension=".pdf",
            )
        except Exception as exc:  # noqa: BLE001 - normalize lib errors
            raise ConversionError(
                f"Could not convert PDF '{filename}': {exc}"
            ) from exc

        markdown = (result.text_content or "").strip()
        if not markdown:
            # No selectable text => scanned / image-only PDF. Fall back to local
            # OCR so the user still gets Markdown back automatically.
            markdown = ocr.ocr_pdf(data, filename)
            warnings.append(
                "No selectable text was found, so this PDF was read with OCR. "
                "Please double-check the result for accuracy."
            )

        metadata = {}
        title = getattr(result, "title", None)
        if title:
            metadata["title"] = str(title)

        return ConversionResult(
            markdown=markdown,
            source_filename=filename,
            warnings=warnings,
            metadata=metadata,
        )
