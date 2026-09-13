param([string]$Version='0.1.0-dev',[switch]$SkipUnity,[switch]$Publishable,[string]$Unity='C:\Program Files\Unity\Hub\Editor\2022.3.22f1\Editor\Unity.exe')
$ErrorActionPreference='Stop'
if(-not $SkipUnity){
 $taskProject=Join-Path $PSScriptRoot 'unity/TanakaCap'
 $taskLog=Join-Path $PSScriptRoot 'results/unity-release-build.log'
 $taskProcess=Start-Process -FilePath $Unity -ArgumentList @('-batchmode','-quit','-projectPath',('"'+$taskProject+'"'),'-executeMethod','TanakaCap.Editor.BuildRelease.Build','-logFile',('"'+$taskLog+'"')) -WindowStyle Hidden -PassThru -Wait
 if($taskProcess.ExitCode -ne 0){throw "Unity release build failed: $taskLog"}
}
$taskArgs=@('tools/build_release.py','--version',$Version)
if($Publishable){$taskArgs+='--publishable'}
Push-Location $PSScriptRoot
try { & '.\.venv\Scripts\python.exe' @taskArgs; if($LASTEXITCODE){throw 'Release packaging failed'} }
finally { Pop-Location }
