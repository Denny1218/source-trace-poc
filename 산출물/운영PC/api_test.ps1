# STEP 6 Operator PC API smoke test
# Usage: powershell -ExecutionPolicy Bypass -File api_test.ps1
# Encoding: UTF-8 with BOM (required for Korean strings on Windows PowerShell 5.x)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hostFile = Join-Path $scriptDir "server_host.txt"
$baseHost = "localhost"

if (Test-Path -LiteralPath $hostFile) {
    $line = Get-Content -LiteralPath $hostFile -Encoding UTF8 |
        Where-Object { $_ -and -not $_.StartsWith("#") } |
        Select-Object -First 1
    if ($line) { $baseHost = $line.Trim() }
}

$baseUrl = "http://${baseHost}:8010"
Write-Host "========================================"
Write-Host " API test target: $baseUrl"
Write-Host "========================================"
Write-Host ""

function Test-Api {
    param([string]$Name, [scriptblock]$Block)
    try {
        & $Block
        Write-Host "[PASS] $Name" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $Name - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Test-Api "Health" {
    $r = Invoke-RestMethod "$baseUrl/api/health"
    if ($r.status -ne "ok") { throw "status not ok" }
}

Test-Api "Equipment list" {
    Invoke-RestMethod "$baseUrl/api/equipment" | Out-Null
}

$equipmentId = 1
Test-Api "Trace Search" {
    $body = @{
        equipment_id = $equipmentId
        query        = "CalcFare 함수가 왜 변경됐어?"
        file_path    = "FareCalc.c"
    } | ConvertTo-Json
    $r = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/trace/search" `
        -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
    if (-not $r.search_context) { throw "no search_context" }
}

Test-Api "PPT Candidates" {
    $body = @{
        equipment_id = $equipmentId
        keywords     = @("어린이", "요금", "CHILD_FARE")
        date_from    = "2024-01-01"
        date_to      = "2024-12-31"
    } | ConvertTo-Json
    Invoke-RestMethod -Method POST -Uri "$baseUrl/api/trace/ppt-candidates" `
        -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) | Out-Null
}

Test-Api "PPT Analysis" {
    $body = @{
        equipment_id = $equipmentId
        keywords     = @("어린이", "요금", "CHILD_FARE")
        date_from    = "2024-01-01"
        date_to      = "2024-12-31"
    } | ConvertTo-Json
    $r = Invoke-RestMethod -Method POST -Uri "$baseUrl/api/trace/ppt-analysis" `
        -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
    Write-Host "       processed=$($r.processed_documents) cache_hits=$($r.cache_hits)"
}

Test-Api "PPT Cache list" {
    Invoke-RestMethod "$baseUrl/api/equipment/$equipmentId/ppt-cache" | Out-Null
}

Write-Host ""
Write-Host "Done. Assumes equipment_id=1. Some FAIL is OK if equipment is not registered."
Write-Host "Browser UI: $baseUrl"
