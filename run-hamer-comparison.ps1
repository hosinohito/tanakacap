param([string]$Common = 'results/comparisons/first-take')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot 'assets-source/hamer/venv/Scripts/python.exe'
$taskReport = Get-Content -Raw -Encoding UTF8 (Join-Path $Common 'report.json') | ConvertFrom-Json
if ($taskReport.status -ne 'complete') { throw 'Complete baseline comparison required.' }
$taskOutput = Join-Path $PSScriptRoot ('results/comparisons/hamer-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& $taskPython tools/compare_external_model.py hamer --repo assets-source/hamer/repo --checkpoint assets-source/hamer/_DATA/hamer_ckpts/checkpoints/hamer.ckpt --mano-dir assets-source/hamer/mano --mean-params assets-source/hamer/_DATA/data/mano_mean_params.npz --take $taskReport.take --common $Common --output $taskOutput
if ($LASTEXITCODE -ne 0) { throw 'HaMeR inference failed.' }
& '.\.venv\Scripts\python.exe' tools/compare_hamer_fingers.py --common $Common --candidate $taskOutput --output (Join-Path $taskOutput 'fingers')
if ($LASTEXITCODE -ne 0) { throw 'Finger comparison failed.' }
Write-Output $taskOutput
