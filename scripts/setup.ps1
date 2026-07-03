# OpenScoreAI - Setup reproducible del entorno (Windows / PowerShell)
# Uso:  .\scripts\setup.ps1
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "==> Creando entorno virtual (.venv)..." -ForegroundColor Cyan
if (-not (Test-Path $py)) { python -m venv (Join-Path $root ".venv") }

Write-Host "==> Actualizando pip / setuptools / wheel..." -ForegroundColor Cyan
& $py -m pip install --quiet --upgrade pip setuptools wheel

Write-Host "==> Instalando dependencias base (requirements.txt)..." -ForegroundColor Cyan
& $py -m pip install --quiet -r (Join-Path $root "requirements.txt")

Write-Host "==> Instalando Basic Pitch (--no-deps, backend ONNX)..." -ForegroundColor Cyan
& $py -m pip install --quiet --no-deps basic-pitch

Write-Host "==> Verificando..." -ForegroundColor Cyan
& $py -c "from basic_pitch.inference import predict; import onnxruntime; print('OK - entorno listo, ONNX', onnxruntime.__version__)"

Write-Host "`nListo. Arranca la API con:" -ForegroundColor Green
Write-Host "   .venv\Scripts\python.exe -m uvicorn backend.api.main:app --reload" -ForegroundColor Green
