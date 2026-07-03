# OpenScoreAI - Lanzador de escritorio.
# Arranca el servidor (si no está ya corriendo) y abre la app en el navegador.
$ErrorActionPreference = "SilentlyContinue"

$root = Split-Path -Parent $PSScriptRoot          # …\OpenScoreAI
$py   = Join-Path $root ".venv\Scripts\python.exe"
$url  = "http://127.0.0.1:8000"

function Test-Up {
    try { Invoke-WebRequest -Uri "$url/health" -TimeoutSec 1 -UseBasicParsing | Out-Null; return $true }
    catch { return $false }
}

if (-not (Test-Up)) {
    # Arrancar uvicorn en una ventana minimizada (ciérrala para detener el servidor).
    Start-Process -FilePath $py `
        -ArgumentList @("-m", "uvicorn", "backend.api.main:app", "--app-dir", $root, "--port", "8000") `
        -WorkingDirectory $root `
        -WindowStyle Minimized

    # Esperar hasta que responda (máx ~15 s).
    for ($i = 0; $i -lt 30; $i++) {
        if (Test-Up) { break }
        Start-Sleep -Milliseconds 500
    }
}

# Abrir la app en el navegador por defecto.
Start-Process $url
