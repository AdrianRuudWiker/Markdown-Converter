"""HTTP API routes.

All routes are under ``/api``. Conversion output is returned in the JSON
response and never persisted server-side; the browser builds the downloadable
``.md`` file client-side.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, UploadFile

from app.config import settings
from app.converters import registry
from app.errors import MarkdownConverterError
from app.models import (
    BatchItem,
    BatchResponse,
    ConvertResponse,
    FormatInfo,
    HealthResponse,
)
from app.orchestrator import convert as convert_bytes

# Log outcomes only — never document contents, and avoid logging full
# filenames at info level since even FIN filenames can be sensitive.
logger = logging.getLogger("markdown_converter")

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=settings.version)


@router.get("/formats", response_model=list[FormatInfo])
async def formats() -> list[FormatInfo]:
    return [FormatInfo(**f) for f in registry.supported()]


@router.post("/convert", response_model=ConvertResponse)
async def convert_one(file: UploadFile = File(...)) -> ConvertResponse:
    data = await file.read()
    result = await convert_bytes(data, file.filename or "upload", file.content_type)
    logger.info("converted file (%d bytes) -> ok", len(data))
    return ConvertResponse(
        filename=result.source_filename,
        markdown=result.markdown,
        warnings=result.warnings,
        metadata=result.metadata,
    )


@router.post("/convert/batch", response_model=BatchResponse)
async def convert_batch(
    files: list[UploadFile] = File(...),
) -> BatchResponse:
    items: list[BatchItem] = []
    for file in files[: settings.max_batch_files]:
        name = file.filename or "upload"
        data = await file.read()
        try:
            result = await convert_bytes(data, name, file.content_type)
            items.append(
                BatchItem(
                    filename=name,
                    status="ok",
                    markdown=result.markdown,
                    warnings=result.warnings,
                )
            )
        except MarkdownConverterError as exc:
            items.append(BatchItem(filename=name, status="error", error=str(exc)))
    return BatchResponse(results=items)
