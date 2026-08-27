@echo off
setlocal
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."
set "LOCK=%ROOT%\backend\requirements-lock.txt"
set "OUT=%ROOT%\offline_packages\python"

mkdir "%OUT%" 2>nul

if exist "%OUT%\*" (
    echo Cleaning existing wheels in %OUT% ...
    del /q "%OUT%\*"
)

(
echo fastapi==0.139.0
echo uvicorn[standard]==0.49.0
echo httpx==0.28.1
echo python-dotenv==1.2.2
echo python-pptx==1.0.2
echo annotated-doc==0.0.4
echo annotated-types==0.7.0
echo anyio==4.13.0
echo certifi==2026.5.20
echo click==8.4.1
echo colorama==0.4.6
echo h11==0.16.0
echo httpcore==1.0.9
echo httptools==0.8.0
echo idna==3.18
echo lxml==6.1.1
echo pillow==12.2.0
echo pydantic==2.13.4
echo pydantic_core==2.46.4
echo PyYAML==6.0.3
echo starlette==1.2.1
echo typing-inspection==0.4.2
echo typing_extensions==4.15.0
echo watchfiles==1.2.0
echo websockets==16.0
echo xlsxwriter==3.2.9
) > "%LOCK%"

echo Downloading wheels to %OUT% ...
pip download -r "%LOCK%" -d "%OUT%"
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE%==0 (
    echo Offline packages ready.
) else (
    echo pip download failed with exit code %EXIT_CODE%
)

endlocal
exit /b %EXIT_CODE%
