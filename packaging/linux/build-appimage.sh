#!/bin/bash
# Build AppImage for XtoMarkdown
# Run from the project root directory

set -e

APP_NAME="XtoMarkdown"
APP_ID="com.github.tx2z.XtoMarkdown"
VERSION="1.0.0"
ARCH="x86_64"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build/appimage"

echo "Building AppImage for ${APP_NAME} v${VERSION}..."

# Clean and create build directory
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Create AppDir structure
mkdir -p AppDir/usr/{bin,share/{applications,icons/hicolor/512x512/apps,metainfo}}

# Create virtual environment and build with PyInstaller
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install "${PROJECT_ROOT}"
pip install pyinstaller

# Build with PyInstaller
echo "Building with PyInstaller..."
pyinstaller --onedir --windowed \
    --name xtomarkdown \
    --add-data "${PROJECT_ROOT}/src/xtomarkdown/gui/resources:xtomarkdown/gui/resources" \
    "${PROJECT_ROOT}/src/xtomarkdown/app.py"

# Copy PyInstaller output to AppDir
cp -r dist/xtomarkdown/* AppDir/usr/bin/

# Copy desktop file, icon, and metainfo
cp "${SCRIPT_DIR}/${APP_ID}.desktop" AppDir/usr/share/applications/
cp "${PROJECT_ROOT}/src/xtomarkdown/gui/resources/icons/app-icon.png" "AppDir/usr/share/icons/hicolor/512x512/apps/${APP_ID}.png"
cp "${SCRIPT_DIR}/${APP_ID}.metainfo.xml" AppDir/usr/share/metainfo/

# Create AppDir root symlinks
ln -sf usr/share/applications/${APP_ID}.desktop AppDir/
ln -sf usr/share/icons/hicolor/512x512/apps/${APP_ID}.png AppDir/
ln -sf usr/bin/xtomarkdown AppDir/AppRun

# Download linuxdeploy if not present
if [ ! -f linuxdeploy-x86_64.AppImage ]; then
    echo "Downloading linuxdeploy..."
    wget -q "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
    chmod +x linuxdeploy-x86_64.AppImage
fi

# Download appimagetool if not present
if [ ! -f appimagetool-x86_64.AppImage ]; then
    echo "Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# Build AppImage
echo "Creating AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir "${APP_NAME}-${VERSION}-${ARCH}.AppImage"

echo ""
echo "AppImage created: ${BUILD_DIR}/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
deactivate
