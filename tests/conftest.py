"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_pdf_bytes() -> bytes:
    return (FIXTURES / "sample_text.pdf").read_bytes()


@pytest.fixture(scope="session")
def expected_markdown() -> str:
    return (FIXTURES / "sample_text.expected.md").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def docx_bytes() -> bytes:
    return (FIXTURES / "sample.docx").read_bytes()


@pytest.fixture(scope="session")
def xlsx_bytes() -> bytes:
    return (FIXTURES / "sample.xlsx").read_bytes()


@pytest.fixture(scope="session")
def pptx_bytes() -> bytes:
    return (FIXTURES / "sample.pptx").read_bytes()


@pytest.fixture(scope="session")
def html_bytes() -> bytes:
    return (FIXTURES / "sample.html").read_bytes()


@pytest.fixture(scope="session")
def scanned_pdf_bytes() -> bytes:
    return (FIXTURES / "scanned.pdf").read_bytes()
