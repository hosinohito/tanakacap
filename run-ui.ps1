param([switch]$DemoAvatar)
$ErrorActionPreference='Stop'
$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/pythonw.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run setup.ps1 first.' }
$taskUiArgs=@('-m','tanakacap.control_panel')
if ($DemoAvatar) { $taskUiArgs+='--demo-avatar' }
Start-Process -FilePath $taskPython -ArgumentList $taskUiArgs -WorkingDirectory $PSScriptRoot
