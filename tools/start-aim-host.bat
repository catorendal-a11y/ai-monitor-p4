@echo off
title AI Monitor Host
setlocal
echo Starting AI Monitor Host...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-aim-host.ps1"
if errorlevel 1 (
  echo Host startup failed. Check Python and pyserial.
  timeout /t 5 /nobreak >nul
  exit /b 1
)
exit /b 0
