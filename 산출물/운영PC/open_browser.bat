@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

set "DIR=%~dp0"
set "HOST=localhost"
set "PORT=8010"

if exist "%DIR%server_host.txt" (
    for /f "usebackq delims=" %%a in ("%DIR%server_host.txt") do (
        set "LINE=%%a"
        if not "!LINE!"=="" if not "!LINE:~0,1!"=="#" (
            set "HOST=!LINE!"
            goto :found
        )
    )
)
:found

set "URL=http://%HOST%:%PORT%"

echo ========================================
echo  Equipment Change Trace - Open Browser
echo  %URL%
echo ========================================
echo.

echo Checking Health ...
powershell -NoProfile -Command "try { $r = Invoke-RestMethod '%URL%/api/health' -TimeoutSec 5; Write-Host '[OK]' $r.status } catch { Write-Host '[FAIL]' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo.
    echo Cannot connect to the server.
    echo - Check IP in server_host.txt
    echo - Confirm 03_start_server.bat / 03_서버시작.bat is running on the server PC
    echo - Confirm firewall allows TCP 8010
    pause
    exit /b 1
)

echo Opening browser ...
start "" "%URL%"

endlocal
