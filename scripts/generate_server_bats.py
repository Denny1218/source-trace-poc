"""Generate ASCII-only server batch files (CP949/UTF-8 safe on Windows cmd)."""

from __future__ import annotations

from pathlib import Path

ROOT_BLOCK = r"""set "DEPLOY_ROOT="
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
"""

CHECK_BAT = (
    "@echo off\r\n"
    "setlocal EnableDelayedExpansion\r\n"
    "chcp 65001 >nul 2>&1\r\n"
    "\r\n"
    + ROOT_BLOCK.replace("\n", "\r\n")
    + "\r\n"
    "cd /d \"%DEPLOY_ROOT%\"\r\n"
    "\r\n"
    "echo ========================================\r\n"
    "echo  Server Environment Check\r\n"
    "echo ========================================\r\n"
    "echo deploy root: %DEPLOY_ROOT%\r\n"
    "echo.\r\n"
    "\r\n"
    "set \"HAS_FAIL=0\"\r\n"
    "\r\n"
    "where python >nul 2>&1\r\n"
    "if errorlevel 1 (\r\n"
    "    echo [FAIL] Python not found\r\n"
    "    set \"HAS_FAIL=1\"\r\n"
    ") else (\r\n"
    "    python --version\r\n"
    "    echo [OK] Python\r\n"
    ")\r\n"
    "\r\n"
    "where git >nul 2>&1\r\n"
    "if errorlevel 1 (\r\n"
    "    echo [FAIL] Git not found\r\n"
    "    set \"HAS_FAIL=1\"\r\n"
    ") else (\r\n"
    "    git --version\r\n"
    "    echo [OK] Git\r\n"
    ")\r\n"
    "\r\n"
    "if exist \"%DEPLOY_ROOT%\\frontend\\dist\\index.html\" (\r\n"
    "    echo [OK] frontend\\dist\r\n"
    ") else (\r\n"
    "    echo [FAIL] frontend\\dist missing\r\n"
    "    set \"HAS_FAIL=1\"\r\n"
    ")\r\n"
    "\r\n"
    "set \"WHEEL_COUNT=0\"\r\n"
    "for %%F in (\"%DEPLOY_ROOT%\\offline_packages\\python\\*.whl\") do set /a WHEEL_COUNT+=1\r\n"
    "echo [INFO] offline wheels: !WHEEL_COUNT!\r\n"
    "if !WHEEL_COUNT! LSS 1 echo [WARN] no wheels in offline_packages\\python\r\n"
    "\r\n"
    "if exist \"%DEPLOY_ROOT%\\.env\" (echo [OK] .env) else (echo [WARN] .env missing)\r\n"
    "if exist \"%DEPLOY_ROOT%\\backend\\.venv\\Scripts\\python.exe\" (\r\n"
    "    echo [OK] backend\\.venv\r\n"
    ") else (\r\n"
    "    echo [WARN] backend\\.venv missing - run 02_offline_install.bat\r\n"
    ")\r\n"
    "\r\n"
    "echo.\r\n"
    "if \"!HAS_FAIL!\"==\"1\" (\r\n"
    "    echo [RESULT] FAILED\r\n"
    ") else (\r\n"
    "    echo [RESULT] OK\r\n"
    ")\r\n"
    "echo.\r\n"
    "pause\r\n"
    "endlocal\r\n"
    "exit /b 0\r\n"
)

INSTALL_BAT = (
    "@echo off\r\n"
    "setlocal\r\n"
    "chcp 65001 >nul 2>&1\r\n"
    "\r\n"
    + ROOT_BLOCK.replace("\n", "\r\n")
    + "\r\n"
    "cd /d \"%DEPLOY_ROOT%\\backend\"\r\n"
    "\r\n"
    "echo ========================================\r\n"
    "echo  Python Offline Install\r\n"
    "echo ========================================\r\n"
    "echo deploy root: %DEPLOY_ROOT%\r\n"
    "echo.\r\n"
    "\r\n"
    "if not exist \"%DEPLOY_ROOT%\\offline_packages\\python\\*.whl\" (\r\n"
    "    echo [ERROR] no wheels in offline_packages\\python\r\n"
    "    pause\r\n"
    "    exit /b 1\r\n"
    ")\r\n"
    "\r\n"
    "if not exist \".venv\" (\r\n"
    "    echo Creating venv ...\r\n"
    "    python -m venv .venv\r\n"
    "    if errorlevel 1 (\r\n"
    "        echo [FAIL] venv creation failed\r\n"
    "        pause\r\n"
    "        exit /b 1\r\n"
    "    )\r\n"
    ")\r\n"
    "\r\n"
    "call .venv\\Scripts\\activate.bat\r\n"
    "if errorlevel 1 (\r\n"
    "    echo [FAIL] venv activation failed\r\n"
    "    pause\r\n"
    "    exit /b 1\r\n"
    ")\r\n"
    "\r\n"
    "pip install --no-index --find-links=..\\offline_packages\\python -r requirements-lock.txt\r\n"
    "if errorlevel 1 (\r\n"
    "    echo [FAIL] pip install failed\r\n"
    "    pause\r\n"
    "    exit /b 1\r\n"
    ")\r\n"
    "\r\n"
    "python -c \"import fastapi, pptx; print('import ok')\"\r\n"
    "if errorlevel 1 (\r\n"
    "    echo [FAIL] import test failed\r\n"
    "    pause\r\n"
    "    exit /b 1\r\n"
    ")\r\n"
    "\r\n"
    "echo [OK] install complete\r\n"
    "pause\r\n"
    "endlocal\r\n"
    "exit /b 0\r\n"
)

