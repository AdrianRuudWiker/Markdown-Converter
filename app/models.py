"""Pydantic response schemas for the API."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class FormatInfo(BaseModel):
    name: str
    extensions: list[str]
    mime_types: list[str]
    implemented: bool


class ConvertResponse(BaseModel):
    filename: str
    markdown: str
    warnings: list[str] = []
    metadata: dict[str, str] = {}


class BatchItem(BaseModel):
    filename: str
    status: str  # "ok" | "error"
    markdown: str | None = None
    error: str | None = None
    warnings: list[str] = []


class BatchResponse(BaseModel):
    results: list[BatchItem]
