$ErrorActionPreference = 'Stop'
$taskAuthDirectory = Join-Path (Split-Path $PSScriptRoot -Parent) 'results/github-auth'
$taskToken = Read-Host 'Paste the fine-grained GitHub token (input is hidden)' -AsSecureString
if ($taskToken.Length -eq 0) {
    throw 'No token entered. Nothing was saved.'
}
try {
    New-Item -ItemType Directory -Force -Path $taskAuthDirectory | Out-Null
    # Windows DPAPI: only this Windows user can decrypt the saved credential.
    $taskToken | ConvertFrom-SecureString | Set-Content -LiteralPath (Join-Path $taskAuthDirectory 'token.dpapi') -Encoding ASCII
    Write-Host 'Saved encrypted token for this Windows user. Do not send the token in chat.'
} finally {
    $taskToken.Dispose()
}
