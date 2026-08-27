@echo off
setlocal
chcp 65001 >nul 2>&1

echo ========================================
echo  Server Status Check
echo ========================================
echo.

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8010/api/health' -UseBasicParsing -TimeoutSec 5; Write-Host ('[OK] health ' + $r.StatusCode + ' ' + $r.Content); exit 0 } catch { Write-Host '[FAIL] server not reachable on http://127.0.0.1:8010'; exit 1 }"
set "ERR=%ERRORLEVEL%"
echo.
if not "%ERR%"=="0" (
    echo [RESULT] DOWN
    pause
    exit /b 1
)
echo [RESULT] UP
pause
endlocal
exit /b 0
