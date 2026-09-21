param([ValidateSet('capture','analyze')][string]$Mode='capture',[string]$Take='',[ValidateSet('body','face-head')][string]$Profile='body')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    if ($Mode -eq 'capture') {
        Write-Host 'モデル比較用の元カメラ映像を撮影します。開始ボタンを押すまでは保存しません。'
        & '.\.venv\Scripts\python.exe' -m tanakacap.comparison_capture --profile $Profile
    } else {
        if (-not $Take) {
            $taskTakes=@()
            $taskTakesRoot=Join-Path $PSScriptRoot 'results\comparison-takes'
            if (Test-Path -LiteralPath $taskTakesRoot -PathType Container) {
                $taskTakes=Get-ChildItem -LiteralPath $taskTakesRoot -Directory | Sort-Object Name -Descending
            }
            foreach ($taskTake in $taskTakes) {
                $taskManifest=Join-Path $taskTake.FullName 'take.json'
                if ((Test-Path -LiteralPath $taskManifest) -and (Get-Content -LiteralPath $taskManifest -Raw -Encoding UTF8 | ConvertFrom-Json).status -eq 'complete') { $Take=$taskTake.FullName;break }
            }
        }
        if (-not $Take) {
            Write-Host 'これは撮影後に使う解析用バッチです。まだ完了した撮影がありません。'
            Write-Host 'デスクトップの tanakacap-compare-capture.bat を開き、撮影開始を押してください。'
            return
        }
        Write-Host "同一入力で比較します: $Take"
        & '.\.venv\Scripts\python.exe' -m tanakacap.comparison $Take
    }
    if ($LASTEXITCODE -ne 0) { throw "Comparison exited with code $LASTEXITCODE" }
} finally { Pop-Location }
