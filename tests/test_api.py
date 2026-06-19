"""End-to-end API tests via FastAPI's TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_formats_lists_supported_types():
    resp = client.get("/api/formats")
    assert resp.status_code == 200
    names = {f["name"]: f for f in resp.json()}
    for fmt in ("pdf", "word", "excel", "powerpoint", "html"):
        assert names[fmt]["implemented"] is True


def test_convert_pdf_ok(sample_pdf_bytes):
    resp = client.post(
        "/api/convert",
        files={"file": ("sample_text.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Markdown Converter Test Document" in body["markdown"]
    assert body["filename"] == "sample_text.pdf"


def test_convert_unsupported_type():
    resp = client.post(
        "/api/convert",
        files={"file": ("notes.xyz", b"hello", "application/octet-stream")},
    )
    assert resp.status_code == 415


def test_convert_docx_ok(docx_bytes):
    resp = client.post(
        "/api/convert",
        files={
            "file": (
                "sample.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document",
            )
        },
    )
    assert resp.status_code == 200
    assert "Quarterly Report" in resp.json()["markdown"]


def test_convert_oversize_returns_413(monkeypatch):
    from dataclasses import replace

    # settings is a frozen dataclass; patch the name the orchestrator resolves.
    monkeypatch.setattr(
        "app.orchestrator.settings", replace(settings, max_file_bytes=10)
    )
    resp = client.post(
        "/api/convert",
        files={"file": ("big.pdf", b"x" * 100, "application/pdf")},
    )
    assert resp.status_code == 413


def test_batch_mixed_results(sample_pdf_bytes):
    resp = client.post(
        "/api/convert/batch",
        files=[
            ("files", ("sample_text.pdf", sample_pdf_bytes, "application/pdf")),
            ("files", ("broken.pdf", b"not a pdf", "application/pdf")),
        ],
    )
    assert resp.status_code == 200
    results = {r["filename"]: r for r in resp.json()["results"]}
    assert results["sample_text.pdf"]["status"] == "ok"
    assert results["broken.pdf"]["status"] == "error"
