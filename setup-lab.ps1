param([string]$Python = '3.11')
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv is required for this development setup.' }
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & uv venv .venv --python $Python --cache-dir .cache\uv
        if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
    }
    & uv pip sync --python .venv\Scripts\python.exe --cache-dir .cache\uv requirements-lab.lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & .venv\Scripts\python.exe -m capture_lab fetch rtmw-l-384 dwpose-l-384 yolox-m-human rtmw3d-x-384
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed.' }
} finally { Pop-Location }
