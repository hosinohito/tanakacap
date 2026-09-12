param([string]$Avatar,[ValidateSet(720,1080)][int]$OutputHeight=720,
    [switch]$NoEdgeAA)
$ErrorActionPreference='Stop'
$taskExe=Join-Path $PSScriptRoot 'builds/lab/TanakaCap.exe'
if (-not (Test-Path -LiteralPath $taskExe)) { throw 'Run build-unity-lab.ps1 first.' }
$taskArgs=@('--motion-demo','-nolog')
$taskArgs+=@('--output-height',$OutputHeight.ToString())
if ($NoEdgeAA) { $taskArgs+='--no-edge-aa' }
if ($Avatar) { $taskArgs+=@('--avatar',('"'+(Resolve-Path -LiteralPath $Avatar).Path+'"')) }
# The visible Player is the requested interactive window. No camera or capture process.
$taskProcess=Start-Process -FilePath $taskExe -ArgumentList $taskArgs -WorkingDirectory $PSScriptRoot -PassThru -Wait
if ($taskProcess.ExitCode -ne 0) { throw "Avatar exited with code $($taskProcess.ExitCode)" }
