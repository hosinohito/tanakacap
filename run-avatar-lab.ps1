param([int]$Camera = 1, [int]$Frames = 18000, [switch]$Diagnose,
    [ValidateSet('rtmw-l-384','dwpose-l-384')][string]$Model = 'rtmw-l-384',
    [ValidateSet(1,3)][int]$ObservationBlock = 3,
    [ValidateSet(1,3)][int]$ObservationStride = 1,
    [switch]$IntegerBodyPeaks)
$ErrorActionPreference = 'Stop'
if (-not $PSBoundParameters.ContainsKey('ObservationBlock')) {
    $taskSettingsPath = Join-Path $PSScriptRoot 'tracking-settings.json'
    if (Test-Path -LiteralPath $taskSettingsPath) {
        $taskSettings = Get-Content -LiteralPath $taskSettingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($taskSettings.observation_block -notin @(1,3)) { throw 'observation_block must be 1 or 3' }
        $ObservationBlock = [int]$taskSettings.observation_block
    }
}
if (-not $PSBoundParameters.ContainsKey('ObservationStride') -and $taskSettings -and $taskSettings.PSObject.Properties.Name -contains 'observation_stride') {
    if ($taskSettings.observation_stride -notin @(1,3)) { throw 'observation_stride must be 1 or 3' }
    $ObservationStride = [int]$taskSettings.observation_stride
}
if ($ObservationBlock -eq 1) { $ObservationStride = 1 }
Write-Host "Observation stride: $ObservationStride"
Write-Host "Observation block: $ObservationBlock (1=original, 3=three-frame averages)"
Push-Location $PSScriptRoot
$taskPlayer = $null
try {
    $taskExe = Join-Path $PSScriptRoot 'builds\lab\TanakaCap.exe'
    if (-not (Test-Path -LiteralPath $taskExe)) { throw 'Run build-unity-lab.ps1 first.' }
    # This is the interactive avatar window requested by this launcher.
    $taskGazeSettings=Get-Content (Join-Path $PSScriptRoot 'tracking-settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $taskGazeGain=4.0
    if ($taskGazeSettings.PSObject.Properties.Name -contains 'gaze_gain') { $taskGazeGain=[double]$taskGazeSettings.gaze_gain }
    if ($taskGazeGain -lt .5 -or $taskGazeGain -gt 6 -or [double]::IsNaN($taskGazeGain)) { throw 'gaze_gain must be 0.5..6' }
    $taskPlayerArgs=@('--gaze-gain',$taskGazeGain.ToString([Globalization.CultureInfo]::InvariantCulture))
    if ($taskGazeSettings.gaze_render_mode -eq 'bones') { $taskPlayerArgs+='--gaze-bones' }
    if ($taskGazeSettings.face_distance_enabled -eq $false) { $taskPlayerArgs+='--no-face-distance' }
    if ($taskGazeSettings.face_distance_mode -eq 'seated') { $taskPlayerArgs+='--face-distance-seated' }
    if ($taskGazeSettings.face_distance_mode -eq 'translate') { $taskPlayerArgs+='--face-distance-translate' }
    $taskPlayer = Start-Process -FilePath $taskExe -ArgumentList $taskPlayerArgs -PassThru
    $taskExtra = @()
    if ($Diagnose) { $taskExtra += '--landmarks' }
    if ($IntegerBodyPeaks) { $taskExtra += '--integer-body-peaks' }
    if ($taskGazeSettings.gaze_enabled -eq $true) { $taskExtra += '--gaze' }
    if ($taskGazeSettings.head_pose_mode) { $taskExtra += @('--head-pose-mode',$taskGazeSettings.head_pose_mode) }
    if ($taskGazeSettings.PSObject.Properties.Name -contains 'head_pitch_gain') {
        $taskPitchGain=[double]$taskGazeSettings.head_pitch_gain
        if ([double]::IsNaN($taskPitchGain) -or $taskPitchGain -lt .5 -or $taskPitchGain -gt 3) { throw 'head_pitch_gain must be 0.5..3' }
        $taskExtra += @('--head-pitch-gain',$taskPitchGain.ToString([Globalization.CultureInfo]::InvariantCulture))
    }
    if ($taskGazeSettings.gaze_reference) { $taskExtra += @('--gaze-reference',$taskGazeSettings.gaze_reference) }
    & '.venv\Scripts\python.exe' -m capture_lab benchmark --source camera --camera $Camera --model $Model --frames $Frames --preview --unity-port 39540 --body3d --observation-block $ObservationBlock --observation-stride $ObservationStride @taskExtra
    if ($LASTEXITCODE -ne 0) { throw "Capture exited with code $LASTEXITCODE" }
} finally {
    if ($taskPlayer -and -not $taskPlayer.HasExited) { $null = $taskPlayer.CloseMainWindow() }
    Pop-Location
}
