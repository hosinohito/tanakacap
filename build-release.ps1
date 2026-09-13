param([string]$Version='', [switch]$SkipUnity, [switch]$Publishable, [switch]$CheckOnly, [string]$Unity='C:\Program Files\Unity\Hub\Editor\2022.3.22f1\Editor\Unity.exe')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
$taskTranscript=$false
try {
if(-not $Version){$Version='0.1.0-build-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')}
if($Version -notmatch '^[0-9A-Za-z][0-9A-Za-z._-]{0,60}$'){throw 'Invalid version name'}
New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot 'results') -Force | Out-Null
$taskBuildLog=Join-Path $PSScriptRoot ('results/release-build-'+$Version+'.log')
Start-Transcript -Path $taskBuildLog | Out-Null
$taskTranscript=$true
Write-Host "Build log: $taskBuildLog"
if(-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')){throw 'Missing .venv. Follow README.md to create the locked Python environment.'}
if(-not $SkipUnity -and -not (Test-Path -LiteralPath $Unity)){throw "Unity 2022.3.22f1 not found: $Unity"}
if(-not $CheckOnly -and -not (Test-Path -LiteralPath 'assets-source/licenses/opencv-ffmpeg-sources.zip')){
 & '.\.venv\Scripts\python.exe' -X utf8 tools/prepare_ffmpeg_sources.py
 if($LASTEXITCODE){throw 'FFmpeg source preparation failed'}
}
& '.\.venv\Scripts\python.exe' -X utf8 tools/check_release_inputs.py
if($LASTEXITCODE){throw 'Missing or changed originals. Restore the listed files; see README.md.'}
if($CheckOnly){Write-Host 'Input check only. Unity activation will be checked during the actual build.';return}
$taskOutput=Join-Path $PSScriptRoot ('builds/releases/'+$Version)
if(Test-Path -LiteralPath $taskOutput){throw "Version already exists: $taskOutput"}
if(-not $SkipUnity){
 Write-Host 'Building Player and Exporter from source. Close this project in Unity Editor first.'
 $taskProject=Join-Path $PSScriptRoot 'unity/TanakaCap'
 $taskLog=Join-Path $PSScriptRoot ('results/unity-release-'+$Version+'.log')
 $taskProcess=Start-Process -FilePath $Unity -ArgumentList @('-batchmode','-quit','-projectPath',('"'+$taskProject+'"'),'-executeMethod','TanakaCap.Editor.BuildRelease.Build','-logFile',('"'+$taskLog+'"')) -WindowStyle Hidden -PassThru -Wait
 if($taskProcess.ExitCode -ne 0){throw "Unity build failed. Check Hub activation or an open Editor. Log: $taskLog"}
}
$taskArgs=@('-X','utf8','tools/build_release.py','--version',$Version)
if($Publishable){$taskArgs+='--publishable'}
& '.\.venv\Scripts\python.exe' @taskArgs
if($LASTEXITCODE){throw 'Release packaging failed'}
Write-Host "Release ZIPs: $taskOutput"
Write-Host 'Use the assets listed in release-report.json. Nothing was uploaded.'
} finally {
 if($taskTranscript){Stop-Transcript | Out-Null}
 Pop-Location
}
