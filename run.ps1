# One-command launcher for Windows (the likely FIN environment).
# Creates a venv, installs deps, and starts the local server.
$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$venv = ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venv
}

& "$venv\Scripts\Activate.ps1"

Write-Host "Installing dependencies..."
if (Test-Path "wheelhouse") {
    # Offline install path for machines with no internet access.
    pip install --quiet --no-index --find-links wheelhouse -e .
} else {
    pip install --quiet -e .
}

$envHost = if ($env:MDC_HOST) { $env:MDC_HOST } else { "127.0.0.1" }
$port = if ($env:MDC_PORT) { $env:MDC_PORT } else { "8000" }
Write-Host ""
Write-Host "Markdown-Converter is starting at http://${envHost}:${port}"
Write-Host "Press Ctrl+C to stop."
uvicorn app.main:app --host $envHost --port $port
