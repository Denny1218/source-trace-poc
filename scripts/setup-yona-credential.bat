@echo off
REM Yona Git Credential one-time setup (Windows Credential Manager via git credential approve)
REM Usage: setup-yona-credential.bat <host:port> <username>
REM Example: setup-yona-credential.bat 192.168.155.89:9000 source_trace

setlocal
if "%~2"=="" (
  echo Usage: %~nx0 ^<host:port^> ^<username^>
  echo Example: %~nx0 192.168.155.89:9000 source_trace
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-yona-credential.ps1" -YonaHost "%~1" -YonaUsername "%~2"
exit /b %ERRORLEVEL%
