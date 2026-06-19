"""FastAPI application entry point.

Serves the static drag-and-drop frontend and the ``/api`` routes. Importing
:mod:`app.converters` registers every converter at startup.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import app.converters  # noqa: F401 - registers converters on import
from app.api import router
from app.config import settings
from app.errors import MarkdownConverterError

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="Markdown-Converter",
    version=settings.version,
    description="Fully-local document-to-Markdown converter.",
)

app.include_router(router)


@app.exception_handler(MarkdownConverterError)
async def _domain_error_handler(
    request: Request, exc: MarkdownConverterError
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


# Mount static assets last so it doesn't shadow the API routes.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


def run() -> None:
    """Launch the server bound to localhost. Used by ``python -m app.main``."""
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    run()
