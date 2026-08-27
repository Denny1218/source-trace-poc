@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%..\tests\test-data"
cd /d "%ROOT%"

call :setup_device device-a "TEST_DEVICE_A"
call :setup_device device-b "TEST_DEVICE_B"

echo Building Git test repositories ...
python "%SCRIPT_DIR%..\tests\test-data\setup_repositories.py"
python "%SCRIPT_DIR%..\tests\test-data\setup_ppt_documents.py"
python "%SCRIPT_DIR%..\tests\test-data\setup_ppt_fixtures.py"

echo Test data setup complete.
exit /b 0

:setup_device
set "DEVICE=%~1"
set "LABEL=%~2"
set "REPO=%ROOT%\%DEVICE%\repository"
set "DOCS=%ROOT%\%DEVICE%\documents"

mkdir "%REPO%" 2>nul
mkdir "%DOCS%" 2>nul

if not exist "%REPO%\.git" (
    echo Initializing Git repo: %REPO%
    git -C "%REPO%" init
    echo # %LABEL% > "%REPO%\README.md"
    git -C "%REPO%" add .
    git -C "%REPO%" -c user.email="test@example.com" -c user.name="Test User" commit -m "Initial commit for %LABEL%"
)

if not exist "%DOCS%\sample.pptx" (
    echo.>"%DOCS%\sample.pptx"
)
if not exist "%DOCS%\sample2.pptx" (
    echo.>"%DOCS%\sample2.pptx"
)

exit /b 0
