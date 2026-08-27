@echo off
setlocal
chcp 65001 >nul 2>&1

echo ========================================
echo  Stop Server (port 8010)
echo ========================================
echo.

powershell -NoProfile -Command "$conns = Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue; if (-not $conns) { Write-Host '[INFO] no listener on 8010'; exit 0 }; $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($procId in $pids) { try { Stop-Process -Id $procId -Force -ErrorAction Stop; Write-Host ('[OK] stopped PID ' + $procId) } catch { Write-Host ('[FAIL] stop PID ' + $procId + ': ' + $_.Exception.Message); exit 1 } }; exit 0"
set "ERR=%ERRORLEVEL%"
echo.
if not "%ERR%"=="0" (
    echo [RESULT] FAIL
    pause
    exit /b 1
)
echo [RESULT] STOPPED
pause
endlocal
exit /b 0
