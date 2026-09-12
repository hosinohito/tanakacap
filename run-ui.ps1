$ErrorActionPreference='Stop'
$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/pythonw.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run setup-lab.ps1 first.' }
Start-Process -FilePath $taskPython -ArgumentList @('-m','capture_lab.control_panel') -WorkingDirectory $PSScriptRoot
