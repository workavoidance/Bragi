@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install standard 64-bit Python 3.14 from python.org.
  pause
  exit /b 1
)

if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 14) else 1)"
  if errorlevel 1 rmdir /s /q .venv
)

if not exist .venv\Scripts\python.exe (
  py -3.14 -m venv .venv
  if errorlevel 1 goto :failed
)

.venv\Scripts\python.exe tools\bootstrap_dev.py
if errorlevel 1 goto :failed

.venv\Scripts\python.exe tools\dev_runner.py %*
if errorlevel 1 goto :failed
exit /b 0

:failed
echo.
echo Development launcher failed. Read the error above.
pause
exit /b 1
