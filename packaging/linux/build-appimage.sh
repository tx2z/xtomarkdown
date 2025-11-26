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
cd "${PROJECT_ROOT}"

# Set up virtual environment for quality checks
echo ""
echo "Setting up virtual environment for quality checks..."
VENV_DIR="${PROJECT_ROOT}/build/venv-quality"
rm -rf "${VENV_DIR}"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev]"

# Run quality checks before building
echo ""
echo "Running quality checks..."
echo "========================="

echo "Running ruff check (linting)..."
if ! ruff check src/; then
    deactivate
    echo "ERROR: Linting failed. Please fix the issues above before building."
    exit 1
fi
echo "Linting passed."

echo ""
echo "Running ruff format --check (formatting)..."
if ! ruff format --check src/; then
    deactivate
    echo "ERROR: Formatting check failed. Run 'ruff format src/' to fix."
    exit 1
fi
echo "Formatting check passed."

echo ""
echo "Running mypy (type checking)..."
if ! mypy src/; then
    deactivate
    echo "ERROR: Type checking failed. Please fix the issues above before building."
    exit 1
fi
echo "Type checking passed."

echo ""
echo "Running pytest (tests)..."
# Allow builds with no tests (exit code 5 = no tests collected)
pytest_exit_code=0
pytest || pytest_exit_code=$?
if [ $pytest_exit_code -ne 0 ] && [ $pytest_exit_code -ne 5 ]; then
    deactivate
    echo "ERROR: Tests failed. Please fix the failing tests before building."
    exit 1
fi
if [ $pytest_exit_code -eq 5 ]; then
    echo "No tests found (skipping)."
else
    echo "Tests passed."
fi

deactivate

echo ""
echo "All quality checks passed!"
echo "========================="
echo ""

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
    "${PROJECT_ROOT}/src/xtomarkdown/__main__.py"

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
