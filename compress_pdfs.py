#!/usr/bin/env python3
"""
compress_pdfs.py - Compress large PDF reports down to their essence using AI.

Pipeline per PDF:
  1. Extract the document as Markdown (text + tables) with PyMuPDF4LLM.
     Images and binary overhead are dropped; tables survive as Markdown tables.
  2. Split the Markdown into chunks without ever cutting a table in half.
  3. Send each chunk to Claude with instructions to distil the prose down to
     its essence while keeping every table verbatim and the relevant context
     around it.
  4. Reassemble the distilled chunks into one .md file per input PDF.

The result is typically 10-100x smaller than the source PDF while retaining
all tables and the information that matters.

Input can be a single PDF, a directory of PDFs, or a .zip archive of PDFs.

Set your API key first:   export ANTHROPIC_API_KEY=sk-ant-...
Example:                  python compress_pdfs.py reports.zip -o compressed/
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import zipfile
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Default model: good balance of quality and cost for large volumes.
# Override with --model (e.g. claude-opus-4-8 for max quality,
# claude-haiku-4-5-20251001 for lowest cost).
DEFAULT_MODEL = "claude-sonnet-4-6"

# Roughly characters-per-token for English prose. Used only for chunk sizing
# and cost estimation.
CHARS_PER_TOKEN = 4

# Approximate USD price per 1M tokens (input, output). For cost estimates only;
# these change over time, so verify current rates at anthropic.com/pricing.
PRICING = {
    "claude-opus-4-8": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
}

# Distilled output is assumed to be ~40% the size of the input, for estimating
# output-token cost before we actually run.
ASSUMED_OUTPUT_RATIO = 0.4

SYSTEM_PROMPT = """\
You are a document compressor. You distil long report sections down to their \
essence while losing nothing that matters.

