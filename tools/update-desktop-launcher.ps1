$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskDesktop = [Environment]::GetFolderPath('Desktop')
if (-not $taskDesktop) { throw 'Desktop path is unavailable' }
$taskTarget = Join-Path $taskDesktop 'tanakacap-test.bat'
$taskScript = Join-Path $taskRoot 'run-avatar-lab.ps1'
$taskContents = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$taskScript`" -Camera 1 -Diagnose -Frames 1800`r`npause`r`n"
# cmd.exe consumes its system ANSI encoding. Current project path is ASCII.
[IO.File]::WriteAllText($taskTarget,$taskContents,[Text.Encoding]::Default)
Write-Output $taskTarget

$taskComparisonScript = Join-Path $taskRoot 'run-comparison-lab.ps1'
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
