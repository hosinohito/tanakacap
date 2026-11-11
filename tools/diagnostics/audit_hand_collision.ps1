param([string]$Method='HandCollisionExportAudit.Run',[string]$Log='export-audit',[string]$SourceProject)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskProject=Join-Path $taskRoot 'results/hand-collision/project'
if(-not (Test-Path -LiteralPath $taskProject)){
 if(-not $SourceProject){throw 'Supply -SourceProject to create an isolated copy first.'}
 New-Item -ItemType Directory -Path $taskProject | Out-Null
 foreach($name in @('Assets','Packages','ProjectSettings')){Copy-Item -LiteralPath (Join-Path $SourceProject $name) -Destination $taskProject -Recurse}
}
$taskSource=Join-Path $taskRoot 'unity/TanakaCap/Assets/TanakaCap'
$taskTarget=Join-Path $taskProject 'Assets/TanakaCap'
New-Item -ItemType Directory -Force -Path (Join-Path $taskTarget 'Editor') | Out-Null
foreach($name in @('AvatarPackage.cs','FaceExpressions.cs','SecondaryMotion.cs','Editor/AvatarExporter.cs','Editor/FaceProfileExporter.cs','Editor/AvatarShaderCompatibility.cs','Editor/SecondaryMotionExporter.cs','Editor/StandardHandColliderExporter.cs','Editor/HandCollisionChecks.cs')){
 Copy-Item -LiteralPath (Join-Path $taskSource $name) -Destination (Join-Path $taskTarget $name) -Force
}
Copy-Item (Join-Path $PSScriptRoot 'hand-collision/*.cs') (Join-Path $taskTarget 'Editor') -Force
'using System; namespace TanakaCap { public static class RuntimeStartup { public static void RecordError(Exception e){UnityEngine.Debug.LogWarning(e.Message);} } }' | Set-Content -Encoding utf8 (Join-Path $taskTarget 'AuditLog.cs')
$taskLog=Join-Path $taskRoot ('results/hand-collision/'+$Log+'.log')
$p=Start-Process -FilePath 'C:\Program Files\Unity\Hub\Editor\2022.3.22f1\Editor\Unity.exe' -ArgumentList @('-batchmode','-quit','-projectPath',('"'+$taskProject+'"'),'-executeMethod',$Method,'-logFile',('"'+$taskLog+'"')) -WindowStyle Hidden -PassThru -Wait
if($p.ExitCode -ne 0){throw "Unity audit failed: $taskLog"}
$taskMarker=if($Method -eq 'HandCollisionRuntimeAudit.Run'){'HAND_RUNTIME_AUDIT_OK'}else{'HAND_AUDIT_OK'}
if(-not (Select-String -LiteralPath $taskLog -Pattern $taskMarker -Quiet)){throw 'Audit completion marker missing'}