Hard rules:
- Reproduce EVERY table EXACTLY as given, verbatim, in Markdown. Never drop, \
summarize, merge, reword, or reorder table rows, columns, headers, or cell \
values. Numbers and figures are sacred.
- Keep the context immediately around each table (what it shows, units, \
caveats, key takeaways) so the table is still understandable on its own.
- Aggressively cut: boilerplate, repetition, filler, legal/standard \
disclaimers, image descriptions, decorative prose, and anything restating \
something already said.
- Keep: all concrete facts, figures, dates, names, findings, conclusions, \
and the logical structure (headings).
- Preserve heading structure (#, ##, ...) so the document stays navigable.

Output ONLY the compressed Markdown for this section. No preamble, no \
commentary, no "Here is...". If a section is already pure data/tables, return \
it essentially unchanged."""

USER_TEMPLATE = """\
Compress the following report section to its essence following your rules. \
Remember: tables verbatim, prose distilled, structure preserved.

--- SECTION START ---
{chunk}
--- SECTION END ---"""


def collect_pdfs(input_path: Path, workdir: Path) -> list[Path]:
    """Resolve the input into a flat list of PDF paths.

    Handles a single .pdf, a directory (recursive), or a .zip archive.
    """
    if not input_path.exists():
        sys.exit(f"Input not found: {input_path}")

    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        extract_dir = workdir / "unzipped"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(input_path) as zf:
            zf.extractall(extract_dir)
        return sorted(extract_dir.rglob("*.pdf"))

    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]

    if input_path.is_dir():
        return sorted(input_path.rglob("*.pdf"))

    sys.exit(f"Unsupported input (need a .pdf, a folder, or a .zip): {input_path}")


def strip_images(markdown: str) -> str:
    """Remove Markdown image references; we keep no pictures."""
    out_lines = []
    for line in markdown.splitlines():
        stripped = line.strip()
        # Drop standalone image lines like ![](...) or ![alt](path)
        if stripped.startswith("![") and stripped.endswith(")"):
            continue
        out_lines.append(line)
    return "\n".join(out_lines)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def chunk_markdown(markdown: str, max_tokens: int) -> list[str]:
    """Split Markdown into chunks under max_tokens without splitting tables.

    Blocks are separated by blank lines. A Markdown table is a run of lines
    that all start with '|' and contains no blank line, so it stays intact as
    a single block. Oversized blocks (e.g. a huge table) are kept whole.
    """
    blocks = markdown.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        block_tokens = estimate_tokens(block)
        if current and current_tokens + block_tokens > max_tokens:
            chunks.append("\n\n".join(current))
            current = []
            current_tokens = 0
        current.append(block)
        current_tokens += block_tokens

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def distill_chunk(client, model: str, chunk: str, max_retries: int = 5) -> str:
    """Send one chunk to Claude and return the distilled Markdown.

    Retries with exponential backoff on transient/rate-limit errors.
    """
    import anthropic

    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": USER_TEMPLATE.format(chunk=chunk)}],
            )
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"    API error ({type(e).__name__}); retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def extract_and_chunk(pdf_path: Path, max_chunk_tokens: int) -> list[str]:
    """Extract a PDF to image-stripped Markdown and split it into chunks."""
    import pymupdf4llm

    raw_md = pymupdf4llm.to_markdown(str(pdf_path), show_progress=False)
    raw_md = strip_images(raw_md)
    return chunk_markdown(raw_md, max_chunk_tokens)


def estimate_cost(total_input_tokens: int, model: str) -> tuple[float, str]:
    """Return (approx_usd, human_readable) for distilling the given tokens.

    Output tokens are assumed to be ASSUMED_OUTPUT_RATIO of input. Pricing is
    approximate. Unknown models return a 0 cost with a note.
    """
    if model not in PRICING:
        return 0.0, f"~? (no pricing on file for {model}; verify at anthropic.com/pricing)"
    in_rate, out_rate = PRICING[model]
    out_tokens = total_input_tokens * ASSUMED_OUTPUT_RATIO
    usd = (total_input_tokens * in_rate + out_tokens * out_rate) / 1_000_000
    return usd, f"~${usd:.2f} (approx; verify at anthropic.com/pricing)"


def distill_chunks(chunks: list[str], client, model: str, workers: int, progress) -> str:
    """Distil all chunks (optionally in parallel) and reassemble in order."""
    results: list[str] = [""] * len(chunks)

    def work(idx_chunk):
        idx, chunk = idx_chunk
        out = distill_chunk(client, model, chunk)
        if progress is not None:
            progress.update(1)
        return idx, out

    if workers > 1 and len(chunks) > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for idx, distilled in ex.map(work, enumerate(chunks)):
                results[idx] = distilled
    else:
        for pair in enumerate(chunks):
            idx, distilled = work(pair)
            results[idx] = distilled

    return ("\n\n".join(r for r in results if r)).strip() + "\n"


class _NullBar:
    """Minimal stand-in for tqdm when it isn't installed."""

    def __init__(self, iterable=None, **kwargs):
        self._it = iterable

    def __iter__(self):
        return iter(self._it or [])

    def update(self, n=1):
        pass

    def close(self):
        pass

    @staticmethod
    def write(msg):
        print(msg)


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compress PDF reports to their essence (Markdown) using AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="A .pdf file, a folder of PDFs, or a .zip archive.")
    parser.add_argument("-o", "--output", type=Path, default=Path("compressed"),
                        help="Output directory for .md files (default: ./compressed).")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Claude model (default: {DEFAULT_MODEL}).")
    parser.add_argument("--max-chunk-tokens", type=int, default=6000,
                        help="Approx tokens per chunk sent to the model (default: 6000).")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel API requests per document (default: 4).")
    parser.add_argument("--no-distill", action="store_true",
                        help="Skip the AI step: extract text+tables to Markdown only (no API key needed).")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Skip the cost-estimate confirmation prompt.")
    args = parser.parse_args()

    # tqdm is optional; degrade gracefully to a no-op bar if not installed.
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = _NullBar

    client = None
    if not args.no_distill:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set. Export it, or use --no-distill for extract-only.")
        import anthropic
        client = anthropic.Anthropic()

    workdir = Path(tempfile.mkdtemp(prefix="pdf-compress-"))
    try:
        pdfs = collect_pdfs(args.input, workdir)
        if not pdfs:
            sys.exit("No PDF files found in the input.")

        print(f"Found {len(pdfs)} PDF(s). Mode: "
              f"{'extract-only' if args.no_distill else f'AI distillation ({args.model})'}\n")

        # Phase 1: extract + chunk every PDF (local, cheap), keeping originals.
        jobs = []  # (pdf, out_path, chunks, orig_size)
        total_chunks = 0
        total_input_tokens = 0
        for pdf in tqdm(pdfs, desc="Extracting", unit="pdf"):
            try:
                chunks = extract_and_chunk(pdf, args.max_chunk_tokens)
            except Exception as e:  # noqa: BLE001 - keep going on a bad file
                print(f"  FAILED to read {pdf.name}: {e}", file=sys.stderr)
                continue
            out_path = args.output / (pdf.stem + ".md")
            jobs.append((pdf, out_path, chunks, pdf.stat().st_size))
            total_chunks += len(chunks)
            total_input_tokens += sum(estimate_tokens(c) for c in chunks)

        if not jobs:
            sys.exit("No PDFs could be read.")

        # Cost estimate + confirmation (distill mode only).
        if not args.no_distill:
            _, cost_str = estimate_cost(total_input_tokens, args.model)
            print(f"\n{len(jobs)} document(s), {total_chunks} chunk(s), "
                  f"~{total_input_tokens:,} input tokens.")
            print(f"Estimated API cost: {cost_str}\n")
            if not args.yes:
                reply = input("Proceed with the AI distillation? [y/N] ").strip().lower()
                if reply not in ("y", "yes"):
                    sys.exit("Aborted before any API calls were made.")

        # Phase 2: distill (or just write, in extract-only mode) + report sizes.
        total_in = total_out = 0
        bar = tqdm(total=total_chunks, desc="Distilling", unit="chunk") \
            if not args.no_distill else None
        for pdf, out_path, chunks, orig in jobs:
            try:
                if args.no_distill:
                    final_md = ("\n\n".join(chunks)).strip() + "\n"
                else:
                    final_md = distill_chunks(chunks, client, args.model, args.workers, bar)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(final_md, encoding="utf-8")
                comp = out_path.stat().st_size
            except Exception as e:  # noqa: BLE001 - keep going on a bad file
                print(f"\n  FAILED on {pdf.name}: {e}", file=sys.stderr)
                continue
            total_in += orig
            total_out += comp
            ratio = (orig / comp) if comp else 0
            tqdm.write(f"  {pdf.name}: {human(orig)} -> {human(comp)} "
                       f"({ratio:.0f}x)  -> {out_path}")
        if bar is not None:
            bar.close()

        print(f"\nDone. Total: {human(total_in)} -> {human(total_out)}", end="")
        if total_out:
            print(f"  ({total_in / total_out:.0f}x smaller overall)")
        else:
            print()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
