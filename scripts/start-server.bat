@echo off
setlocal
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

if not exist ".env" (
    if exist ".env.example" copy /Y ".env.example" ".env" >nul
)

echo Starting production server on port 8010 ...
if not exist "%PROJECT_ROOT%\frontend\dist\index.html" (
    echo [WARN] frontend\dist not found - API only mode. Run scripts\build-frontend.bat first for Web UI.
)
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010

endlocal
