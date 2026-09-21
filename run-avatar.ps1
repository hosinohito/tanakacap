[CmdletBinding()]
param([int]$Camera = 1, [int]$Frames = 18000, [switch]$Diagnose,
    [ValidateSet('rtmw-l-384','dwpose-l-384')][string]$Model = 'rtmw-l-384',
    [ValidateSet(1,3)][int]$ObservationBlock = 3,
    [ValidateSet(1,3)][int]$ObservationStride = 1,
    [ValidateSet("legacy","width_only","face_ratio")][string]$ShoulderYawMode,
    [string]$Avatar,
    [switch]$NoLog,
    [ValidateRange(64,4096)][int]$OutputHeight=1080,
    [ValidateRange(64,4096)][int]$OutputWidth,
    [switch]$NoPreview,
    [switch]$LegacyPreview,
    [ValidateRange(0,1)][double]$MouthCornerEmphasis=0,
    [ValidateRange(.25,4)][Nullable[double]]$MouthCornerGamma,
    [ValidateRange(0,1)][Nullable[double]]$MouthOpenSmileSuppression,
    [ValidateSet('existing','auto-custom')][string]$ExpressionMode='existing',
    [switch]$LegacySecondaryResponse,
    [ValidateSet(30,60)][int]$RenderFps=60,
    [switch]$NoEdgeAA,
    [switch]$NoBody,
    [switch]$HeadOnly,
    [ValidateSet('full','face_head','head_only')][string]$TrackingMode,
    [int[]]$HeadRoi,
    [ValidateSet('auto','fixed')][string]$HeadRoiMode='auto',
    [ValidateSet(1,2,3)][int]$DetectorInterval,
    [ValidateSet('yolox-m-human','yolox-tiny-human')][string]$DetectorModel,
    [ValidateSet('separate','body3d')][string]$FaceSource,
    [ValidateSet('pnp','size2d','legacy','depth3d','pnp_depthmouth')][string]$HeadPoseMode,
    [ValidateSet('legacy','crop')][string]$PreprocessMode,
    [switch]$BatchEyes,
    [switch]$NoBatchEyes,
    [switch]$DetectorGraph,
    [switch]$NoDetectorGraph,
    [switch]$NoGaze,
    [switch]$NoPersonDetector,
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
    $taskExe = Join-Path $PSScriptRoot 'builds\player\TanakaCap.exe'
    if (-not (Test-Path -LiteralPath $taskExe)) { throw 'Run build-player.ps1 first.' }
    # This is the interactive avatar window requested by this launcher.
    $taskGazeSettings=Get-Content (Join-Path $PSScriptRoot 'tracking-settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $TrackingMode) { $TrackingMode=$taskGazeSettings.tracking_mode }
    if (-not $TrackingMode) { $TrackingMode='full' }
    if ($TrackingMode -notin @('full','face_head','head_only')) { throw 'tracking_mode must be full, face_head or head_only' }
    if ($TrackingMode -eq 'head_only') { $HeadOnly=$true }
    if ($TrackingMode -eq 'face_head') { $NoBody=$true; $NoGaze=$true }
    if ($HeadOnly) { $NoBody=$true; $NoGaze=$true; $NoPersonDetector=$true }
    if ($taskGazeSettings.body_enabled -eq $false) { $NoBody=$true }
    if ($taskGazeSettings.person_detector_enabled -eq $false) { $NoPersonDetector=$true }
    if (-not $DetectorInterval) { $DetectorInterval=$taskGazeSettings.detector_interval }
    if (-not $DetectorInterval) { $DetectorInterval=1 }
    if ($DetectorInterval -notin @(1,2,3)) { throw 'Invalid detector_interval' }
    if (-not $DetectorModel) { $DetectorModel=$taskGazeSettings.detector_model }
    if (-not $DetectorModel) { $DetectorModel='yolox-m-human' }
    if ($DetectorModel -notin @('yolox-m-human','yolox-tiny-human')) { throw 'Invalid detector_model' }
    if (-not $FaceSource) { $FaceSource=$taskGazeSettings.face_source }
    if (-not $FaceSource) { $FaceSource='separate' }
    if (-not $HeadPoseMode) { $HeadPoseMode=$taskGazeSettings.head_pose_mode }
    if (-not $HeadPoseMode) { $HeadPoseMode='pnp' }
    if ($HeadPoseMode -in @('depth3d','pnp_depthmouth') -and $FaceSource -ne 'body3d') { throw 'depth3d requires -FaceSource body3d' }
    if ($FaceSource -notin @('separate','body3d')) { throw 'Invalid face_source' }
    $taskGazeGain=4.0
    if ($taskGazeSettings.PSObject.Properties.Name -contains 'gaze_gain') { $taskGazeGain=[double]$taskGazeSettings.gaze_gain }
    if ($taskGazeGain -lt .5 -or $taskGazeGain -gt 6 -or [double]::IsNaN($taskGazeGain)) { throw 'gaze_gain must be 0.5..6' }
    $taskPlayerArgs=@('--gaze-gain',$taskGazeGain.ToString([Globalization.CultureInfo]::InvariantCulture))
    $taskPlayerArgs+=@('--expression-mode',$ExpressionMode)
    $taskPlayerArgs+=@('--render-fps',$RenderFps.ToString())
    $taskPlayerArgs+=@('--output-height',$OutputHeight.ToString())
    if (-not $PSBoundParameters.ContainsKey('MouthCornerEmphasis') -and $taskGazeSettings.PSObject.Properties.Name -contains 'mouth_corner_emphasis') { $MouthCornerEmphasis=[double]$taskGazeSettings.mouth_corner_emphasis }
    if ([double]::IsNaN($MouthCornerEmphasis) -or $MouthCornerEmphasis -lt 0 -or $MouthCornerEmphasis -gt 1) { throw 'mouth_corner_emphasis must be 0..1' }
    $taskPlayerArgs+=@('--mouth-corner-emphasis',$MouthCornerEmphasis.ToString([Globalization.CultureInfo]::InvariantCulture))
    foreach($taskOption in @(@('MouthCornerGamma','mouth_corner_gamma','--mouth-corner-gamma',.25,4),@('MouthOpenSmileSuppression','mouth_open_smile_suppression','--mouth-open-smile-suppression',0,1))) {
        $taskValue=Get-Variable -Name $taskOption[0] -ValueOnly
        if (-not $PSBoundParameters.ContainsKey($taskOption[0])) { $taskValue=$taskGazeSettings.($taskOption[1]) }
        if ($null -ne $taskValue) {
            $taskValue=[double]$taskValue
            if ([double]::IsNaN($taskValue) -or [double]::IsInfinity($taskValue) -or $taskValue -lt $taskOption[3] -or $taskValue -gt $taskOption[4]) { throw "Invalid $($taskOption[1])" }
            $taskPlayerArgs+=@($taskOption[2],$taskValue.ToString([Globalization.CultureInfo]::InvariantCulture))
        }
    }
    if ($OutputWidth) { $taskPlayerArgs+=@('--output-width',$OutputWidth.ToString()) }
    if ($NoPreview) { $taskPlayerArgs+='--no-preview' }
    if ($LegacyPreview) { $taskPlayerArgs+='--legacy-preview' }
    if ($LegacySecondaryResponse) { $taskPlayerArgs+='--legacy-secondary-response' }
    if ($NoEdgeAA) { $taskPlayerArgs+='--no-edge-aa' }
    if ($NoLog) { $taskPlayerArgs += @('-nolog') }
    if ($Diagnose -and -not $NoLog) {
        $taskPerfFolder=Join-Path $PSScriptRoot 'results/player-performance'
        $null=New-Item -ItemType Directory -Force -Path $taskPerfFolder
        $taskPerfFile=Join-Path $taskPerfFolder ([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'.jsonl')
        $taskPlayerArgs+=@('--performance-log',('"'+$taskPerfFile+'"'))
        Write-Host "Player performance: $taskPerfFile"
    }
    if ($Avatar) { $taskPlayerArgs += @('--avatar',('"'+(Resolve-Path -LiteralPath $Avatar).Path+'"')) }
    if ($taskGazeSettings.gaze_render_mode -eq 'bones') { $taskPlayerArgs+='--gaze-bones' }
    if ($NoBody -or $taskGazeSettings.face_distance_enabled -eq $false) { $taskPlayerArgs+='--no-face-distance' }
    if ($taskGazeSettings.face_distance_mode -eq 'seated') { $taskPlayerArgs+='--face-distance-seated' }
    if ($taskGazeSettings.face_distance_mode -eq 'translate') { $taskPlayerArgs+='--face-distance-translate' }

    $taskPlayer = Start-Process -FilePath $taskExe -ArgumentList $taskPlayerArgs -PassThru
    $taskExtra = @('--face-source',$FaceSource,'--detector-interval',$DetectorInterval.ToString(),'--detector-model',$DetectorModel)
    if (-not $PreprocessMode) { $PreprocessMode=$taskGazeSettings.preprocess_mode }
    if (-not $PreprocessMode) { $PreprocessMode='legacy' }
    $taskExtra+=@('--preprocess-mode',$PreprocessMode)
    if (($BatchEyes -or $taskGazeSettings.batch_eyes) -and -not $NoBatchEyes) { $taskExtra+='--batch-eyes' }
    if (($DetectorGraph -or $taskGazeSettings.detector_graph) -and -not $NoDetectorGraph) { $taskExtra+='--detector-graph' }
    if ($HeadOnly) { $taskExtra+=@('--head-only','--head-roi-mode',$HeadRoiMode); if ($HeadRoi) { if ($HeadRoi.Count -ne 4) { throw 'HeadRoi must be x,y,w,h' }; $taskExtra+='--roi'; $taskExtra+=$HeadRoi } }
    if ($NoBody) { $taskExtra+='--no-body' } else { $taskExtra+='--body3d' }
    if ($NoPersonDetector) { $taskExtra+='--fixed-roi' }
    $taskExtra += @('--parent-pid',$taskPlayer.Id)
    if ($NoLog) { $taskExtra += '--no-log'; $Frames=0 }
    if ($Diagnose -and -not $NoLog) { $taskExtra += '--landmarks' }
    if ($IntegerBodyPeaks) { $taskExtra += '--integer-body-peaks' }
    if (-not $NoGaze -and $taskGazeSettings.gaze_enabled -eq $true) { $taskExtra += '--gaze' }
    if ($HeadPoseMode) { $taskExtra += @('--head-pose-mode',$HeadPoseMode) }
    if ($taskGazeSettings.PSObject.Properties.Name -contains 'brow_gain') {
        $taskExtra+=@('--brow-gain',([double]$taskGazeSettings.brow_gain).ToString([Globalization.CultureInfo]::InvariantCulture))
    }
    if ($taskGazeSettings.PSObject.Properties.Name -contains 'head_pitch_gain') {
        $taskPitchGain=[double]$taskGazeSettings.head_pitch_gain
        if ([double]::IsNaN($taskPitchGain) -or $taskPitchGain -lt .5 -or $taskPitchGain -gt 3) { throw 'head_pitch_gain must be 0.5..3' }
        $taskExtra += @('--head-pitch-gain',$taskPitchGain.ToString([Globalization.CultureInfo]::InvariantCulture))
    }
    if ($taskGazeSettings.PSObject.Properties.Name -contains 'mouth_lip_depth_scale') {
        $taskLipDepth=[double]$taskGazeSettings.mouth_lip_depth_scale
        if ([double]::IsNaN($taskLipDepth) -or $taskLipDepth -lt .5 -or $taskLipDepth -gt 2) { throw 'mouth_lip_depth_scale must be 0.5..2' }
        $taskExtra += @('--mouth-lip-depth-scale',$taskLipDepth.ToString([Globalization.CultureInfo]::InvariantCulture))
    }
    if ($taskGazeSettings.face_distance_filter) { $taskExtra += @('--face-distance-filter',$taskGazeSettings.face_distance_filter) }
    if ($ShoulderYawMode) { $taskExtra += @('--shoulder-yaw-mode',$ShoulderYawMode) }
    elseif ($taskGazeSettings.shoulder_yaw_mode) { $taskExtra += @('--shoulder-yaw-mode',$taskGazeSettings.shoulder_yaw_mode) }
    if ($taskGazeSettings.arm_depth_mode) { $taskExtra += @('--arm-depth-mode',$taskGazeSettings.arm_depth_mode) }
    if ($taskGazeSettings.gaze_reference) { $taskExtra += @('--gaze-reference',$taskGazeSettings.gaze_reference) }
    & '.venv\Scripts\python.exe' -m tanakacap benchmark --source camera --camera $Camera --model $Model --frames $Frames --unity-port 39540 --observation-block $ObservationBlock --observation-stride $ObservationStride @taskExtra
    if ($LASTEXITCODE -ne 0) { throw "Capture exited with code $LASTEXITCODE" }
} finally {
    if ($taskPlayer -and -not $taskPlayer.HasExited) { $null = $taskPlayer.CloseMainWindow() }
    Pop-Location
}
