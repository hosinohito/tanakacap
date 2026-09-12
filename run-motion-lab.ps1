param([string]$Avatar)
$ErrorActionPreference='Stop'
$taskExe=Join-Path $PSScriptRoot 'builds/lab/TanakaCap.exe'
if (-not (Test-Path -LiteralPath $taskExe)) { throw 'Run build-unity-lab.ps1 first.' }
$taskArgs=@('--motion-demo','-nolog')
if ($Avatar) { $taskArgs+=@('--avatar',('"'+(Resolve-Path -LiteralPath $Avatar).Path+'"')) }
# The visible Player is the requested interactive window. No camera or capture process.
$taskProcess=Start-Process -FilePath $taskExe -ArgumentList $taskArgs -WorkingDirectory $PSScriptRoot -PassThru -Wait
if ($taskProcess.ExitCode -ne 0) { throw "Avatar exited with code $($taskProcess.ExitCode)" }
