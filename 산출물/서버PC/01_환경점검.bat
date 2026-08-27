@echo off
setlocal EnableDelayedExpansion
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

echo ========================================
echo  Server Environment Check
echo ========================================
echo deploy root: %DEPLOY_ROOT%
echo.

set "HAS_FAIL=0"

where python >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found
    set "HAS_FAIL=1"
) else (
    python --version
    echo [OK] Python
)

where git >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Git not found
    set "HAS_FAIL=1"
) else (
    git --version
    echo [OK] Git
)

if exist "%DEPLOY_ROOT%\frontend\dist\index.html" (
    echo [OK] frontend\dist
) else (
    echo [FAIL] frontend\dist missing
    set "HAS_FAIL=1"
)

set "WHEEL_COUNT=0"
for %%F in ("%DEPLOY_ROOT%\offline_packages\python\*.whl") do set /a WHEEL_COUNT+=1
echo [INFO] offline wheels: !WHEEL_COUNT!
if !WHEEL_COUNT! LSS 1 echo [WARN] no wheels in offline_packages\python

if exist "%DEPLOY_ROOT%\.env" (echo [OK] .env) else (echo [WARN] .env missing)
if exist "%DEPLOY_ROOT%\backend\.venv\Scripts\python.exe" (
    echo [OK] backend\.venv
) else (
    echo [WARN] backend\.venv missing - run 02_offline_install.bat
)

echo.
if "!HAS_FAIL!"=="1" (
    echo [RESULT] FAILED
) else (
    echo [RESULT] OK
)
echo.
pause
endlocal
exit /b 0
