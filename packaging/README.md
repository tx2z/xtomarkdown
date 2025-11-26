# XtoMarkdown Packaging

Build instructions for creating distributable packages on all platforms.

## Linux

### Flatpak (Recommended for distribution)

Prerequisites:
```bash
# Install flatpak-builder
sudo apt install flatpak-builder  # Debian/Ubuntu
sudo dnf install flatpak-builder  # Fedora

# Install required runtime
flatpak install flathub org.kde.Platform//6.8 org.kde.Sdk//6.8
```

Build:
```bash
cd /path/to/xtomarkdown
./packaging/linux/build-flatpak.sh
```

Output: `build/flatpak/com.github.tx2z.XtoMarkdown-1.0.0.flatpak`

Install locally:
```bash
flatpak install build/flatpak/com.github.tx2z.XtoMarkdown-1.0.0.flatpak
```

### AppImage

Prerequisites:
```bash
# Install dependencies
sudo apt install python3-venv wget  # Debian/Ubuntu
```

Build:
```bash
cd /path/to/xtomarkdown
./packaging/linux/build-appimage.sh
```

Output: `build/appimage/XtoMarkdown-1.0.0-x86_64.AppImage`

Run:
```bash
chmod +x build/appimage/XtoMarkdown-1.0.0-x86_64.AppImage
./build/appimage/XtoMarkdown-1.0.0-x86_64.AppImage
```

## macOS (App Store)

### Prerequisites

1. **Xcode** installed with command line tools:
   ```bash
   xcode-select --install
   ```

2. **Apple Developer Account** ($99/year) with:
   - "3rd Party Mac Developer Application" certificate (for signing)
   - "3rd Party Mac Developer Installer" certificate (for .pkg)
   - App ID registered: `com.xtomarkdown.XtoMarkdown`

3. **Export certificates** and set environment variables:
   ```bash
   export APP_SIGN_ID="3rd Party Mac Developer Application: Your Name (XXXXXXXXXX)"
   export INSTALLER_ID="3rd Party Mac Developer Installer: Your Name (XXXXXXXXXX)"
   export TEAM_ID="XXXXXXXXXX"
   ```

### Build

```bash
cd /path/to/xtomarkdown
./packaging/macos/build-macos.sh
```

Output:
- `build/macos/dist/XtoMarkdown.app` - The signed app bundle
- `build/macos/XtoMarkdown-1.0.0.pkg` - Installer for App Store

### App Store Submission

1. **Create App in App Store Connect**:
   - Go to https://appstoreconnect.apple.com
   - Create new app with bundle ID `com.xtomarkdown.XtoMarkdown`
   - Set price to €1.00 (or your preferred price)

2. **Upload using Transporter** (recommended):
   - Download Transporter from Mac App Store
   - Open and sign in with your Apple ID
   - Drag the `.pkg` file to upload

3. **Or upload via command line**:
   ```bash
   xcrun altool --upload-app \
       -f build/macos/XtoMarkdown-1.0.0.pkg \
       -t macos \
       -u your@apple.id \
       -p @keychain:AC_PASSWORD
   ```

4. **Submit for Review** in App Store Connect

### Notes for App Store

- The app uses App Sandbox (required for Mac App Store)
- File access is limited to user-selected files (via Open/Save dialogs and drag-drop)
- Ensure all dependencies are bundled (PyInstaller handles this)
- Test thoroughly with sandbox enabled before submission

## Windows (Microsoft Store)

### Prerequisites

1. **Windows 10 SDK** (includes `makeappx.exe` and `signtool.exe`):
   - Install via Visual Studio Installer → Individual Components → "Windows 10 SDK"
   - Or download from https://developer.microsoft.com/windows/downloads/windows-sdk/

2. **Python 3.10+** installed and in PATH

3. **Partner Center Account** (free for individuals, one-time $19 registration):
   - Register at https://partner.microsoft.com/dashboard
   - Get your Publisher ID from Partner Center → Account Settings → Organization profile

