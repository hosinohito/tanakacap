param(
    [ValidateSet('rtmw-l-384','dwpose-l-384')][string]$Model = 'rtmw-l-384',
    [int]$Camera = 1,
    [int]$Frames = 1800,
    [switch]$Headless
)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run setup-lab.ps1 first.' }
    $taskArgs = @('-m','capture_lab','benchmark','--source','camera','--model',$Model,
                  '--camera',"$Camera",'--backend','msmf','--frames',"$Frames")
    if (-not $Headless) { $taskArgs += '--preview' }
    & $taskPython @taskArgs
    if ($LASTEXITCODE -ne 0) { throw "Capture lab exited with code $LASTEXITCODE" }
} finally { Pop-Location }
