param([switch]$AutoCustom,[switch]$RecordedTest)
$ErrorActionPreference='Stop'
$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/pythonw.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run setup.ps1 first.' }
$taskUiArgs=@('-m','tanakacap.control_panel')
if ($AutoCustom) { $taskUiArgs+='--auto-custom' }
if ($RecordedTest) { $taskUiArgs+='--recorded-test' }
Start-Process -FilePath $taskPython -ArgumentList $taskUiArgs -WorkingDirectory $PSScriptRoot
