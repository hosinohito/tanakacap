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
