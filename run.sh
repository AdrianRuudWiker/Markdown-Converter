#!/usr/bin/env bash
# One-command launcher: create a venv, install deps, start the local server.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV=".venv"

if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment..."
  "$PYTHON" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "Installing dependencies..."
if [ -d "wheelhouse" ]; then
  # Offline install path for machines with no internet access.
  pip install --quiet --no-index --find-links wheelhouse -e .
else
  pip install --quiet -e .
fi

HOST="${MDC_HOST:-127.0.0.1}"
PORT="${MDC_PORT:-8000}"
echo ""
echo "Markdown-Converter is starting at http://${HOST}:${PORT}"
echo "Press Ctrl+C to stop."
exec uvicorn app.main:app --host "$HOST" --port "$PORT"
