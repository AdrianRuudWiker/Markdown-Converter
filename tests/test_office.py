"""Office and HTML format conversions via the generic MarkItDown converter."""

from __future__ import annotations

from app.converters import generic


def test_docx_to_markdown(docx_bytes):
    result = generic.word_converter().convert(docx_bytes, "sample.docx")
    assert "Quarterly Report" in result.markdown
    assert "Revenue increased" in result.markdown


def test_xlsx_to_markdown_table(xlsx_bytes):
    result = generic.excel_converter().convert(xlsx_bytes, "sample.xlsx")
    # Spreadsheets become Markdown tables.
    assert "Revenue" in result.markdown
    assert "|" in result.markdown


def test_pptx_to_markdown(pptx_bytes):
    result = generic.powerpoint_converter().convert(pptx_bytes, "sample.pptx")
    assert "Quarterly Report" in result.markdown


def test_html_to_markdown(html_bytes):
    result = generic.html_converter().convert(html_bytes, "sample.html")
    assert "# Quarterly Report" in result.markdown
    assert "Revenue increased" in result.markdown
