"""Registry that dispatches files to the right converter.

Resolution prefers MIME type (more reliable than a filename) and falls back to
the file extension. ``supported()`` exposes the catalog to the API/frontend so
the UI's accepted-types list and "planned" badges come from a single source of
truth.
"""

from __future__ import annotations

import os

from app.converters.base import Converter

_BY_EXT: dict[str, Converter] = {}
_BY_MIME: dict[str, Converter] = {}
_REGISTERED: list[Converter] = []


def register(converter: Converter) -> None:
    """Register a converter under all of its extensions and MIME types."""
    _REGISTERED.append(converter)
    for ext in converter.extensions:
        _BY_EXT[ext.lower()] = converter
    for mime in converter.mime_types:
        _BY_MIME[mime.lower()] = converter


def resolve(filename: str, mime: str | None = None) -> Converter | None:
    """Find the converter for a file by MIME type, then extension."""
    if mime:
        match = _BY_MIME.get(mime.lower())
        if match is not None:
            return match
    ext = os.path.splitext(filename)[1].lower()
    return _BY_EXT.get(ext)


def supported() -> list[dict]:
    """Return the catalog of known formats for the API/frontend."""
    return [
        {
            "name": c.name,
            "extensions": list(c.extensions),
            "mime_types": list(c.mime_types),
            "implemented": c.implemented,
        }
        for c in _REGISTERED
    ]


def accepted_extensions(implemented_only: bool = False) -> list[str]:
    """Return the sorted list of registered extensions."""
    exts = {
        ext
        for c in _REGISTERED
        if c.implemented or not implemented_only
        for ext in c.extensions
    }
    return sorted(exts)


def clear() -> None:
    """Reset the registry. Intended for tests."""
    _BY_EXT.clear()
    _BY_MIME.clear()
    _REGISTERED.clear()
