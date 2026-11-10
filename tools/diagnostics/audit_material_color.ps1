param(
 [Parameter(Mandatory=$true)][string]$Avatar,
 [Parameter(Mandatory=$true)][string]$Output,
 [string]$Unity='C:\Program Files\Unity\Hub\Editor\2022.3.22f1\Editor\Unity.exe'
)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskAvatar=(Resolve-Path -LiteralPath $Avatar).Path
$taskOutput=[IO.Path]::GetFullPath($Output)
if(Test-Path -LiteralPath $taskOutput){throw 'Use a new diagnostic output directory.'}
New-Item -ItemType Directory -Path $taskOutput | Out-Null
$taskLog=Join-Path $taskOutput 'unity.log'
$taskRun=Start-Process -FilePath $Unity -ArgumentList @('-batchmode','-quit','-projectPath',('"'+(Join-Path $taskRoot 'unity/TanakaCap')+'"'),'-executeMethod','TanakaCap.Editor.MaterialColorAudit.Run','--audit-avatar',('"'+$taskAvatar+'"'),'--audit-output',('"'+$taskOutput+'"'),'-logFile',('"'+$taskLog+'"')) -WindowStyle Hidden -PassThru -Wait
if($taskRun.ExitCode -ne 0){throw "Material audit failed. See $taskLog"}
if(-not (Select-String -LiteralPath $taskLog -Pattern 'TANAKACAP_MATERIAL_COLOR_AUDIT_OK' -Quiet)){throw 'Material audit completion marker missing.'}
Write-Output $taskOutput
