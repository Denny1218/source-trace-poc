@echo off
setlocal
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%\backend"

echo Running backend tests ...
python -m pytest tests\ -v
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE% equ 0 (
    echo All tests passed.
) else (
    echo Tests failed with exit code %EXIT_CODE%.
)

endlocal
exit /b %EXIT_CODE%
