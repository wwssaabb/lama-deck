$ErrorActionPreference = "Stop"

$here = $PSScriptRoot
$python = Join-Path $here ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

$model = Join-Path $here "models\big-lama.pt"
if (Test-Path $model) { $env:LAMA_MODEL = $model }
$env:TORCH_HOME = Join-Path $here ".cache\torch"
if (-not $env:LAMA_DEVICE) { $env:LAMA_DEVICE = "auto" }
if (-not $env:LAMA_ENGINE) { $env:LAMA_ENGINE = "auto" }
$port = if ($env:PORT) { $env:PORT } else { "8000" }

Push-Location $here
try {
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port $port
}
finally {
    Pop-Location
}
