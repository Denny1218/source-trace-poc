@echo off
setlocal
chcp 65001 >nul 2>&1

set "DEPLOY_ROOT="
set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

if exist "%HERE%\..\frontend\dist\index.html" (
    for %%I in ("%HERE%\..") do set "DEPLOY_ROOT=%%~fI"
    goto :root_ok
)
if exist "%HERE%\deploy\frontend\dist\index.html" (
    for %%I in ("%HERE%\deploy") do set "DEPLOY_ROOT=%%~fI"
    goto :root_ok
)
if exist "%HERE%\frontend\dist\index.html" (
    set "DEPLOY_ROOT=%HERE%"
    goto :root_ok
)
echo [FAIL] deploy root not found
echo Run from deploy\scripts or copy deploy folder completely.
pause
exit /b 1

:root_ok

cd /d "%DEPLOY_ROOT%"

if not exist ".env" (
    if exist ".env.example" copy /Y ".env.example" ".env" >nul
)

if not exist "frontend\dist\index.html" (
    echo [WARN] frontend\dist missing - API only mode
)

echo ========================================
echo  Equipment Change Trace Server
echo  http://0.0.0.0:8010
echo ========================================
echo deploy root: %DEPLOY_ROOT%
echo.

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] run 02_offline_install.bat first
    pause
    exit /b 1
)

cd backend
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010

endlocal
