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
