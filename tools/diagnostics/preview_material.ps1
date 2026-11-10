param([Parameter(Mandatory=$true)][string]$Avatar)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskPlayer=Join-Path $taskRoot 'builds/release-player/TanakaCap.exe'
$taskAvatar=(Resolve-Path -LiteralPath $Avatar).Path
if(-not (Test-Path -LiteralPath $taskPlayer)){throw 'Build the release Player first.'}
$taskLogs=Join-Path $taskRoot 'results/material-color'
New-Item -ItemType Directory -Force -Path $taskLogs | Out-Null
# Avatar-only preview: no inference process and no camera access.
$taskArgs=@('--avatar',('"'+$taskAvatar+'"'),'--expression-mode','auto-custom','--render-fps','60','--output-width','1280','--output-height','720','--error-log',('"'+(Join-Path $taskLogs 'preview-errors.log')+'"'),'-logFile',('"'+(Join-Path $taskLogs 'preview.log')+'"'))
Start-Process -FilePath $taskPlayer -ArgumentList $taskArgs -WorkingDirectory $taskRoot -WindowStyle Normal
