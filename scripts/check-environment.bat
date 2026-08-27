@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

echo ========================================
echo  Equipment Change Trace - Environment Check
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

echo [1/6] Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL - Python not found
    set "PYTHON_OK=0"
) else (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   OK - %%v
    set "PYTHON_OK=1"
)
echo.

echo [2/6] Git
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL - Git not found
    set "GIT_OK=0"
) else (
    for /f "tokens=*" %%v in ('git --version 2^>^&1') do echo   OK - %%v
    set "GIT_OK=1"
)
echo.

echo [3/6] Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL - Node.js not found
    set "NODE_OK=0"
) else (
    for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo   OK - Node %%v
    set "NODE_OK=1"
)
echo.

echo [4/6] Ollama
curl -s -o nul -w "%%{http_code}" --connect-timeout 3 http://127.0.0.1:11434/api/tags > "%TEMP%\ollama_check.txt" 2>nul
set /p OLLAMA_CODE=<"%TEMP%\ollama_check.txt"
del "%TEMP%\ollama_check.txt" 2>nul
if "!OLLAMA_CODE!"=="200" (
    echo   OK - Ollama reachable at http://127.0.0.1:11434
    set "OLLAMA_OK=1"
) else (
    echo   WARN - Ollama unavailable ^(optional for STEP 0^)
    set "OLLAMA_OK=0"
)
echo.

echo [5/6] Port 8010
netstat -ano | findstr ":8010 " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   WARN - Port 8010 is already in use
    netstat -ano | findstr ":8010 " | findstr "LISTENING"
    set "PORT_OK=0"
) else (
    echo   OK - Port 8010 is available
    set "PORT_OK=1"
)
echo.

echo [6/6] Project directories
if exist "data" (echo   OK - data/) else (echo   WARN - data/ missing)
if exist "logs" (echo   OK - logs/) else (echo   WARN - logs/ missing)
if exist "backend\app\main.py" (echo   OK - backend/) else (echo   FAIL - backend/ missing)
if exist "frontend\package.json" (echo   OK - frontend/) else (echo   FAIL - frontend/ missing)
echo.

echo ========================================
echo  Summary
echo ========================================
if "!PYTHON_OK!"=="1" (echo   Python   : OK) else (echo   Python   : FAIL)
if "!GIT_OK!"=="1" (echo   Git      : OK) else (echo   Git      : FAIL)
if "!NODE_OK!"=="1" (echo   Node     : OK) else (echo   Node     : FAIL)
if "!OLLAMA_OK!"=="1" (echo   Ollama   : OK) else (echo   Ollama   : unavailable)
if "!PORT_OK!"=="1" (echo   Port8010 : available) else (echo   Port8010 : in use)
echo ========================================
echo.

endlocal
