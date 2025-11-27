#!/bin/bash
# Test AppImage similar to AppImageHub CI pipeline
# Run from the project root directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build/appimage"

# Find the AppImage
APPIMAGE=$(ls -t "${BUILD_DIR}"/*.AppImage 2>/dev/null | grep -v appimagetool | head -n 1)

if [ -z "$APPIMAGE" ] || [ ! -f "$APPIMAGE" ]; then
    echo "ERROR: No AppImage found in ${BUILD_DIR}"
    echo "Run build-appimage.sh first"
    exit 1
fi

APPIMAGE_NAME=$(basename "$APPIMAGE")
echo "Testing AppImage: $APPIMAGE_NAME"
echo "==========================================="

# Create test script for inside Docker
cat > "${BUILD_DIR}/docker-test.sh" << 'TESTSCRIPT'
#!/bin/bash
set -e

cd /test

APPIMAGE=$(ls *.AppImage 2>/dev/null | grep -v appimagetool | head -n 1)
echo "Testing: $APPIMAGE"
echo ""

# Check file type
echo "=== File Info ==="
file "$APPIMAGE"
echo ""

# Check architecture
ARCHITECTURE=$(file "$APPIMAGE" | cut -d "," -f 2 | xargs | sed -e 's|-|_|g')
echo "Architecture: $ARCHITECTURE"
echo ""

# Extract AppImage
echo "=== Extracting AppImage ==="
chmod +x "$APPIMAGE"
./"$APPIMAGE" --appimage-extract > /dev/null 2>&1
echo "Extracted to squashfs-root/"
echo ""

# Check desktop file
echo "=== Desktop File ==="
DESKTOP_FILE=$(ls squashfs-root/*.desktop 2>/dev/null | head -n 1)
if [ -n "$DESKTOP_FILE" ]; then
    echo "Found: $(basename $DESKTOP_FILE)"
    grep -E "^(Name|Icon|Exec|Categories)=" "$DESKTOP_FILE"
else
    echo "ERROR: No desktop file found!"
    exit 1
fi
echo ""

# Check icon
echo "=== Icon Check ==="
ICON_NAME=$(grep "^Icon=" "$DESKTOP_FILE" | cut -d "=" -f 2)
echo "Icon name from desktop: $ICON_NAME"

# Look for icon in various locations
ICON_FOUND=false
for size in 512x512 256x256 128x128; do
    ICON_PATH="squashfs-root/usr/share/icons/hicolor/${size}/apps/${ICON_NAME}.png"
    if [ -f "$ICON_PATH" ]; then
        ICON_SIZE=$(file "$ICON_PATH" | grep -oE "[0-9]+ x [0-9]+" | head -1)
        echo "Found icon at ${size}: ${ICON_SIZE}"
        ICON_FOUND=true
        break
    fi
done

if [ "$ICON_FOUND" = false ]; then
    # Check root directory
    if [ -f "squashfs-root/${ICON_NAME}.png" ]; then
        echo "Found icon in root directory"
        ICON_FOUND=true
    fi
fi

if [ "$ICON_FOUND" = false ]; then
    echo "WARNING: Icon not found for $ICON_NAME"
fi
echo ""

# Check metainfo/appdata
echo "=== AppStream Metadata ==="
if [ -d "squashfs-root/usr/share/metainfo" ]; then
    ls squashfs-root/usr/share/metainfo/
else
    echo "WARNING: No metainfo directory found"
fi
echo ""

# Check for required libraries
echo "=== Library Check ==="
INTERNAL_DIR="squashfs-root/usr/bin/_internal"
if [ -d "$INTERNAL_DIR" ]; then
    echo "Checking bundled libraries..."

    # Check for libxkbcommon-x11 (the one that was missing)
    if ls "$INTERNAL_DIR"/libxkbcommon-x11* > /dev/null 2>&1; then
        echo "✓ libxkbcommon-x11 found"
    else
        echo "✗ WARNING: libxkbcommon-x11 NOT found!"
    fi

    # Check for Qt plugins
    if [ -d "$INTERNAL_DIR/PySide6/Qt/plugins/platforms" ]; then
        echo "✓ Qt platform plugins found"
        ls "$INTERNAL_DIR/PySide6/Qt/plugins/platforms/" | head -5
    else
        echo "✗ WARNING: Qt platform plugins NOT found!"
    fi

    # Check for magika models
    if [ -d "$INTERNAL_DIR/magika/models" ]; then
        echo "✓ Magika models found"
    else
        echo "✗ WARNING: Magika models NOT found!"
    fi

    # Check for pandoc
    if [ -d "$INTERNAL_DIR/pypandoc/files" ]; then
        echo "✓ Pandoc binary found"
    else
        echo "✗ WARNING: Pandoc binary NOT found!"
    fi
else
    echo "WARNING: _internal directory not found"
fi
echo ""

# Try to run with QT_DEBUG_PLUGINS (headless check)
echo "=== Runtime Test (Headless) ==="
echo "Attempting to run with offscreen platform..."

# Set up virtual display
export QT_QPA_PLATFORM=offscreen
export QT_DEBUG_PLUGINS=0

# Try to run and capture any immediate errors
timeout 5 ./"$APPIMAGE" --help 2>&1 || true

echo ""
echo "=== Summary ==="
echo "AppImage extraction: OK"
echo "Desktop file: $([ -n "$DESKTOP_FILE" ] && echo 'OK' || echo 'MISSING')"
echo "Icon: $([ "$ICON_FOUND" = true ] && echo 'OK' || echo 'WARNING')"
echo ""
echo "Test completed!"

# Cleanup
rm -rf squashfs-root/
TESTSCRIPT

chmod +x "${BUILD_DIR}/docker-test.sh"

# Create Dockerfile for testing
cat > "${BUILD_DIR}/Dockerfile.test" << 'DOCKERFILE'
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    file \
    libfuse2 \
    libgl1-mesa-glx \
    libegl1-mesa \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-keysyms1 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-randr0 \
    libxcb-render-util0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /test
DOCKERFILE

echo "Building test Docker image..."
docker build -t xtomarkdown-appimage-test -f "${BUILD_DIR}/Dockerfile.test" "${BUILD_DIR}"

echo ""
echo "Running tests in Docker container..."
echo "==========================================="

docker run --rm \
    -v "${BUILD_DIR}:/test" \
    xtomarkdown-appimage-test \
    /test/docker-test.sh

echo ""
echo "==========================================="
echo "All tests completed!"
