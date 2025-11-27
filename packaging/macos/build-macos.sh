#!/bin/bash
# Build macOS .app for XtoMarkdown
# Run from the project root directory on macOS
#
# Prerequisites:
#   - Xcode installed with command line tools
#   - Apple Developer account with certificates
#   - Set environment variables:
#     DEVELOPER_ID="Developer ID Application: Your Name (XXXXXXXXXX)"
#     INSTALLER_ID="3rd Party Mac Developer Installer: Your Name (XXXXXXXXXX)"
#     APP_SIGN_ID="3rd Party Mac Developer Application: Your Name (XXXXXXXXXX)"
#     TEAM_ID="XXXXXXXXXX"

set -e

APP_NAME="XtoMarkdown"
BUNDLE_ID="com.xtomarkdown.XtoMarkdown"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build/macos"

# Read version from pyproject.toml (single source of truth)
VERSION=$(grep -E "^version\s*=" "${PROJECT_ROOT}/pyproject.toml" | sed 's/.*"\(.*\)".*/\1/')
if [ -z "${VERSION}" ]; then
    echo "ERROR: Could not read version from pyproject.toml"
    exit 1
fi

echo "Building macOS app for ${APP_NAME} v${VERSION}..."

# Clean and create build directory
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Step 1: Create .icns icon
echo "Creating .icns icon..."
if [ -d "${SCRIPT_DIR}/XtoMarkdown.iconset" ]; then
    iconutil -c icns "${SCRIPT_DIR}/XtoMarkdown.iconset" -o XtoMarkdown.icns
    echo "Icon created: XtoMarkdown.icns"
else
    echo "ERROR: iconset not found at ${SCRIPT_DIR}/XtoMarkdown.iconset"
    exit 1
fi

# Step 2: Create virtual environment and install dependencies
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install "${PROJECT_ROOT}"
pip install pyinstaller

# Step 3: Find and include pandoc binary
echo "Locating pandoc binary..."
PANDOC_PATH=$(python3 -c "import pypandoc; print(pypandoc.get_pandoc_path())" 2>/dev/null || echo "")
if [ -z "${PANDOC_PATH}" ] || [ ! -f "${PANDOC_PATH}" ]; then
    # Try to find it in pypandoc's files directory
    PYPANDOC_DIR=$(python3 -c "import pypandoc; import os; print(os.path.dirname(pypandoc.__file__))")
    PANDOC_PATH="${PYPANDOC_DIR}/files/pandoc"
fi

if [ ! -f "${PANDOC_PATH}" ]; then
    echo "ERROR: Could not find pandoc binary"
    exit 1
fi
echo "Found pandoc at: ${PANDOC_PATH}"

# Step 4: Build with PyInstaller
echo "Building with PyInstaller..."
pyinstaller --windowed \
    --name "${APP_NAME}" \
    --icon "XtoMarkdown.icns" \
    --osx-bundle-identifier "${BUNDLE_ID}" \
    --add-data "${PROJECT_ROOT}/src/xtomarkdown/gui/resources:xtomarkdown/gui/resources" \
    --add-binary "${PANDOC_PATH}:." \
    --hidden-import "xtomarkdown" \
    --hidden-import "xtomarkdown.app" \
    --hidden-import "xtomarkdown.gui" \
    --hidden-import "xtomarkdown.gui.main_window" \
    --hidden-import "xtomarkdown.gui.drop_zone" \
    --hidden-import "xtomarkdown.gui.file_list" \
    --hidden-import "xtomarkdown.gui.preferences" \
    --hidden-import "xtomarkdown.config" \
    --hidden-import "xtomarkdown.config.settings" \
    --hidden-import "xtomarkdown.config.defaults" \
    --hidden-import "xtomarkdown.core" \
    --hidden-import "xtomarkdown.core.converter" \
    --hidden-import "xtomarkdown.core.file_mapping" \
    --hidden-import "xtomarkdown.core.engines" \
    --hidden-import "xtomarkdown.core.engines.base" \
    --hidden-import "xtomarkdown.core.engines.pandoc" \
    --hidden-import "xtomarkdown.core.engines.markitdown" \
    --hidden-import "xtomarkdown.core.engines.registry" \
    --hidden-import "pypandoc" \
    --collect-all "xtomarkdown" \
    "${PROJECT_ROOT}/src/xtomarkdown/launcher.py"

# Step 5: Copy custom Info.plist and update version
echo "Configuring app bundle..."
cp "${SCRIPT_DIR}/Info.plist" "dist/${APP_NAME}.app/Contents/Info.plist"
cp "XtoMarkdown.icns" "dist/${APP_NAME}.app/Contents/Resources/"

