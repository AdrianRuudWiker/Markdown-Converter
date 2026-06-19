"""Privacy guard: conversion must make no network connections.

If a future change (or a misconfigured engine) tried to call out to a remote
service, these tests would fail — protecting the "no files leave this
computer" guarantee for sensitive documents.
"""

from __future__ import annotations

import socket

import pytest

from app.converters.pdf_text import PdfTextConverter


@pytest.fixture
def block_network(monkeypatch):
    def _blocked(*args, **kwargs):
        raise AssertionError("Network access attempted during conversion!")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


def test_pdf_conversion_makes_no_network_calls(block_network, sample_pdf_bytes):
    # Construct the converter inside the test so engine setup is also covered.
    result = PdfTextConverter().convert(sample_pdf_bytes, "sample_text.pdf")
    assert result.markdown
