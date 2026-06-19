"""Runtime configuration.

Defaults are safe and local. Everything is overridable via environment
variables (prefix ``MDC_``) so the tool can be tuned without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    #: Bind address. Localhost only by default — never expose to the network.
    host: str = os.environ.get("MDC_HOST", "127.0.0.1")
    port: int = _int_env("MDC_PORT", 8000)

    #: Max upload size per file, in bytes (default 50 MB).
    max_file_bytes: int = _int_env("MDC_MAX_FILE_BYTES", 50 * 1024 * 1024)

    #: Per-file conversion timeout, in seconds.
    convert_timeout_s: int = _int_env("MDC_CONVERT_TIMEOUT_S", 120)

    #: Max number of files accepted in a single batch request.
    max_batch_files: int = _int_env("MDC_MAX_BATCH_FILES", 50)

    #: OCR language(s) for scanned PDFs (Tesseract codes, '+'-separated).
    #: Defaults to Norwegian + English for Ministry of Finance documents.
    ocr_lang: str = os.environ.get("MDC_OCR_LANG", "nor+eng")

    #: Rendering resolution (DPI) used before OCR. Higher = slower but sharper.
    ocr_dpi: int = _int_env("MDC_OCR_DPI", 300)

    version: str = "1.1.0"


settings = Settings()
