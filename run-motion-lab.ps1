param([string]$Avatar,[ValidateRange(64,4096)][int]$OutputHeight=1080,
    [ValidateRange(64,4096)][int]$OutputWidth,
    [switch]$NoPreview,
    [switch]$LegacyPreview,
    [switch]$LegacySecondaryResponse,
    [switch]$NoEdgeAA)
$ErrorActionPreference='Stop'
$taskExe=Join-Path $PSScriptRoot 'builds/lab/TanakaCap.exe'
if (-not (Test-Path -LiteralPath $taskExe)) { throw 'Run build-unity-lab.ps1 first.' }
$taskArgs=@('--motion-demo','-nolog')
$taskArgs+=@('--output-height',$OutputHeight.ToString())
if ($OutputWidth) { $taskArgs+=@('--output-width',$OutputWidth.ToString()) }
if ($NoPreview) { $taskArgs+='--no-preview' }
if ($LegacyPreview) { $taskArgs+='--legacy-preview' }
if ($LegacySecondaryResponse) { $taskArgs+='--legacy-secondary-response' }
if ($NoEdgeAA) { $taskArgs+='--no-edge-aa' }
if ($Avatar) { $taskArgs+=@('--avatar',('"'+(Resolve-Path -LiteralPath $Avatar).Path+'"')) }
# The visible Player is the requested interactive window. No camera or capture process.
$taskProcess=Start-Process -FilePath $taskExe -ArgumentList $taskArgs -WorkingDirectory $PSScriptRoot -PassThru -Wait
if ($taskProcess.ExitCode -ne 0) { throw "Avatar exited with code $($taskProcess.ExitCode)" }
