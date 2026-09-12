param([string]$Name = 'body-three-models')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if ($Name -notmatch '^[a-zA-Z0-9-]+$') { throw 'Invalid comparison name' }
$taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
$taskSamPython = Join-Path $PSScriptRoot 'assets-source/sam-3d-body-venv/Scripts/python.exe'
$taskCommon = Join-Path $PSScriptRoot 'results/comparisons/first-take'
$taskParent = Get-Content -LiteralPath (Join-Path $taskCommon 'report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskTake = $taskParent.take
$taskMhr = Join-Path $PSScriptRoot 'assets-source/sam-3d-body-dinov3/assets/mhr_model.pt'
$taskCandidates = @('dinov3','vith')
foreach ($taskVariant in $taskCandidates) {
    $taskAssets = Join-Path $PSScriptRoot "assets-source/sam-3d-body-$taskVariant"
    foreach ($taskFile in @('model.ckpt','model_config.yaml')) {
        if (-not (Test-Path -LiteralPath (Join-Path $taskAssets $taskFile))) {
            Write-Host "Save $taskFile in $taskAssets"
            Write-Host "https://huggingface.co/facebook/sam-3d-body-$taskVariant/resolve/main/$($taskFile)?download=true"
            throw 'Required model asset missing; no camera recording started.'
        }
    }
}
foreach ($taskVariant in $taskCandidates) {
    $taskAssets = Join-Path $PSScriptRoot "assets-source/sam-3d-body-$taskVariant"
    $taskRaw = Join-Path $PSScriptRoot "results/comparisons/first-take-sam-$taskVariant"
    if (Test-Path -LiteralPath $taskRaw) {
        $taskRawReport = Get-Content -LiteralPath (Join-Path $taskRaw 'report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($taskRawReport.status -ne 'complete') { throw "Raw run is $($taskRawReport.status): $taskRaw. Check its existing process/log before starting another run." }
        $taskHash = (Get-FileHash -LiteralPath (Join-Path $taskAssets 'model.ckpt') -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($taskHash -ne $taskRawReport.checkpoint_sha256) { throw 'Cached checkpoint differs from current file' }
        if ($taskRawReport.video_sha256 -ne $taskParent.source_video_sha256 -or $taskRawReport.controls_sha256 -ne $taskParent.controls.sha256) { throw 'Cached input provenance differs' }
        Write-Host "Reusing completed SAM $taskVariant predictions"
    } else {
        & $taskSamPython tools/compare_external_model.py sam3d --repo assets-source/sam-3d-body-code --checkpoint (Join-Path $taskAssets 'model.ckpt') --mhr $taskMhr --dinov3-repo assets-source/dinov3 --take $taskTake --common $taskCommon --output $taskRaw --keep-cuda-cache --torch-threads 1
        if ($LASTEXITCODE -ne 0) { throw "SAM $taskVariant inference failed" }
    }
}
$taskComparison = Join-Path $PSScriptRoot "results/comparisons/$Name"
if (-not (Test-Path -LiteralPath $taskComparison)) {
    & $taskPython tools/compare_body_models.py --common $taskCommon --candidate sam-dinov3=results/comparisons/first-take-sam-dinov3 --candidate sam-vith=results/comparisons/first-take-sam-vith --output $taskComparison
    if ($LASTEXITCODE -ne 0) { throw 'Body comparison failed' }
} else {
    $taskComparisonReport = Get-Content -LiteralPath (Join-Path $taskComparison 'report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($taskComparisonReport.status -ne 'complete' -or $taskComparisonReport.partial_test) { throw "Incomplete comparison: $taskComparison" }
}
$taskVideos = Join-Path $PSScriptRoot "results/avatar-videos/$Name"
if (-not (Test-Path -LiteralPath $taskVideos)) {
    & $taskPython tools/render_comparison_videos.py --comparison $taskComparison --output $taskVideos
    if ($LASTEXITCODE -ne 0) { throw 'Video rendering failed' }
} else {
    $taskVideoReport = Get-Content -LiteralPath (Join-Path $taskVideos 'report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($taskVideoReport.status -ne 'complete') { throw "Incomplete videos: $taskVideos" }
}
Write-Host "Complete: $taskVideos"
Invoke-Item -LiteralPath $taskVideos