# Update version in Info.plist (read from pyproject.toml)
echo "Setting version to ${VERSION} in Info.plist..."
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${VERSION}" "dist/${APP_NAME}.app/Contents/Info.plist"
# Increment CFBundleVersion (build number) - use a simple incrementing scheme based on version
BUILD_NUMBER=$(echo "${VERSION}" | tr -d '.')
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion ${BUILD_NUMBER}" "dist/${APP_NAME}.app/Contents/Info.plist"

# Step 6: Sign the app (if certificates are available)
if [ -n "${APP_SIGN_ID}" ]; then
    echo "Signing app bundle..."

    # First, sign everything inside Python.framework (if it exists)
    PYTHON_FW="dist/${APP_NAME}.app/Contents/Frameworks/Python.framework"
    if [ -d "${PYTHON_FW}" ]; then
        echo "Signing Python framework contents..."

        # Sign all .so and .dylib files inside Python.framework
        find "${PYTHON_FW}" -type f \( -name "*.so" -o -name "*.dylib" \) | while read -r file; do
            codesign --force --options runtime --sign "${APP_SIGN_ID}" \
                --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" "$file" 2>/dev/null || true
        done

        # Sign the Python binary inside the framework
        if [ -f "${PYTHON_FW}/Versions/Current/Python" ]; then
            codesign --force --options runtime --sign "${APP_SIGN_ID}" \
                --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" \
                "${PYTHON_FW}/Versions/Current/Python"
        fi

        # Sign the Python.framework bundle itself
        codesign --force --options runtime --sign "${APP_SIGN_ID}" \
            --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" \
            "${PYTHON_FW}"
    fi

    # Sign all other .so and .dylib files
    echo "Signing libraries..."
    find "dist/${APP_NAME}.app/Contents" -type f \( -name "*.dylib" -o -name "*.so" \) ! -path "*/Python.framework/*" | while read -r file; do
        codesign --force --options runtime --sign "${APP_SIGN_ID}" \
            --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" "$file" 2>/dev/null || true
    done

    # Sign all executables in MacOS
    echo "Signing executables..."
    find "dist/${APP_NAME}.app/Contents/MacOS" -type f -perm +111 | while read -r file; do
        codesign --force --options runtime --sign "${APP_SIGN_ID}" \
            --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" "$file" 2>/dev/null || true
    done

    # Sign the bundled pandoc binary (in Frameworks directory for windowed apps)
    BUNDLED_PANDOC="dist/${APP_NAME}.app/Contents/Frameworks/pandoc"
    if [ -f "${BUNDLED_PANDOC}" ]; then
        echo "Signing bundled pandoc..."
        codesign --force --options runtime --sign "${APP_SIGN_ID}" \
            --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" "${BUNDLED_PANDOC}"
    fi

    # Sign any other framework bundles
    find "dist/${APP_NAME}.app/Contents/Frameworks" -name "*.framework" -type d ! -name "Python.framework" | while read -r fw; do
        codesign --force --options runtime --sign "${APP_SIGN_ID}" \
            --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" "$fw" 2>/dev/null || true
    done

    # Sign the main app bundle
    echo "Signing main app bundle..."
    codesign --force --options runtime --sign "${APP_SIGN_ID}" \
        --entitlements "${SCRIPT_DIR}/entitlements.plist" \
        "dist/${APP_NAME}.app"

    echo "Verifying signature..."
    codesign --verify --deep --strict "dist/${APP_NAME}.app"
    echo "Signature verified!"
else
    echo "Skipping signing (no APP_SIGN_ID set)"
fi

# Step 7: Create .pkg for App Store (if installer certificate is available)
if [ -n "${INSTALLER_ID}" ]; then
    echo "Creating installer package..."
    productbuild --component "dist/${APP_NAME}.app" /Applications \
        --sign "${INSTALLER_ID}" \
        "${APP_NAME}-${VERSION}.pkg"
    echo "Installer created: ${APP_NAME}-${VERSION}.pkg"
else
    echo "Skipping .pkg creation (no INSTALLER_ID set)"
fi

deactivate

echo ""
echo "Build complete!"
echo "App bundle: ${BUILD_DIR}/dist/${APP_NAME}.app"
[ -f "${APP_NAME}-${VERSION}.pkg" ] && echo "Installer: ${BUILD_DIR}/${APP_NAME}-${VERSION}.pkg"

echo ""
echo "=== For Mac App Store submission ==="
echo "1. Open Xcode and create an Archive, or use:"
echo "   xcrun altool --upload-app -f ${APP_NAME}-${VERSION}.pkg -t macos -u YOUR_APPLE_ID"
echo ""
echo "2. Or use Transporter.app to upload the .pkg"
