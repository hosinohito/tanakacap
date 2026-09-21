$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskUiScript=Join-Path $taskRoot 'run-ui.ps1'
$taskDesktop = [Environment]::GetFolderPath('Desktop')
if (-not $taskDesktop) { throw 'Desktop path is unavailable' }
$taskMainDesktop=[IO.Path]::GetFullPath($taskDesktop)
$taskDesktop=Join-Path $taskMainDesktop 'tanakacap-tools'
$taskRetiredDemo=Join-Path $taskDesktop 'tanakacap-demo-custom-brows.bat'
if (Test-Path -LiteralPath $taskRetiredDemo -PathType Leaf) { Remove-Item -LiteralPath $taskRetiredDemo }
if (-not (Test-Path -LiteralPath $taskDesktop)) { New-Item -ItemType Directory -Path $taskDesktop | Out-Null }
# Only this project's known auxiliary launchers are moved. Main launchers stay visible.
$taskAuxiliaryNames=@(
 'tanakacap-avatar-files.bat','tanakacap-compare-analyze.bat','tanakacap-compare-arm-depth.bat',
 'tanakacap-compare-body.bat','tanakacap-compare-capture.bat','tanakacap-compare-expressions.bat',
 'tanakacap-compare-f.bat','tanakacap-compare-face.bat','tanakacap-compare-fp16.bat',
 'tanakacap-compare-hamer.bat','tanakacap-compare-head-follow.bat','tanakacap-compare-physbone.bat',
 'tanakacap-compare-shoulder.bat','tanakacap-demo-custom-brows.bat','tanakacap-head-only.bat',
 'tanakacap-motion-auto-expressions.bat','tanakacap-test-30fps.bat','tanakacap-test-auto-expressions.bat',
 'tanakacap-test-face-original.bat','tanakacap-test-face-pnp.bat','tanakacap-test-fp16.bat',
 'tanakacap-test-mouth-z.bat','tanakacap-test-no-preview.bat','tanakacap-test-shoulder.bat')
