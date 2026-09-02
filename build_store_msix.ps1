param(
    [string]$Version = "",
    [ValidateRange(1, 65535)]
    [int]$StoreBuild = 1,
    [string]$ExecutablePath = "",
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $Version) {
    $Version = (Get-Content release\VERSION -Raw).Trim()
}

$match = [regex]::Match(
    $Version,
    '^v(?<major>[0-9]+)\.(?<minor>[0-9]+)\.(?<patch>[0-9]+)(?:-[0-9A-Za-z.-]+)?$'
)
if (-not $match.Success) {
    throw "Version must look like v0.2.0 or v0.2.0-alpha.2."
}

# Store package versions must start above zero and reserve the fourth field for
# Microsoft. The workflow run number keeps every package update monotonic even
# when several prereleases share the same product version.
$packageMajor = [int]$match.Groups["major"].Value + 1
$packageMinor = [int]$match.Groups["minor"].Value
if ($packageMajor -gt 65535 -or $packageMinor -gt 65535) {
    throw "The release version cannot be represented as a Store package version."
}
$packageVersion = "$packageMajor.$packageMinor.$StoreBuild.0"

if (-not $ExecutablePath) {
    $ExecutablePath = Join-Path $PSScriptRoot "dist\Skrivi.exe"
}
$ExecutablePath = [IO.Path]::GetFullPath($ExecutablePath)
if (-not (Test-Path -LiteralPath $ExecutablePath -PathType Leaf)) {
    throw "Build dist\Skrivi.exe before creating the Store package."
}

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $PSScriptRoot "dist\store"
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$buildRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "build\msix"))
$packageRoot = Join-Path $buildRoot "package"
if (-not $packageRoot.StartsWith($buildRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to prepare a package outside build\msix."
}

if (Test-Path -LiteralPath $packageRoot) {
    Remove-Item -LiteralPath $packageRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageRoot "Assets") -Force |
    Out-Null
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

Copy-Item -LiteralPath $ExecutablePath -Destination (Join-Path $packageRoot "Skrivi.exe")
Copy-Item -Path "store\assets\*.png" -Destination (Join-Path $packageRoot "Assets")
Copy-Item -LiteralPath "LICENSE" -Destination $packageRoot
Copy-Item -LiteralPath "THIRD_PARTY_NOTICES.md" -Destination $packageRoot

$manifest = Get-Content "store\AppxManifest.xml" -Raw
$manifest = $manifest.Replace("__PACKAGE_VERSION__", $packageVersion)
$manifestPath = Join-Path $packageRoot "AppxManifest.xml"
Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding utf8NoBOM

$makeAppx = Get-Command makeappx.exe -ErrorAction SilentlyContinue
if ($makeAppx) {
    $makeAppxPath = $makeAppx.Source
} else {
    $kitsRoot = Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\bin"
    $makeAppxPath = Get-ChildItem -Path "$kitsRoot\*\x64\makeappx.exe" -File |
        Sort-Object FullName -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}
if (-not $makeAppxPath) {
    throw "MakeAppx.exe was not found. Install the Windows SDK and try again."
}

$outputPath = Join-Path $OutputDirectory "Skrivi-$Version-windows-x64.msix"
& $makeAppxPath pack /d $packageRoot /p $outputPath /o
if ($LASTEXITCODE -ne 0) {
    throw "Microsoft Store package creation failed."
}

Write-Host "Microsoft Store package created:" -ForegroundColor Green
Write-Host $outputPath
Write-Host "Package version: $packageVersion"
