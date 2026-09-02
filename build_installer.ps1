param(
    [string]$Version = "0.1.0",
    [string]$BuildId = "",
    [switch]$Development
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Version = $Version -replace '^v', ''
if ($Version -notmatch '^[0-9]+\.[0-9]+\.[0-9]+(?:[-.][0-9A-Za-z.-]+)?$') {
    throw "Installer version must start with three numeric parts, for example 0.2.0."
}
if (-not $BuildId) {
    $BuildId = $Version
}

Write-Host "Building Skrivi Windows installer..." -ForegroundColor Cyan

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

$InstallerDist = Join-Path $PSScriptRoot "dist\installed"
$InstallerWork = Join-Path $PSScriptRoot "build\installer"
$InstallerSpec = Join-Path $PSScriptRoot "build\installer-spec"
$IconPath = Join-Path $PSScriptRoot "assets\skrivi.ico"
New-Item -ItemType Directory -Path $InstallerDist, $InstallerWork, $InstallerSpec -Force | Out-Null

& $BuildPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --contents-directory runtime `
    --windowed `
    --name Skrivi `
    --icon $IconPath `
    --paths src `
    --distpath $InstallerDist `
    --workpath $InstallerWork `
    --specpath $InstallerSpec `
    --collect-all faster_whisper `
    --collect-all ctranslate2 `
    --collect-all tokenizers `
    --collect-all sounddevice `
    --hidden-import pynput.keyboard._win32 `
    --hidden-import pynput.mouse._win32 `
    src\whisper_dictate\__main__.py

if ($LASTEXITCODE -ne 0) { throw "The installed application build failed." }

$ApplicationDir = Join-Path $InstallerDist "Skrivi"
@{
    build_id = $BuildId
    development = [bool]$Development
} | ConvertTo-Json | Set-Content (Join-Path $ApplicationDir "BUILD_INFO.json") -Encoding utf8

$InnoCandidates = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path $_) }
$InnoCompiler = $InnoCandidates | Select-Object -First 1
if (-not $InnoCompiler) {
    throw "Inno Setup 6 was not found. Install it and run this build again."
}

$InstallerOutput = Join-Path $PSScriptRoot "dist\installer"
New-Item -ItemType Directory -Path $InstallerOutput -Force | Out-Null
$env:SKRIVI_INSTALLER_VERSION = $Version
$env:SKRIVI_INSTALLER_SOURCE = $ApplicationDir
$env:SKRIVI_INSTALLER_OUTPUT = $InstallerOutput
$env:SKRIVI_PROJECT_ROOT = $PSScriptRoot

& $InnoCompiler "installer\Skrivi.iss"
if ($LASTEXITCODE -ne 0) { throw "The installer build failed." }

$OutputName = "Skrivi-$Version-windows-x64-setup.exe"
Write-Host ""
Write-Host "Installer complete:" -ForegroundColor Green
Write-Host (Join-Path $InstallerOutput $OutputName)
