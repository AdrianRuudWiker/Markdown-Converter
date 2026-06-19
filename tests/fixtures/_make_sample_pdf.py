"""Generate the committed `sample_text.pdf` test fixture (stdlib only).

Run once to (re)create the fixture:  python tests/fixtures/_make_sample_pdf.py

It builds a minimal, valid, text-based PDF with correct cross-reference byte
offsets so pdfminer (used by MarkItDown) can extract the text reliably.
"""

from __future__ import annotations

from pathlib import Path

LINES = [
    "Markdown Converter Test Document",
    "This is a sample PDF used by the test suite.",
    "It contains selectable text on a single page.",
]


def _content_stream() -> bytes:
    ops = ["BT", "/F1 18 Tf", "72 720 Td"]
    for i, line in enumerate(LINES):
        if i > 0:
            ops.append("0 -28 Td")
        escaped = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        ops.append(f"({escaped}) Tj")
    ops.append("ET")
    return ("\n".join(ops)).encode("latin-1")


def build_pdf() -> bytes:
    content = _content_stream()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i
        out += body
        out += b"\nendobj\n"

    xref_pos = len(out)
    n = len(objects) + 1
    out += b"xref\n"
    out += b"0 %d\n" % n
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off

    out += b"trailer\n"
    out += b"<< /Size %d /Root 1 0 R >>\n" % n
    out += b"startxref\n"
    out += b"%d\n" % xref_pos
    out += b"%%EOF"
    return bytes(out)


if __name__ == "__main__":
    target = Path(__file__).with_name("sample_text.pdf")
    target.write_bytes(build_pdf())
    print(f"Wrote {target} ({target.stat().st_size} bytes)")