foreach ($taskName in $taskAuxiliaryNames) {
    $taskOld=[IO.Path]::GetFullPath((Join-Path $taskMainDesktop $taskName))
    $taskNew=[IO.Path]::GetFullPath((Join-Path $taskDesktop $taskName))
    if ([IO.Path]::GetDirectoryName($taskOld) -ne $taskMainDesktop -or
        [IO.Path]::GetDirectoryName($taskNew) -ne $taskDesktop) { throw 'Launcher path escaped its intended directory' }
    if (Test-Path -LiteralPath $taskOld -PathType Leaf) {
        if (Test-Path -LiteralPath $taskNew) { throw "Both launcher paths exist; preserve and inspect: $taskName" }
        Move-Item -LiteralPath $taskOld -Destination $taskNew
    }
}
$taskUiTarget=Join-Path $taskMainDesktop 'tanakacap.bat'
[IO.File]::WriteAllText($taskUiTarget,"@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskUiScript`"`r`n",[Text.Encoding]::Default)
$taskTarget = Join-Path $taskMainDesktop 'tanakacap-test.bat'
$taskScript = Join-Path $taskRoot 'run-avatar.ps1'
$taskContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskUiScript`" -AutoCustom -RecordedTest`r`n"
# cmd.exe consumes its system ANSI encoding. Current project path is ASCII.
[IO.File]::WriteAllText($taskTarget,$taskContents,[Text.Encoding]::Default)
Write-Output $taskTarget

$taskComparisonScript = Join-Path $taskRoot 'run-comparison.ps1'
$taskArmVideos = Join-Path $taskRoot 'results\avatar-videos\arm-corrections-final'
$taskArmVideoBat = Join-Path $taskDesktop 'tanakacap-compare-arm-corrections.bat'
[IO.File]::WriteAllText($taskArmVideoBat,"@echo off`r`nstart `"`" `"$taskArmVideos`"`r`n",[Text.Encoding]::Default)
$taskFaceCapture = Join-Path $taskMainDesktop 'tanakacap-face-capture.bat'
[IO.File]::WriteAllText($taskFaceCapture,"@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskComparisonScript`" -Mode capture -Profile face-head`r`npause`r`n",[Text.Encoding]::Default)
Write-Output $taskFaceCapture
$taskHeadFollowVideo=Join-Path $taskRoot 'results/avatar-videos/head-follow/face-closeup.mp4'
$taskHeadFollowBat=Join-Path $taskDesktop 'tanakacap-compare-head-follow.bat'
[IO.File]::WriteAllText($taskHeadFollowBat,"@echo off`r`nstart `"`" `"$taskHeadFollowVideo`"`r`n",[Text.Encoding]::Default)
Write-Output $taskHeadFollowBat
foreach ($taskMode in @('capture','analyze')) {
    $taskComparisonTarget = Join-Path $taskDesktop ("tanakacap-compare-$taskMode.bat")
    $taskComparisonContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskComparisonScript`" -Mode $taskMode`r`npause`r`n"
    [IO.File]::WriteAllText($taskComparisonTarget,$taskComparisonContents,[Text.Encoding]::Default)
    Write-Output $taskComparisonTarget
}

$taskHamerTarget = Join-Path $taskDesktop 'tanakacap-compare-hamer.bat'
$taskHamerScript = Join-Path $taskRoot 'run-hamer-comparison.ps1'
$taskHamerContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskHamerScript`"`r`npause`r`n"
[IO.File]::WriteAllText($taskHamerTarget,$taskHamerContents,[Text.Encoding]::Default)
Write-Output $taskHamerTarget

$taskBodyTarget = Join-Path $taskDesktop 'tanakacap-compare-body.bat'
$taskBodyScript = Join-Path $taskRoot 'run-body-comparison.ps1'
$taskBodyContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskBodyScript`"`r`npause`r`n"
[IO.File]::WriteAllText($taskBodyTarget,$taskBodyContents,[Text.Encoding]::Default)
Write-Output $taskBodyTarget

$taskArmTarget = Join-Path $taskDesktop 'tanakacap-compare-arm-depth.bat'
$taskArmFolder = Join-Path $taskRoot 'results/avatar-videos/front-projection-final'
$taskArmContents = "@echo off`r`nexplorer.exe `"$taskArmFolder`"`r`n"
[IO.File]::WriteAllText($taskArmTarget,$taskArmContents,[Text.Encoding]::Default)
Write-Output $taskArmTarget

$taskShoulderTarget = Join-Path $taskDesktop 'tanakacap-compare-shoulder.bat'
$taskShoulderFolder = Join-Path $taskRoot 'results/avatar-videos/shoulder-projection-final'
$taskShoulderContents = "@echo off`r`nexplorer.exe `"$taskShoulderFolder`"`r`n"
[IO.File]::WriteAllText($taskShoulderTarget,$taskShoulderContents,[Text.Encoding]::Default)
Write-Output $taskShoulderTarget
$taskShoulderTest = Join-Path $taskDesktop 'tanakacap-test-shoulder.bat'
$taskShoulderTestContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskScript`" -Camera 1 -Diagnose -Frames 1800 -ShoulderYawMode face_ratio`r`npause`r`n"
[IO.File]::WriteAllText($taskShoulderTest,$taskShoulderTestContents,[Text.Encoding]::Default)
Write-Output $taskShoulderTest

$taskPackageTarget = Join-Path $taskDesktop 'tanakacap-avatar-files.bat'
$taskPackageFolder = Join-Path $taskRoot 'builds/player'
$taskPackageContents = "@echo off`r`nexplorer.exe `"$taskPackageFolder`"`r`n"
[IO.File]::WriteAllText($taskPackageTarget,$taskPackageContents,[Text.Encoding]::Default)
Write-Output $taskPackageTarget

# Separate non-recording, unlimited launchers. The diagnostic launcher stays available.
$taskLiveTarget = Join-Path $taskMainDesktop 'tanakacap-live.bat'
$taskLiveContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskScript`" -Camera 1 -NoLog`r`nif errorlevel 1 pause`r`n"
[IO.File]::WriteAllText($taskLiveTarget,$taskLiveContents,[Text.Encoding]::Default)
Write-Output $taskLiveTarget
$taskDemoTarget = Join-Path $taskMainDesktop 'tanakacap-motion.bat'
$taskDemoScript = Join-Path $taskRoot 'run-motion.ps1'
$taskDemoContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskDemoScript`"`r`nif errorlevel 1 pause`r`n"
[IO.File]::WriteAllText($taskDemoTarget,$taskDemoContents,[Text.Encoding]::Default)
Write-Output $taskDemoTarget

# Head-only with automatic CUDA region acquisition; no expression/body/gaze or logs.
$taskHeadTarget = Join-Path $taskDesktop 'tanakacap-head-only.bat'
$taskHeadContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskScript`" -Camera 1 -HeadOnly -NoLog`r`nif errorlevel 1 pause`r`n"
[IO.File]::WriteAllText($taskHeadTarget,$taskHeadContents,[Text.Encoding]::Default)
Write-Output $taskHeadTarget

# Locally rendered real PhysBone / independent solver comparison videos.
$taskPhysTarget = Join-Path $taskDesktop 'tanakacap-compare-physbone.bat'
$taskPhysFolder = Join-Path $taskRoot 'results/avatar-videos/physbone-vs-independent'
$taskPhysContents = "@echo off`r`nexplorer.exe /select,`"$taskPhysFolder\front.mp4`"`r`n"
[IO.File]::WriteAllText($taskPhysTarget,$taskPhysContents,[Text.Encoding]::Default)
Write-Output $taskPhysTarget

# Face source trial: original camera shortcut and recorded avatar comparison.
$taskFaceOriginalTarget = Join-Path $taskDesktop 'tanakacap-test-face-original.bat'
$taskFaceOriginalContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskScript`" -Camera 1 -TrackingMode full -FaceSource separate -HeadPoseMode pnp -Diagnose -Frames 1800`r`npause`r`n"
[IO.File]::WriteAllText($taskFaceOriginalTarget,$taskFaceOriginalContents,[Text.Encoding]::Default)
Write-Output $taskFaceOriginalTarget
$taskFaceCompareTarget = Join-Path $taskDesktop 'tanakacap-compare-face.bat'
$taskFaceVideo = Join-Path $taskRoot 'results/avatar-videos/mouth-no-z/face-closeup.mp4'
$taskFaceCompareContents = "@echo off`r`nexplorer.exe /select,`"$taskFaceVideo`"`r`n"
[IO.File]::WriteAllText($taskFaceCompareTarget,$taskFaceCompareContents,[Text.Encoding]::Default)
Write-Output $taskFaceCompareTarget

$taskFCompareTarget = Join-Path $taskDesktop 'tanakacap-compare-f.bat'
$taskFVideo = Join-Path $taskRoot 'results/avatar-videos/detector-graph-f/side-by-side.mp4'
$taskFCompareContents = "@echo off`r`nexplorer.exe /select,`"$taskFVideo`"`r`n"
[IO.File]::WriteAllText($taskFCompareTarget,$taskFCompareContents,[Text.Encoding]::Default)
Write-Output $taskFCompareTarget

$taskPrecisionTarget = Join-Path $taskDesktop 'tanakacap-compare-fp16.bat'
$taskPrecisionVideo = Join-Path $taskRoot 'results/avatar-videos/cuda-precision/side-by-side.mp4'
$taskPrecisionContents = "@echo off`r`nexplorer.exe /select,`"$taskPrecisionVideo`"`r`n"
[IO.File]::WriteAllText($taskPrecisionTarget,$taskPrecisionContents,[Text.Encoding]::Default)
Write-Output $taskPrecisionTarget

$taskFp16TestTarget = Join-Path $taskDesktop 'tanakacap-test-fp16.bat'
[IO.File]::WriteAllText($taskFp16TestTarget,$taskContents,[Text.Encoding]::Default)
Write-Output $taskFp16TestTarget

$taskFacePnpTarget = Join-Path $taskDesktop 'tanakacap-test-face-pnp.bat'
$taskFacePnpContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskScript`" -Camera 1 -TrackingMode full -FaceSource body3d -HeadPoseMode pnp -Diagnose -Frames 1800`r`npause`r`n"
[IO.File]::WriteAllText($taskFacePnpTarget,$taskFacePnpContents,[Text.Encoding]::Default)
Write-Output $taskFacePnpTarget

$taskMouthZTarget = Join-Path $taskDesktop 'tanakacap-test-mouth-z.bat'
$taskMouthZContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskScript`" -Camera 1 -TrackingMode full -FaceSource body3d -HeadPoseMode pnp_depthmouth -Diagnose -Frames 1800`r`npause`r`n"
[IO.File]::WriteAllText($taskMouthZTarget,$taskMouthZContents,[Text.Encoding]::Default)
Write-Output $taskMouthZTarget

$taskThirtyTarget = Join-Path $taskDesktop 'tanakacap-test-30fps.bat'
[IO.File]::WriteAllText($taskThirtyTarget,$taskContents.Replace(' -Diagnose',' -RenderFps 30 -Diagnose'),[Text.Encoding]::Default)
Write-Output $taskThirtyTarget

$taskHiddenTarget = Join-Path $taskDesktop 'tanakacap-test-no-preview.bat'
[IO.File]::WriteAllText($taskHiddenTarget,$taskContents.Replace(' -Diagnose',' -NoPreview -Diagnose'),[Text.Encoding]::Default)
Write-Output $taskHiddenTarget

$taskExpressionCompare = Join-Path $taskDesktop 'tanakacap-compare-expressions.bat'
$taskExpressionVideo = Join-Path $taskRoot 'results/avatar-videos/expression-mapping/face-closeup.mp4'
[IO.File]::WriteAllText($taskExpressionCompare,"@echo off`r`nexplorer.exe /select,`"$taskExpressionVideo`"`r`n",[Text.Encoding]::Default)
Write-Output $taskExpressionCompare
$taskAutoTest = Join-Path $taskDesktop 'tanakacap-test-auto-expressions.bat'
[IO.File]::WriteAllText($taskAutoTest,$taskContents.Replace(' -Diagnose',' -ExpressionMode auto-custom -Diagnose'),[Text.Encoding]::Default)
Write-Output $taskAutoTest
$taskAutoMotion = Join-Path $taskDesktop 'tanakacap-motion-auto-expressions.bat'
$taskMotionScript = Join-Path $taskRoot 'run-motion.ps1'
[IO.File]::WriteAllText($taskAutoMotion,"@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskMotionScript`" -ExpressionMode auto-custom`r`npause`r`n",[Text.Encoding]::Default)
Write-Output $taskAutoMotion
$taskCameraDiagnostic=Join-Path $taskDesktop 'tanakacap-diagnose-camera.bat'
$taskDiagnosticScript=Join-Path $taskRoot 'tools/diagnostics/diagnose-camera.bat'
[IO.File]::WriteAllText($taskCameraDiagnostic,"@echo off`r`ncall `"$taskDiagnosticScript`"`r`n",[Text.Encoding]::Default)
Write-Output $taskCameraDiagnostic

$taskHandVideos = Join-Path $taskRoot 'results\avatar-videos\hand-head-contact'
$taskHandVideoBat = Join-Path $taskDesktop 'tanakacap-compare-hand-head.bat'
[IO.File]::WriteAllText($taskHandVideoBat,"@echo off`r`nstart `"`" `"$taskHandVideos`"`r`n",[Text.Encoding]::Default)
