"""Conversion orchestration: resolve -> run in a threadpool -> enforce timeout.

The orchestrator is the one place that knows how to turn raw upload bytes into
a :class:`ConversionResult`. It keeps data in memory, runs the (CPU-bound,
possibly blocking) converter off the event loop, and bounds each conversion
with a timeout so a malformed or huge file can't hang the server.
"""

from __future__ import annotations

import anyio

from app.config import settings
from app.converters import registry
from app.converters.base import ConversionResult
from app.errors import (
    ConversionTimeoutError,
    FileTooLargeError,
    UnsupportedFormatError,
)


async def convert(data: bytes, filename: str, mime: str | None) -> ConversionResult:
    """Convert one file's bytes to Markdown, applying limits and timeouts."""
    if len(data) > settings.max_file_bytes:
        mb = settings.max_file_bytes / (1024 * 1024)
        raise FileTooLargeError(
            f"'{filename}' exceeds the {mb:.0f} MB limit."
        )

    converter = registry.resolve(filename, mime)
    if converter is None:
        raise UnsupportedFormatError(
            f"No converter available for '{filename}'."
        )

    try:
        with anyio.fail_after(settings.convert_timeout_s):
            # Run the blocking converter in a worker thread so the event loop
            # stays responsive.
            return await anyio.to_thread.run_sync(
                converter.convert, data, filename
            )
    except TimeoutError as exc:
        raise ConversionTimeoutError(
            f"Converting '{filename}' took too long and was stopped."
        ) from exc
