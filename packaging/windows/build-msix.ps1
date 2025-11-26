# Build MSIX package for Windows Store
# Run from the project root directory in PowerShell
#
# Prerequisites:
#   - Python 3.10+ installed
#   - Windows 10 SDK (for makeappx.exe and signtool.exe)
#   - Partner Center account for Windows Store
#
# Usage:
#   .\packaging\windows\build-msix.ps1
#
# For signing (required for Store submission):
#   $env:PUBLISHER_ID = "CN=YOUR-PUBLISHER-ID-FROM-PARTNER-CENTER"
#   $env:PFX_PATH = "path\to\your\certificate.pfx"
#   $env:PFX_PASSWORD = "your-certificate-password"

param(
    [string]$Version = "1.0.0.0",
    [string]$OutputDir = "build\windows"
)

$ErrorActionPreference = "Stop"

$AppName = "XtoMarkdown"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Write-Host "Building MSIX for $AppName v$Version..." -ForegroundColor Cyan

# Clean and create build directory
$BuildDir = Join-Path $ProjectRoot $OutputDir
if (Test-Path $BuildDir) {
    Remove-Item -Recurse -Force $BuildDir
}
New-Item -ItemType Directory -Path $BuildDir | Out-Null
Set-Location $BuildDir

# Step 1: Create virtual environment and install dependencies
Write-Host "`nStep 1: Setting up Python environment..." -ForegroundColor Yellow
python -m venv venv
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip wheel
python -m pip install "$ProjectRoot"
python -m pip install pyinstaller

# Step 2: Build with PyInstaller
Write-Host "`nStep 2: Building with PyInstaller..." -ForegroundColor Yellow
$IconPath = Join-Path $ProjectRoot "src\xtomarkdown\gui\resources\icons\app-icon.ico"
$ResourcesPath = Join-Path $ProjectRoot "src\xtomarkdown\gui\resources"

pyinstaller --onedir --windowed `
    --name $AppName `
    --icon $IconPath `
    --add-data "$ResourcesPath;xtomarkdown\gui\resources" `
    "$ProjectRoot\src\xtomarkdown\app.py"

# Step 3: Prepare MSIX directory structure
Write-Host "`nStep 3: Preparing MSIX structure..." -ForegroundColor Yellow
$MsixDir = Join-Path $BuildDir "msix"
New-Item -ItemType Directory -Path $MsixDir | Out-Null

# Copy PyInstaller output
Copy-Item -Recurse "dist\$AppName\*" $MsixDir

# Copy Assets
$AssetsSource = Join-Path $ScriptDir "Assets"
$AssetsDest = Join-Path $MsixDir "Assets"
Copy-Item -Recurse $AssetsSource $AssetsDest

# Copy and update AppxManifest.xml
$ManifestSource = Join-Path $ScriptDir "AppxManifest.xml"
$ManifestDest = Join-Path $MsixDir "AppxManifest.xml"
$ManifestContent = Get-Content $ManifestSource -Raw

# Update version
$ManifestContent = $ManifestContent -replace 'Version="1\.0\.0\.0"', "Version=`"$Version`""

# Update Publisher ID if provided
if ($env:PUBLISHER_ID) {
    $ManifestContent = $ManifestContent -replace 'Publisher="CN=PUBLISHER_ID"', "Publisher=`"$env:PUBLISHER_ID`""
    Write-Host "  Using Publisher ID: $env:PUBLISHER_ID" -ForegroundColor Gray
} else {
    Write-Host "  WARNING: PUBLISHER_ID not set. Using placeholder." -ForegroundColor Red
    Write-Host "  Set `$env:PUBLISHER_ID before building for Store submission." -ForegroundColor Red
}

$ManifestContent | Set-Content $ManifestDest -Encoding UTF8

# Step 4: Create MSIX package
Write-Host "`nStep 4: Creating MSIX package..." -ForegroundColor Yellow

# Find Windows SDK tools
$SdkPath = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin\10.*\x64" -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    Select-Object -First 1

if (-not $SdkPath) {
    Write-Host "ERROR: Windows 10 SDK not found. Please install it from Visual Studio Installer." -ForegroundColor Red
    exit 1
}

$MakeAppx = Join-Path $SdkPath.FullName "makeappx.exe"
$SignTool = Join-Path $SdkPath.FullName "signtool.exe"

$MsixOutput = Join-Path $BuildDir "$AppName-$Version.msix"

& $MakeAppx pack /d $MsixDir /p $MsixOutput /o

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: makeappx failed" -ForegroundColor Red
    exit 1
}

Write-Host "  Created: $MsixOutput" -ForegroundColor Green

# Step 5: Sign the package (if certificate is available)
if ($env:PFX_PATH -and (Test-Path $env:PFX_PATH)) {
    Write-Host "`nStep 5: Signing MSIX package..." -ForegroundColor Yellow

    $SignArgs = @(
        "sign",
        "/fd", "SHA256",
        "/f", $env:PFX_PATH
    )

    if ($env:PFX_PASSWORD) {
        $SignArgs += "/p"
        $SignArgs += $env:PFX_PASSWORD
    }

    $SignArgs += $MsixOutput

    & $SignTool @SignArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Package signed successfully" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Signing failed" -ForegroundColor Red
    }
} else {
    Write-Host "`nStep 5: Skipping signing (no PFX_PATH set)" -ForegroundColor Yellow
}

# Deactivate venv
deactivate

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nMSIX package: $MsixOutput"
Write-Host "`nTo submit to Windows Store:"
Write-Host "  1. Go to Partner Center: https://partner.microsoft.com/dashboard"
Write-Host "  2. Create a new app submission"
Write-Host "  3. Upload the .msix file"
Write-Host "`nTo install locally (for testing):"
Write-Host "  Add-AppPackage -Path `"$MsixOutput`""
