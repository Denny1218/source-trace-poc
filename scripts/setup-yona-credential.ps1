# Yona Git Credential setup (run once on server PC as Backend service account).
# Uses Git Credential Manager (credential.helper=manager) → Windows Credential Manager.
# Does NOT use credential.helper=store (plaintext). Password is not saved in .env/SQLite.

param(
    [Parameter(Mandatory = $true)]
    [string]$YonaHost,

    [string]$YonaUsername = $env:YONA_DEFAULT_USERNAME
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($YonaUsername)) {
    Write-Error "YONA_DEFAULT_USERNAME이 설정되지 않았습니다. .env 또는 -YonaUsername으로 지정하세요."
}

$helpers = git config --show-origin --get-all credential.helper 2>$null
Write-Host "현재 credential.helper:"
if ($helpers) {
    $helpers | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "  (없음 — Git for Windows 설치 및 manager helper 확인 필요)"
}

Write-Host ""
Write-Host "Yona Git Credential 설정"
Write-Host "Host: $YonaHost"
Write-Host "Username (YONA_DEFAULT_USERNAME): $YonaUsername"
Write-Host ""

$secure = Read-Host "Yona Password" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}

if ([string]::IsNullOrWhiteSpace($password)) {
    Write-Error "Password가 비어 있습니다."
}

$input = @(
    "protocol=http",
    "host=$YonaHost",
    "username=$YonaUsername",
    "password=$password"
) -join "`n"

$input | git credential approve
if ($LASTEXITCODE -ne 0) {
    Write-Error "git credential approve 실패 (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "Credential 저장 완료 (Git Credential Manager / Windows Credential Manager)."
Write-Host "Backend .env에 YONA_DEFAULT_USERNAME=$YonaUsername 설정을 확인하세요."
Write-Host "Password는 Backend/SQLite/.env/API/브라우저에 저장되지 않습니다."
