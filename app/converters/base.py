"""Core converter interface and shared types.

Every file format is handled by a :class:`Converter`. Converters receive raw
``bytes`` (never a filesystem path) so the orchestrator can keep document data
in memory and centralize any temp-file handling and cleanup. This matters for
sensitive Ministry of Finance documents: we avoid leaving plaintext on disk
unless a library strictly requires a path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ConversionResult:
    """The outcome of converting a single document."""

    markdown: str
    source_filename: str
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class Converter(Protocol):
    """A pluggable converter for one or more file formats.

    Implementations are registered in :mod:`app.converters.registry` keyed by
    file extension and MIME type. To add a new format, create a converter and
    register it in :mod:`app.converters` — no core code changes required.
    """

    name: str
    extensions: tuple[str, ...]
    mime_types: tuple[str, ...]
    implemented: bool

    def convert(self, data: bytes, filename: str) -> ConversionResult:
        """Convert ``data`` (the raw file bytes) to Markdown.

        Raises:
            NotImplementedConverterError: if this is a registered stub for a
                format that is planned but not yet enabled.
            ConversionError: if the document cannot be converted (corrupt,
                encrypted, or otherwise unreadable).
        """
        ...
