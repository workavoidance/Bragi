$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Building Bragi portable executable..." -ForegroundColor Cyan

if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonLauncher = "py"
    $PythonArgs = @("-3.14")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonLauncher = "python"
    $PythonArgs = @()
} else {
    throw "Python 3.14 was not found. Install it from python.org and run this again."
}

& $PythonLauncher @PythonArgs -c "import sys; assert sys.version_info[:2] == (3, 14), 'Python 3.14 is required'"
if ($LASTEXITCODE -ne 0) { throw "Standard 64-bit Python 3.14 is required." }

& $PythonLauncher @PythonArgs -m venv --clear .build-venv
$BuildPython = Join-Path $PSScriptRoot ".build-venv\Scripts\python.exe"
& $BuildPython -m pip install --upgrade pip
& $BuildPython -m pip install -r requirements-build.txt -c constraints-windows.txt
& $BuildPython tools\create_icon.py

& $BuildPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name WhisperDictate `
    --icon assets\whisper-dictate.ico `
    --paths src `
    --collect-all faster_whisper `
    --collect-all ctranslate2 `
    --collect-all tokenizers `
    --collect-all sounddevice `
    --hidden-import pynput.keyboard._win32 `
    --hidden-import pynput.mouse._win32 `
    src\whisper_dictate\__main__.py

if ($LASTEXITCODE -ne 0) { throw "The portable build failed." }

Write-Host ""
Write-Host "Build complete:" -ForegroundColor Green
Write-Host (Join-Path $PSScriptRoot "dist\WhisperDictate.exe")
Write-Host "The first launch downloads the local multilingual small model once."
