param([ValidateSet('capture','analyze')][string]$Mode='capture',[string]$Take='')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    if ($Mode -eq 'capture') {
        Write-Host 'モデル比較用の元カメラ映像を撮影します。開始ボタンを押すまでは保存しません。'
        & '.\.venv\Scripts\python.exe' -m capture_lab.comparison_capture --camera 1
    } else {
        if (-not $Take) {
            $taskTakes=Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'results\comparison-takes') -Directory | Sort-Object Name -Descending
            foreach ($taskTake in $taskTakes) {
                $taskManifest=Join-Path $taskTake.FullName 'take.json'
                if ((Test-Path -LiteralPath $taskManifest) -and (Get-Content -LiteralPath $taskManifest -Raw -Encoding UTF8 | ConvertFrom-Json).status -eq 'complete') { $Take=$taskTake.FullName;break }
            }
        }
        if (-not $Take) { throw '完了した撮影がありません。先に撮影してください。' }
        Write-Host "同一入力で比較します: $Take"
        & '.\.venv\Scripts\python.exe' -m capture_lab.comparison $Take
    }
    if ($LASTEXITCODE -ne 0) { throw "Comparison exited with code $LASTEXITCODE" }
} finally { Pop-Location }
