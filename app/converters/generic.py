"""Generic MarkItDown-backed converter for office and web formats.

Word, Excel, PowerPoint, and HTML all convert through the same MarkItDown call;
they differ only in the file-extension hint and the labels shown in the UI. As
with the PDF converter, MarkItDown is created with **no LLM client**, so there
is no network access during conversion.
"""

from __future__ import annotations

import io

from app.converters.base import ConversionResult
from app.errors import ConversionError


class MarkItDownConverter:
    """A converter for any format MarkItDown can read from a byte stream."""

    implemented = True

    def __init__(
        self,
        name: str,
        extensions: tuple[str, ...],
        mime_types: tuple[str, ...],
        file_extension: str,
    ) -> None:
        from markitdown import MarkItDown

        self.name = name
        self.extensions = extensions
        self.mime_types = mime_types
        self._file_extension = file_extension
        self._engine = MarkItDown(enable_plugins=False)

    def convert(self, data: bytes, filename: str) -> ConversionResult:
        try:
            result = self._engine.convert_stream(
                io.BytesIO(data),
                file_extension=self._file_extension,
            )
        except Exception as exc:  # noqa: BLE001 - normalize library errors
            raise ConversionError(
                f"Could not convert '{filename}': {exc}"
            ) from exc

        markdown = (result.text_content or "").strip()
        if not markdown:
            raise ConversionError(
                f"No content could be extracted from '{filename}'. The file may "
                "be empty, corrupt, or password-protected."
            )

        metadata = {}
        title = getattr(result, "title", None)
        if title:
            metadata["title"] = str(title)

        return ConversionResult(
            markdown=markdown,
            source_filename=filename,
            metadata=metadata,
        )


def word_converter() -> MarkItDownConverter:
    return MarkItDownConverter(
        "word",
        (".docx", ".doc"),
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ),
        ".docx",
    )


def excel_converter() -> MarkItDownConverter:
    return MarkItDownConverter(
        "excel",
        (".xlsx", ".xls"),
        (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ),
        ".xlsx",
    )


def powerpoint_converter() -> MarkItDownConverter:
    return MarkItDownConverter(
        "powerpoint",
        (".pptx", ".ppt"),
        (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.ms-powerpoint",
        ),
        ".pptx",
    )


def html_converter() -> MarkItDownConverter:
    return MarkItDownConverter(
        "html",
        (".html", ".htm"),
        ("text/html",),
        ".html",
    )
