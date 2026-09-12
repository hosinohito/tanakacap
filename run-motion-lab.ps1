param([string]$Avatar,[ValidateRange(64,4096)][int]$OutputHeight=1080,
    [ValidateRange(64,4096)][int]$OutputWidth,
    [switch]$NoPreview,
    [switch]$LegacyPreview,
    [ValidateRange(0,1)][double]$MouthCornerEmphasis=0,
    [switch]$LegacySecondaryResponse,
    [switch]$NoEdgeAA)
$ErrorActionPreference='Stop'
$taskExe=Join-Path $PSScriptRoot 'builds/lab/TanakaCap.exe'
if (-not (Test-Path -LiteralPath $taskExe)) { throw 'Run build-unity-lab.ps1 first.' }
$taskArgs=@('--motion-demo','-nolog')
$taskArgs+=@('--output-height',$OutputHeight.ToString())
if (-not $PSBoundParameters.ContainsKey('MouthCornerEmphasis')) {
    $taskMotionSettings=Get-Content (Join-Path $PSScriptRoot 'tracking-settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($taskMotionSettings.PSObject.Properties.Name -contains 'mouth_corner_emphasis') { $MouthCornerEmphasis=[double]$taskMotionSettings.mouth_corner_emphasis }
}
if ([double]::IsNaN($MouthCornerEmphasis) -or $MouthCornerEmphasis -lt 0 -or $MouthCornerEmphasis -gt 1) { throw 'mouth_corner_emphasis must be 0..1' }
$taskArgs+=@('--mouth-corner-emphasis',$MouthCornerEmphasis.ToString([Globalization.CultureInfo]::InvariantCulture))
if ($OutputWidth) { $taskArgs+=@('--output-width',$OutputWidth.ToString()) }
if ($NoPreview) { $taskArgs+='--no-preview' }
if ($LegacyPreview) { $taskArgs+='--legacy-preview' }
if ($LegacySecondaryResponse) { $taskArgs+='--legacy-secondary-response' }
if ($NoEdgeAA) { $taskArgs+='--no-edge-aa' }
if ($Avatar) { $taskArgs+=@('--avatar',('"'+(Resolve-Path -LiteralPath $Avatar).Path+'"')) }
# The visible Player is the requested interactive window. No camera or capture process.
$taskProcess=Start-Process -FilePath $taskExe -ArgumentList $taskArgs -WorkingDirectory $PSScriptRoot -PassThru -Wait
if ($taskProcess.ExitCode -ne 0) { throw "Avatar exited with code $($taskProcess.ExitCode)" }
