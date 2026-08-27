@echo off
setlocal
chcp 65001 >nul 2>&1
cd /d "%~dp0.."
python scripts\package-deploy.py
exit /b %ERRORLEVEL%