START_BAT = (
    "@echo off\r\n"
    "setlocal\r\n"
    "chcp 65001 >nul 2>&1\r\n"
    "\r\n"
    + ROOT_BLOCK.replace("\n", "\r\n")
    + "\r\n"
    "cd /d \"%DEPLOY_ROOT%\"\r\n"
    "\r\n"
    "if not exist \".env\" (\r\n"
    "    if exist \".env.example\" copy /Y \".env.example\" \".env\" >nul\r\n"
    ")\r\n"
    "\r\n"
    "if not exist \"frontend\\dist\\index.html\" (\r\n"
    "    echo [WARN] frontend\\dist missing - API only mode\r\n"
    ")\r\n"
    "\r\n"
    "echo ========================================\r\n"
    "echo  Equipment Change Trace Server\r\n"
    "echo  http://0.0.0.0:8010\r\n"
    "echo ========================================\r\n"
    "echo deploy root: %DEPLOY_ROOT%\r\n"
    "echo.\r\n"
    "\r\n"
    "if not exist \"backend\\.venv\\Scripts\\python.exe\" (\r\n"
    "    echo [ERROR] run 02_offline_install.bat first\r\n"
    "    pause\r\n"
    "    exit /b 1\r\n"
    ")\r\n"
    "\r\n"
    "cd backend\r\n"
    "call .venv\\Scripts\\activate.bat\r\n"
    "python -m uvicorn app.main:app --host 0.0.0.0 --port 8010\r\n"
    "\r\n"
    "endlocal\r\n"
)

STATUS_BAT = (
    "@echo off\r\n"
    "setlocal\r\n"
    "chcp 65001 >nul 2>&1\r\n"
    "\r\n"
    "echo ========================================\r\n"
    "echo  Server Status Check\r\n"
    "echo ========================================\r\n"
    "echo.\r\n"
    "\r\n"
    "powershell -NoProfile -Command \"try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8010/api/health' -UseBasicParsing -TimeoutSec 5; Write-Host ('[OK] health ' + $r.StatusCode + ' ' + $r.Content); exit 0 } catch { Write-Host '[FAIL] server not reachable on http://127.0.0.1:8010'; exit 1 }\"\r\n"
    "set \"ERR=%ERRORLEVEL%\"\r\n"
    "echo.\r\n"
    "if not \"%ERR%\"==\"0\" (\r\n"
    "    echo [RESULT] DOWN\r\n"
    "    pause\r\n"
    "    exit /b 1\r\n"
    ")\r\n"
    "echo [RESULT] UP\r\n"
    "pause\r\n"
    "endlocal\r\n"
    "exit /b 0\r\n"
)

STOP_BAT = (
    "@echo off\r\n"
    "setlocal\r\n"
    "chcp 65001 >nul 2>&1\r\n"
    "\r\n"
    "echo ========================================\r\n"
    "echo  Stop Server (port 8010)\r\n"
    "echo ========================================\r\n"
    "echo.\r\n"
    "\r\n"
    "powershell -NoProfile -Command \"$conns = Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue; if (-not $conns) { Write-Host '[INFO] no listener on 8010'; exit 0 }; $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($procId in $pids) { try { Stop-Process -Id $procId -Force -ErrorAction Stop; Write-Host ('[OK] stopped PID ' + $procId) } catch { Write-Host ('[FAIL] stop PID ' + $procId + ': ' + $_.Exception.Message); exit 1 } }; exit 0\"\r\n"
    "set \"ERR=%ERRORLEVEL%\"\r\n"
    "echo.\r\n"
    "if not \"%ERR%\"==\"0\" (\r\n"
    "    echo [RESULT] FAIL\r\n"
    "    pause\r\n"
    "    exit /b 1\r\n"
    ")\r\n"
    "echo [RESULT] STOPPED\r\n"
    "pause\r\n"
    "endlocal\r\n"
    "exit /b 0\r\n"
)

FILES = {
    "01_env_check.bat": CHECK_BAT,
    "02_offline_install.bat": INSTALL_BAT,
    "03_start_server.bat": START_BAT,
    "04_status_check.bat": STATUS_BAT,
    "05_stop_server.bat": STOP_BAT,
}

# Korean filenames for user-facing copies (same ASCII content)
KOREAN_ALIASES = {
    "01_환경점검.bat": CHECK_BAT,
    "02_오프라인설치.bat": INSTALL_BAT,
    "03_서버시작.bat": START_BAT,
    "04_상태확인.bat": STATUS_BAT,
    "05_서버중지.bat": STOP_BAT,
}


def write_bat(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # ASCII only - safe for cmd.exe on any Windows code page
    path.write_bytes(content.encode("ascii"))


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    server_dir = project / "산출물" / "서버PC"

    for name, content in {**FILES, **KOREAN_ALIASES}.items():
        write_bat(server_dir / name, content)
        print(f"written: {server_dir / name}")

    print("Done. Re-run package-deploy.py to refresh deploy\\scripts")


if __name__ == "__main__":
    main()
