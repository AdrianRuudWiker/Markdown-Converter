# Markdown-Converter

Take big PDF reports and produce a **small, compressed PDF** of each — distilled
to its **essence** by AI, with **every table kept verbatim** and the relevant
context around it. Pictures and filler are dropped. Output is typically
**10–100x smaller** than the source (a 4 MB image-heavy report compresses to
~25 KB). Markdown output is also available via `--format`.

This was built for compressing a big pile of FIN reports, but works on any
PDFs.

## How it works

For each PDF:

1. **Extract** the document to Markdown (text + tables) with PyMuPDF4LLM.
   Images and PDF binary overhead are dropped; tables become Markdown tables.
2. **Chunk** the Markdown without ever splitting a table.
3. **Distil** each chunk with Claude: prose is cut down to its essence, but
   tables are reproduced exactly and the context around them is kept.
4. **Render** the result back to a compact, text-based PDF (one per input).
   Bundled DejaVu fonts ensure Norwegian and typographic characters render
   correctly. Pass `--format md` for Markdown instead, or `both`.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...     # get one at console.anthropic.com
```

## Usage

```bash
# A whole zip of reports (e.g. the one from your desktop)
python compress_pdfs.py ~/Desktop/reports.zip -o compressed/

# A folder of PDFs
python compress_pdfs.py ./my_reports -o compressed/

# A single PDF
python compress_pdfs.py report.pdf -o compressed/
```

Results land in `compressed/`, one compressed `.pdf` per input PDF, with a size
summary printed at the end.

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output` | `compressed/` | Output directory. |
| `-f, --format` | `pdf` | Output format: `pdf`, `md`, or `both`. |
| `--model` | `claude-sonnet-4-6` | Claude model. Use `claude-opus-4-8` for max quality, `claude-haiku-4-5-20251001` for lowest cost. |
| `--max-chunk-tokens` | `6000` | Approx tokens per chunk sent to the model. |
| `--workers` | `4` | Parallel API requests per document. |
| `--no-distill` | off | Skip AI: just extract text + tables to Markdown. **No API key needed.** Fully lossless on text, big size win, no summarizing. |
| `-y, --yes` | off | Skip the cost-estimate confirmation prompt (for unattended runs). |

### Cost estimate before it runs

Before any API calls, the tool extracts everything locally, then prints how
many documents, chunks and input tokens it found and an **approximate USD
cost**, and waits for you to confirm. Nothing is sent to the API until you say
yes (or you pass `-y`). Pricing is approximate — verify current rates at
anthropic.com/pricing.

### Tip: try one first

Run on a single report and eyeball the output before processing the whole zip,
so you're happy with how aggressively prose is cut. `--no-distill` is a free,
no-key way to see the pure extraction baseline.

## Notes

- The AI step is **lossy on prose** by design (that's the compression) but
  **lossless on tables** — they are copied verbatim. Always keep your original
  PDFs.
- Cost scales with input size and the chosen model. Sonnet is a good balance
  for large volumes; switch with `--model`.
- A single bad/corrupt PDF is reported and skipped; the rest still process.
