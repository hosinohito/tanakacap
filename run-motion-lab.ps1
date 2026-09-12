param([string]$Avatar,[ValidateRange(64,4096)][int]$OutputHeight=1080,
    [ValidateRange(64,4096)][int]$OutputWidth,
    [switch]$NoPreview,
    [switch]$LegacyPreview,
    [ValidateRange(0,1)][double]$MouthCornerEmphasis=0,
    [ValidateRange(.25,4)][Nullable[double]]$MouthCornerGamma,
    [ValidateRange(0,1)][Nullable[double]]$MouthOpenSmileSuppression,
    [ValidateSet('existing','auto-custom')][string]$ExpressionMode='existing',
    [switch]$LegacySecondaryResponse,
    [switch]$NoEdgeAA)
$ErrorActionPreference='Stop'
$taskExe=Join-Path $PSScriptRoot 'builds/lab/TanakaCap.exe'
if (-not (Test-Path -LiteralPath $taskExe)) { throw 'Run build-unity-lab.ps1 first.' }
$taskArgs=@('--motion-demo','-nolog')
$taskArgs+=@('--expression-mode',$ExpressionMode)
$taskArgs+=@('--output-height',$OutputHeight.ToString())
$taskMotionSettings=Get-Content (Join-Path $PSScriptRoot 'tracking-settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $PSBoundParameters.ContainsKey('MouthCornerEmphasis')) {
    if ($taskMotionSettings.PSObject.Properties.Name -contains 'mouth_corner_emphasis') { $MouthCornerEmphasis=[double]$taskMotionSettings.mouth_corner_emphasis }
}
if ([double]::IsNaN($MouthCornerEmphasis) -or $MouthCornerEmphasis -lt 0 -or $MouthCornerEmphasis -gt 1) { throw 'mouth_corner_emphasis must be 0..1' }
$taskArgs+=@('--mouth-corner-emphasis',$MouthCornerEmphasis.ToString([Globalization.CultureInfo]::InvariantCulture))
foreach($taskOption in @(@('MouthCornerGamma','mouth_corner_gamma','--mouth-corner-gamma',.25,4),@('MouthOpenSmileSuppression','mouth_open_smile_suppression','--mouth-open-smile-suppression',0,1))) {
    $taskValue=Get-Variable -Name $taskOption[0] -ValueOnly
    if (-not $PSBoundParameters.ContainsKey($taskOption[0])) { $taskValue=$taskMotionSettings.($taskOption[1]) }
    if ($null -ne $taskValue) {
        $taskValue=[double]$taskValue
        if ([double]::IsNaN($taskValue) -or [double]::IsInfinity($taskValue) -or $taskValue -lt $taskOption[3] -or $taskValue -gt $taskOption[4]) { throw "Invalid $($taskOption[1])" }
        $taskArgs+=@($taskOption[2],$taskValue.ToString([Globalization.CultureInfo]::InvariantCulture))
    }
}
if ($OutputWidth) { $taskArgs+=@('--output-width',$OutputWidth.ToString()) }
if ($NoPreview) { $taskArgs+='--no-preview' }
if ($LegacyPreview) { $taskArgs+='--legacy-preview' }
if ($LegacySecondaryResponse) { $taskArgs+='--legacy-secondary-response' }
if ($NoEdgeAA) { $taskArgs+='--no-edge-aa' }
if ($Avatar) { $taskArgs+=@('--avatar',('"'+(Resolve-Path -LiteralPath $Avatar).Path+'"')) }
# The visible Player is the requested interactive window. No camera or capture process.
$taskProcess=Start-Process -FilePath $taskExe -ArgumentList $taskArgs -WorkingDirectory $PSScriptRoot -PassThru -Wait
if ($taskProcess.ExitCode -ne 0) { throw "Avatar exited with code $($taskProcess.ExitCode)" }
