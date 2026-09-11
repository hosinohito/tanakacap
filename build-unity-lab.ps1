param([string]$Unity = 'C:\Program Files\Unity\Hub\Editor\2022.3.22f1\Editor\Unity.exe')
$ErrorActionPreference = 'Stop'
$taskProject = Join-Path $PSScriptRoot 'unity\TanakaCap'
$taskLog = Join-Path $PSScriptRoot 'results\unity-build.log'
if (-not (Test-Path -LiteralPath $Unity)) { throw "Unity Editor not found: $Unity" }
if (-not (Test-Path -LiteralPath (Join-Path $taskProject 'Assets\HAOLAN\Phys_Haolan.prefab'))) {
    throw 'Run .venv\Scripts\python.exe tools\prepare_unity.py first.'
}
# Explicit Wait is required: Unity is a Windows GUI executable.
$taskProcess = Start-Process -FilePath $Unity -ArgumentList @('-batchmode','-quit','-projectPath', ('"'+$taskProject+'"'),
    '-executeMethod','TanakaCap.Editor.BuildLab.Build','-logFile',('"'+$taskLog+'"')) -WindowStyle Hidden -PassThru -Wait
if ($taskProcess.ExitCode -ne 0) { throw "Unity failed. See $taskLog" }
