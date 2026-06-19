# Markdown-Converter

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/AdrianRuudWiker/Markdown-Converter)

A fully-local, drag-and-drop web app that converts documents to Markdown.

Built for use with sensitive Ministry of Finance (Finansdepartementet) documents:
**everything runs on your own machine and no file ever leaves your computer.**

## What it does

- Drop a file in the browser, get clean Markdown back to preview, copy, or download.
- Convert one file or a batch at once.
- **v1 supports text-based PDF.** Word, Excel, PowerPoint, HTML, and scanned-PDF
  OCR are recognized and shown as "coming soon"; enabling them later is a small,
  isolated change (see *Adding a format*).

## Privacy

- Binds to `127.0.0.1` only — never exposed to the network.
- No telemetry, no cloud calls, no third-party CDNs (all frontend assets are local).
- The conversion engine (Microsoft MarkItDown, MIT-licensed) is run with **no LLM
  client and no API key**, so there is no outbound network access during conversion.
  A test (`tests/test_offline.py`) enforces this by failing if any network call is
  attempted while converting.
- Converted output is never persisted server-side; the `.md` file is built in your
  browser.

## Run in GitHub Codespaces (easiest)

1. Click the **Open in GitHub Codespaces** badge above (or, on the repo page,
   **Code → Codespaces → Create codespace**).
2. Wait for the Codespace to finish setting up — it installs everything for you.
3. The app **starts automatically** and a preview of it opens on the forwarded
   port (8000). That's it — drag a PDF in and get Markdown back.

If the preview doesn't pop up, open the **Ports** tab and click the globe icon
next to port 8000, or run the **Run Markdown-Converter** task
(`Terminal → Run Task...`).

## Requirements (local install)

- Python 3.11 or newer.

## Run it locally

**macOS / Linux:**

```bash
./run.sh
```

**Windows:**

```powershell
.\run.ps1
```

Then open <http://127.0.0.1:8000> in your browser.

The launcher creates a virtual environment, installs dependencies, and starts the
server. To stop it, press `Ctrl+C`.

### Offline / air-gapped install

On a machine with internet, download the wheels into a `wheelhouse/` folder:

```bash
pip download -d wheelhouse -e .
```

Copy the project (including `wheelhouse/`) to the offline machine. The launcher
detects `wheelhouse/` and installs with `--no-index`, so no internet is needed.

## Configuration

All optional, via environment variables:

| Variable                | Default     | Meaning                                |
| ----------------------- | ----------- | -------------------------------------- |
| `MDC_HOST`              | `127.0.0.1` | Bind address (keep on localhost).      |
| `MDC_PORT`              | `8000`      | Port.                                  |
| `MDC_MAX_FILE_BYTES`    | `52428800`  | Max upload size per file (50 MB).      |
| `MDC_CONVERT_TIMEOUT_S` | `120`       | Per-file conversion timeout (seconds). |
| `MDC_MAX_BATCH_FILES`   | `50`        | Max files per batch request.           |

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest          # run the test suite
ruff check .    # lint
```

`requirements.lock` holds exact pinned versions for reproducible installs.

## How it's structured

```
app/
  main.py            FastAPI app: serves the frontend and /api routes
  api.py             /api/health, /api/formats, /api/convert, /api/convert/batch
  orchestrator.py    resolve converter -> run in threadpool -> enforce timeout
  config.py          settings (env-overridable)
  errors.py          domain errors and their HTTP status codes
  converters/
    base.py          the Converter interface + ConversionResult
    registry.py      dispatch by MIME type / extension
    pdf_text.py      text PDF -> Markdown (MarkItDown), enabled
    stubs.py         planned formats (word/excel/powerpoint/html)
    __init__.py      registers all converters at startup
static/              drag-and-drop frontend (vanilla HTML/CSS/JS)
tests/               registry, converter, API, and offline-guarantee tests
```

## Adding a format

1. Write a converter class in `app/converters/` implementing the `Converter`
   protocol from `base.py` (set `implemented = True`).
2. Register it in `app/converters/__init__.py` in place of the matching stub.
3. Add the relevant MarkItDown extra to `pyproject.toml` if needed
   (e.g. `markitdown[docx]`).

The frontend picks up the new format automatically from `/api/formats`.

## License

This project is intended for internal use. The conversion engine, Microsoft
MarkItDown, is MIT-licensed.
