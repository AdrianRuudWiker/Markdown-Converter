# Markdown-Converter

Compress large PDF reports down to their **essence** using AI, while keeping
**every table verbatim** and the relevant context around it. Pictures and
filler are dropped. Output is one Markdown (`.md`) file per PDF — typically
**10–100x smaller** than the source.

This was built for compressing a big pile of FIN reports, but works on any
PDFs.

## How it works

For each PDF:

1. **Extract** the document to Markdown (text + tables) with PyMuPDF4LLM.
   Images and PDF binary overhead are dropped; tables become Markdown tables.
2. **Chunk** the Markdown without ever splitting a table.
3. **Distil** each chunk with Claude: prose is cut down to its essence, but
   tables are reproduced exactly and the context around them is kept.
4. **Reassemble** into one `.md` per PDF.

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

Results land in `compressed/`, one `.md` per input PDF, with a size summary
printed at the end.

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output` | `compressed/` | Output directory for `.md` files. |
| `--model` | `claude-sonnet-4-6` | Claude model. Use `claude-opus-4-8` for max quality, `claude-haiku-4-5-20251001` for lowest cost. |
| `--max-chunk-tokens` | `6000` | Approx tokens per chunk sent to the model. |
| `--workers` | `4` | Parallel API requests per document. |
| `--no-distill` | off | Skip AI: just extract text + tables to Markdown. **No API key needed.** Fully lossless on text, big size win, no summarizing. |

### Tip: try one first

Run on a single report and eyeball the `.md` before processing the whole zip,
so you're happy with how aggressively prose is cut. `--no-distill` is a free,
no-key way to see the pure extraction baseline.

## Notes

- The AI step is **lossy on prose** by design (that's the compression) but
  **lossless on tables** — they are copied verbatim. Always keep your original
  PDFs.
- Cost scales with input size and the chosen model. Sonnet is a good balance
  for large volumes; switch with `--model`.
- A single bad/corrupt PDF is reported and skipped; the rest still process.
