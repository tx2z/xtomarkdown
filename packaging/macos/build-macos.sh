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
VERSION="1.0.0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build/macos"

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

# Step 3: Build with PyInstaller
echo "Building with PyInstaller..."
pyinstaller --windowed \
    --name "${APP_NAME}" \
    --icon "XtoMarkdown.icns" \
    --osx-bundle-identifier "${BUNDLE_ID}" \
    --add-data "${PROJECT_ROOT}/src/xtomarkdown/gui/resources:xtomarkdown/gui/resources" \
    "${PROJECT_ROOT}/src/xtomarkdown/app.py"

# Step 4: Copy custom Info.plist
echo "Configuring app bundle..."
cp "${SCRIPT_DIR}/Info.plist" "dist/${APP_NAME}.app/Contents/Info.plist"
cp "XtoMarkdown.icns" "dist/${APP_NAME}.app/Contents/Resources/"

# Step 5: Sign the app (if certificates are available)
if [ -n "${APP_SIGN_ID}" ]; then
    echo "Signing app bundle..."

    # Sign all frameworks and dylibs first
    find "dist/${APP_NAME}.app/Contents" -type f \( -name "*.dylib" -o -name "*.so" -o -name "*.framework" \) | while read -r file; do
        codesign --force --options runtime --sign "${APP_SIGN_ID}" \
            --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" "$file" 2>/dev/null || true
    done

    # Sign all executables in MacOS and Frameworks
    find "dist/${APP_NAME}.app/Contents/MacOS" -type f -perm +111 | while read -r file; do
        codesign --force --options runtime --sign "${APP_SIGN_ID}" \
            --entitlements "${SCRIPT_DIR}/entitlements-inherit.plist" "$file" 2>/dev/null || true
    done

    # Sign the main app bundle
    codesign --force --options runtime --sign "${APP_SIGN_ID}" \
        --entitlements "${SCRIPT_DIR}/entitlements.plist" \
        "dist/${APP_NAME}.app"

    echo "Verifying signature..."
    codesign --verify --deep --strict "dist/${APP_NAME}.app"
    echo "Signature verified!"
else
    echo "Skipping signing (no APP_SIGN_ID set)"
fi

# Step 6: Create .pkg for App Store (if installer certificate is available)
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
