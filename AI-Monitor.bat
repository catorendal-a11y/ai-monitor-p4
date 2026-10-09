@echo off
setlocal
title AI Monitor P4
cd /d "%~dp0"
if exist "%~dp0AI-Monitor.exe" (
  "%~dp0AI-Monitor.exe"
  exit /b
)
if not exist "%~dp0.venv\Scripts\python.exe" (
  "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
  if errorlevel 1 goto failed
)
"%~dp0.venv\Scripts\python.exe" -c "import serial, psutil" >nul 2>&1
if errorlevel 1 (
  "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
  if errorlevel 1 goto failed
)
"%~dp0.venv\Scripts\python.exe" "%~dp0tools\aim_control.py"
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Setup or startup failed. Read the message above, then try again.
pause
exit /b 1
