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

.venv\Scripts\python.exe -m pip install -r requirements.txt -c constraints-windows.txt
if errorlevel 1 goto :failed
.venv\Scripts\python.exe -m pip install -e . -c constraints-windows.txt
if errorlevel 1 goto :failed
start "" .venv\Scripts\pythonw.exe -m whisper_dictate
exit /b 0

:failed
echo.
echo Setup failed. Read the error above.
pause
exit /b 1
