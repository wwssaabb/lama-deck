param(
    [string]$OutDir = (Join-Path $PSScriptRoot "..\backend\models"),
    [string]$Url = "https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$dest = Join-Path $OutDir "big-lama.pt"

if (Test-Path $dest) {
    Write-Host "Model already exists: $dest"
    exit 0
}

Write-Host "Downloading LaMa weights (big-lama.pt) ..."
$tmp = "$dest.part"
Invoke-WebRequest -Uri $Url -OutFile $tmp -UseBasicParsing
Move-Item -Force $tmp $dest

$size = [math]::Round((Get-Item $dest).Length / 1MB, 1)
Write-Host "Saved: $dest ($size MB)"
Write-Host ""
Write-Host "Usage:"
Write-Host "  `$env:LAMA_MODEL = `"$dest`""
Write-Host "  # or start the backend with scripts in backend/run.ps1 which set it for you"
