$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$PluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = Join-Path $PluginRoot ".env"

if (Test-Path $EnvFile) {
    Get-Content $EnvFile -Encoding utf8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line -match "^([^=]+)=(.*)$") {
            $name = $Matches[1].Trim()
            $value = $Matches[2].Trim().Trim('"').Trim("'")
            Set-Item -Path "Env:$name" -Value $value
        }
    }
} else {
    Write-Host "경고: .env 가 없습니다. .env.example 을 복사해 토큰을 설정하세요." -ForegroundColor Yellow
}

Write-Host "Fitting AI 서버 시작..." -ForegroundColor Cyan
python (Join-Path $PluginRoot "scripts\serve.py")
