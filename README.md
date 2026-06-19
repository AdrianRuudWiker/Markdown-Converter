# Markdown-Converter

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/AdrianRuudWiker/Markdown-Converter)

A drag-and-drop web app that converts documents to Markdown. **Designed to run in
GitHub Codespaces** — open it in your browser, drop a file, get Markdown back.

## What it converts

| Type        | Notes                                                        |
| ----------- | ------------------------------------------------------------ |
| PDF         | Text PDFs directly; **scanned / image-only PDFs via OCR** automatically |
| Word        | `.docx`, `.doc`                                              |
| Excel       | `.xlsx`, `.xls` — becomes Markdown tables                    |
| PowerPoint  | `.pptx`, `.ppt`                                              |
| HTML        | `.html`, `.htm`                                              |

Drop one file or many at once, then preview, copy, or download each as `.md`.

## Run it in GitHub Codespaces

1. Click the **Open in GitHub Codespaces** badge above. (Or, on the repo page,
   **Code → Codespaces → Create codespace** on this branch.)
2. Wait for the Codespace to finish building — it installs everything for you,
   including the OCR tools for scanned PDFs. The first build takes a few minutes.
3. The app **starts automatically** and opens in a preview tab on port **8000**.
   That's it — drag a file in.

**If the app doesn't open by itself:**
- Open the **Ports** tab (bottom panel) and click the globe icon next to port 8000, or
- Run it from the terminal:
  ```bash
  ./run.sh
  ```
- To restart it from the menu: **Terminal → Run Task… → Run Markdown-Converter**.

> **Note on sensitive documents.** In a Codespace, files are processed in a
> GitHub-hosted cloud container — not on your local machine. The app itself makes
> no outbound network calls during conversion, but the container is in the cloud.
> For documents that must never leave your premises, run it locally instead
> (see below).

## Run it on your own machine (fully local)

Requires Python 3.11+. From the project folder:

```bash
./run.sh        # macOS / Linux
.\run.ps1       # Windows (PowerShell)
```

Then open <http://127.0.0.1:8000>. Press `Ctrl+C` to stop.

The launcher creates a virtual environment, installs dependencies, and starts the
server. For **OCR of scanned PDFs** when running locally, also install Tesseract
(with the `nor` and `eng` language packs) and Poppler:

```bash
# Debian / Ubuntu
sudo apt-get install -y tesseract-ocr tesseract-ocr-nor tesseract-ocr-eng poppler-utils
```

(On Windows, install the Tesseract and Poppler binaries and ensure they are on your
`PATH`.) Without these, text PDFs and all office formats still work; only scanned-PDF
OCR is unavailable, and the app says so clearly.

### Offline / air-gapped install

On a machine with internet, download the wheels into a `wheelhouse/` folder:

```bash
pip download -d wheelhouse -e .
```

Copy the project (including `wheelhouse/`) to the offline machine. The launcher
detects `wheelhouse/` and installs with `--no-index`, so no internet is needed.
(OCR system packages must be installed separately on the offline machine.)

## Privacy

- The conversion engine (Microsoft MarkItDown, MIT-licensed) and OCR (Tesseract +
  Poppler) run **locally with no LLM client and no API key** — no outbound network
  access during conversion. A test (`tests/test_offline.py`) enforces this.
- No third-party CDNs; all frontend assets are served locally.
- Converted output is never persisted server-side; the `.md` file is built in your
  browser.
- When bound to `127.0.0.1` (the default), the server is not exposed to the network.

## Configuration

All optional, via environment variables:

| Variable                | Default     | Meaning                                  |
| ----------------------- | ----------- | ---------------------------------------- |
| `MDC_HOST`              | `127.0.0.1` | Bind address.                            |
| `MDC_PORT`              | `8000`      | Port.                                    |
| `MDC_MAX_FILE_BYTES`    | `52428800`  | Max upload size per file (50 MB).        |
| `MDC_CONVERT_TIMEOUT_S` | `120`       | Per-file conversion timeout (seconds).   |
| `MDC_MAX_BATCH_FILES`   | `50`        | Max files per batch request.             |
| `MDC_OCR_LANG`          | `nor+eng`   | Tesseract language(s) for scanned PDFs.  |
| `MDC_OCR_DPI`           | `300`       | Render resolution before OCR.            |

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest          # run the test suite
ruff check .    # lint
```

OCR tests are skipped automatically if Tesseract/Poppler are not installed.
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
    pdf_text.py      PDF -> Markdown (text, with automatic OCR fallback)
    ocr.py           local OCR for scanned PDFs (Tesseract + Poppler)
    generic.py       Word / Excel / PowerPoint / HTML via MarkItDown
    __init__.py      registers all converters at startup
static/              drag-and-drop frontend (vanilla HTML/CSS/JS)
tests/               registry, converter, OCR, API, and offline-guarantee tests
```

## Adding a format

1. For most file types, add a `MarkItDownConverter(...)` in `app/converters/generic.py`
   with the right extensions/MIME types and file-extension hint.
2. Register it in `app/converters/__init__.py`.

The frontend picks up the new format automatically from `/api/formats`.

## License

This project is intended for internal use. The conversion engine (Microsoft
MarkItDown) is MIT-licensed; Tesseract and Poppler are open source.