### Build

```powershell
# From project root
.\packaging\windows\build-msix.bat
```

Or with PowerShell directly:
```powershell
.\packaging\windows\build-msix.ps1
```

Output: `build\windows\XtoMarkdown-1.0.0.0.msix`

### Signing for Store Submission

Before submitting to the Store, you need to sign the package:

```powershell
# Set your Publisher ID (from Partner Center)
$env:PUBLISHER_ID = "CN=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

# If you have a code signing certificate (.pfx):
$env:PFX_PATH = "path\to\certificate.pfx"
$env:PFX_PASSWORD = "your-password"

# Build and sign
.\packaging\windows\build-msix.ps1
```

### Microsoft Store Submission

1. **Create App in Partner Center**:
   - Go to https://partner.microsoft.com/dashboard
   - Apps and Games → New product → App
   - Reserve the name "XtoMarkdown"
   - Set price to €1.00 (or your preferred price)

2. **Update AppxManifest.xml**:
   - Replace `CN=PUBLISHER_ID` with your actual Publisher ID from Partner Center
   - The build script does this automatically if `$env:PUBLISHER_ID` is set

3. **Upload Package**:
   - In Partner Center, go to your app → Packages
   - Upload the `.msix` file

4. **Submit for Certification**:
   - Fill in Store listing (description, screenshots, etc.)
   - Submit for review (typically 1-3 business days)

### Testing Locally

```powershell
# Install the MSIX (must be signed or enable Developer Mode)
Add-AppPackage -Path "build\windows\XtoMarkdown-1.0.0.0.msix"

# Enable Developer Mode for unsigned packages:
# Settings → Update & Security → For developers → Developer mode
```

### Simple EXE (without Store)

For direct distribution (not through Store):

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed `
    --name XtoMarkdown `
    --icon src\xtomarkdown\gui\resources\icons\app-icon.ico `
    --add-data "src\xtomarkdown\gui\resources;xtomarkdown\gui\resources" `
    src\xtomarkdown\app.py
```

Output: `dist\XtoMarkdown.exe`

## Icon Files

The following icon formats are provided:

| Location | Platform | Description |
|----------|----------|-------------|
| `src/.../icons/app-icon.png` | Source/Linux | 2048x2048 master icon |
| `src/.../icons/app-icon.ico` | Windows (exe) | 16-256px multi-size |
| `packaging/macos/XtoMarkdown.iconset/` | macOS | 16-1024px @1x and @2x |
| `packaging/windows/Assets/` | Windows Store | All required tile sizes |

To regenerate macOS .icns (run on macOS):
```bash
cd packaging/macos
iconutil -c icns XtoMarkdown.iconset
```

## Updating Version Number

When releasing a new version, update:
1. `pyproject.toml` - `version = "X.Y.Z"`
2. `packaging/macos/Info.plist` - `CFBundleShortVersionString` and increment `CFBundleVersion`
3. `packaging/windows/AppxManifest.xml` - `Version` attribute (use format `X.Y.Z.0`)
4. `packaging/linux/com.github.tx2z.XtoMarkdown.metainfo.xml` - Add new `<release>` entry

## App IDs

| Platform | ID |
|----------|-----|
| Linux (Flatpak) | `com.github.tx2z.XtoMarkdown` |
| macOS (App Store) | `com.xtomarkdown.XtoMarkdown` |
| Windows (Store) | `XtoMarkdown` (with Publisher CN) |

Change these to match your actual domain/organization.

## Quick Reference

| Platform | Build Command | Output |
|----------|---------------|--------|
| Linux Flatpak | `./packaging/linux/build-flatpak.sh` | `.flatpak` |
| Linux AppImage | `./packaging/linux/build-appimage.sh` | `.AppImage` |
| macOS | `./packaging/macos/build-macos.sh` | `.app` / `.pkg` |
| Windows | `.\packaging\windows\build-msix.bat` | `.msix` |
