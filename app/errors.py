"""Domain exceptions and their HTTP status mappings.

Keeping the exception -> status mapping here lets the API layer translate
failures into clean responses without sprinkling status codes through the
converters.
"""

from __future__ import annotations


class MarkdownConverterError(Exception):
    """Base class for all application errors."""

    #: HTTP status code the API layer should return for this error.
    status_code: int = 500


class UnsupportedFormatError(MarkdownConverterError):
    """No converter is registered for the given file type."""

    status_code = 415


class NotImplementedConverterError(MarkdownConverterError):
    """The format is recognized and planned, but not yet enabled."""

    status_code = 501


class FileTooLargeError(MarkdownConverterError):
    """The uploaded file exceeds the configured size limit."""

    status_code = 413


class ConversionError(MarkdownConverterError):
    """The document could not be converted (corrupt, encrypted, empty, ...)."""

    status_code = 422


class ConversionTimeoutError(MarkdownConverterError):
    """Conversion exceeded the configured per-file timeout."""

    status_code = 422
