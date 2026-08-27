@echo off
setlocal
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

echo ========================================
echo  Equipment Change Trace - Dev Server
echo ========================================
echo.
echo Backend  : http://localhost:8010
echo Frontend : http://localhost:5173
echo Health   : http://localhost:8010/api/health
echo.

if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from .env.example ...
        copy /Y ".env.example" ".env" >nul
    )
)

echo Starting Backend ...
start "ECT-Backend" cmd /k "cd /d \"%PROJECT_ROOT%\backend\" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload"

timeout /t 2 /nobreak >nul

echo Starting Frontend ...
start "ECT-Frontend" cmd /k "cd /d \"%PROJECT_ROOT%\frontend\" && npm run dev"

echo.
echo Dev servers started in separate windows.
echo Close those windows to stop the servers.
echo.

endlocal
