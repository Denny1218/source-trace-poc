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

cd /d "%DEPLOY_ROOT%\backend"

echo ========================================
echo  Python Offline Install
echo ========================================
echo deploy root: %DEPLOY_ROOT%
echo.

if not exist "%DEPLOY_ROOT%\offline_packages\python\*.whl" (
    echo [ERROR] no wheels in offline_packages\python
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Creating venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [FAIL] venv creation failed
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [FAIL] venv activation failed
    pause
    exit /b 1
)

pip install --no-index --find-links=..\offline_packages\python -r requirements-lock.txt
if errorlevel 1 (
    echo [FAIL] pip install failed
    pause
    exit /b 1
)

python -c "import fastapi, pptx; print('import ok')"
if errorlevel 1 (
    echo [FAIL] import test failed
    pause
    exit /b 1
)

echo [OK] install complete
pause
endlocal
exit /b 0
