#!/bin/bash
# Build AppImage for XtoMarkdown
# Run from the project root directory
#
# Uses Docker with Ubuntu 22.04 for maximum compatibility across Linux distributions.
# This ensures the AppImage works on systems with GLIBC 2.35+.

set -e

APP_NAME="XtoMarkdown"
APP_ID="io.github.tx2z.XtoMarkdown"
VERSION="1.0.2"
ARCH="x86_64"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build/appimage"

# Check for --no-docker flag
USE_DOCKER=true
for arg in "$@"; do
    if [ "$arg" == "--no-docker" ]; then
        USE_DOCKER=false
    fi
done

echo "Building AppImage for ${APP_NAME} v${VERSION}..."

# Run quality checks locally (before Docker build)
run_quality_checks() {
    cd "${PROJECT_ROOT}"

    echo ""
    echo "Setting up virtual environment for quality checks..."
    VENV_DIR="${PROJECT_ROOT}/build/venv-quality"
    rm -rf "${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
    source "${VENV_DIR}/bin/activate"
    pip install --quiet --upgrade pip
    pip install --quiet -e ".[dev]"

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
}

# Build AppImage inside Docker container
build_in_docker() {
    echo "Building AppImage in Docker (Ubuntu 22.04 for GLIBC compatibility)..."

    # Clean build directory
    rm -rf "${BUILD_DIR}"
    mkdir -p "${BUILD_DIR}"

    # Create Dockerfile
    cat > "${BUILD_DIR}/Dockerfile" << 'DOCKERFILE'
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    file \
    fuse \
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
DOCKERFILE

    # Create build script for inside container
    cat > "${BUILD_DIR}/docker-build.sh" << BUILDSCRIPT
#!/bin/bash
set -e

APP_NAME="XtoMarkdown"
APP_ID="${APP_ID}"
VERSION="${VERSION}"
ARCH="x86_64"

cd /build

# Create AppDir structure
mkdir -p AppDir/usr/{bin,share/{applications,icons/hicolor/512x512/apps,metainfo}}

# Create virtual environment and build with PyInstaller
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel

echo "Installing application..."
pip install /app

echo "Installing PyInstaller..."
pip install pyinstaller

# Find PySide6 location for Qt plugins
PYSIDE6_PATH=\$(python3 -c "import PySide6; print(PySide6.__path__[0])")
echo "PySide6 path: \$PYSIDE6_PATH"

# Find magika location for model data
MAGIKA_PATH=\$(python3 -c "import magika; print(magika.__path__[0])")
echo "Magika path: \$MAGIKA_PATH"

# Find pypandoc location for bundled pandoc binary
PYPANDOC_PATH=\$(python3 -c "import pypandoc; import os; print(os.path.dirname(pypandoc.__file__))")
echo "Pypandoc path: \$PYPANDOC_PATH"

# Build with PyInstaller including Qt plugins, magika models, and pandoc
echo "Building with PyInstaller..."
pyinstaller --onedir --windowed \
    --name xtomarkdown \
    --add-data "/app/src/xtomarkdown/gui/resources:xtomarkdown/gui/resources" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/platforms:PySide6/Qt/plugins/platforms" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/wayland-shell-integration:PySide6/Qt/plugins/wayland-shell-integration" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/wayland-decoration-client:PySide6/Qt/plugins/wayland-decoration-client" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/wayland-graphics-integration-client:PySide6/Qt/plugins/wayland-graphics-integration-client" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/xcbglintegrations:PySide6/Qt/plugins/xcbglintegrations" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/egldeviceintegrations:PySide6/Qt/plugins/egldeviceintegrations" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/imageformats:PySide6/Qt/plugins/imageformats" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/iconengines:PySide6/Qt/plugins/iconengines" \
    --add-data "\${PYSIDE6_PATH}/Qt/plugins/platformthemes:PySide6/Qt/plugins/platformthemes" \
    --add-data "\${MAGIKA_PATH}/models:magika/models" \
    --add-binary "\${PYPANDOC_PATH}/files/pandoc:pypandoc/files" \
    --add-binary "/usr/lib/x86_64-linux-gnu/libxkbcommon-x11.so.0:." \
    --collect-data magika \
    --collect-data pypandoc \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --hidden-import magika \
    --hidden-import pypandoc \
    /app/src/xtomarkdown/__main__.py

# Copy PyInstaller output to AppDir
cp -r dist/xtomarkdown/* AppDir/usr/bin/

# Copy desktop file, icon, and metainfo
cp /app/packaging/linux/\${APP_ID}.desktop AppDir/usr/share/applications/
cp /app/src/xtomarkdown/gui/resources/icons/app-icon.png "AppDir/usr/share/icons/hicolor/512x512/apps/\${APP_ID}.png"
cp /app/packaging/linux/\${APP_ID}.metainfo.xml AppDir/usr/share/metainfo/
# Create appdata.xml symlink for AppStream compatibility
ln -sf \${APP_ID}.metainfo.xml AppDir/usr/share/metainfo/\${APP_ID}.appdata.xml

# Create AppDir root symlinks
ln -sf usr/share/applications/\${APP_ID}.desktop AppDir/
ln -sf usr/share/icons/hicolor/512x512/apps/\${APP_ID}.png AppDir/
ln -sf usr/bin/xtomarkdown AppDir/AppRun

# Download appimagetool
echo "Downloading appimagetool..."
wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
chmod +x appimagetool-x86_64.AppImage

# Extract appimagetool (can't run AppImage inside Docker without --privileged)
./appimagetool-x86_64.AppImage --appimage-extract
mv squashfs-root appimagetool

# Build AppImage
echo "Creating AppImage..."
ARCH=x86_64 ./appimagetool/AppRun AppDir "\${APP_NAME}-\${VERSION}-\${ARCH}.AppImage"

echo ""
echo "AppImage created successfully!"
deactivate
BUILDSCRIPT

    chmod +x "${BUILD_DIR}/docker-build.sh"

    # Build Docker image
    echo "Building Docker image..."
    docker build -t xtomarkdown-appimage-builder "${BUILD_DIR}"

    # Run build in container as current user to avoid root-owned files
    echo "Running build in container..."
    docker run --rm \
        --user "$(id -u):$(id -g)" \
        -v "${PROJECT_ROOT}:/app:ro" \
        -v "${BUILD_DIR}:/build" \
        xtomarkdown-appimage-builder \
        /build/docker-build.sh

    echo ""
    echo "AppImage created: ${BUILD_DIR}/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
}

# Build AppImage locally (without Docker)
build_locally() {
    echo "Building AppImage locally..."
    echo "WARNING: Building locally may result in GLIBC compatibility issues."
    echo "         Consider using Docker (remove --no-docker flag) for better compatibility."
    echo ""

    cd "${PROJECT_ROOT}"

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

    # Find PySide6 location for Qt plugins
    PYSIDE6_PATH=$(python3 -c "import PySide6; print(PySide6.__path__[0])")
    echo "PySide6 path: $PYSIDE6_PATH"

    # Find magika location for model data
    MAGIKA_PATH=$(python3 -c "import magika; print(magika.__path__[0])")
    echo "Magika path: $MAGIKA_PATH"

    # Find pypandoc location for bundled pandoc binary
    PYPANDOC_PATH=$(python3 -c "import pypandoc; import os; print(os.path.dirname(pypandoc.__file__))")
    echo "Pypandoc path: $PYPANDOC_PATH"

    # Build with PyInstaller including Qt plugins, magika models, and pandoc
    echo "Building with PyInstaller..."
    pyinstaller --onedir --windowed \
        --name xtomarkdown \
        --add-data "${PROJECT_ROOT}/src/xtomarkdown/gui/resources:xtomarkdown/gui/resources" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/platforms:PySide6/Qt/plugins/platforms" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/wayland-shell-integration:PySide6/Qt/plugins/wayland-shell-integration" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/wayland-decoration-client:PySide6/Qt/plugins/wayland-decoration-client" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/wayland-graphics-integration-client:PySide6/Qt/plugins/wayland-graphics-integration-client" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/xcbglintegrations:PySide6/Qt/plugins/xcbglintegrations" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/egldeviceintegrations:PySide6/Qt/plugins/egldeviceintegrations" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/imageformats:PySide6/Qt/plugins/imageformats" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/iconengines:PySide6/Qt/plugins/iconengines" \
        --add-data "${PYSIDE6_PATH}/Qt/plugins/platformthemes:PySide6/Qt/plugins/platformthemes" \
        --add-data "${MAGIKA_PATH}/models:magika/models" \
        --add-binary "${PYPANDOC_PATH}/files/pandoc:pypandoc/files" \
        --add-binary "/usr/lib/x86_64-linux-gnu/libxkbcommon-x11.so.0:." \
        --collect-data magika \
        --collect-data pypandoc \
        --hidden-import PySide6.QtCore \
        --hidden-import PySide6.QtGui \
        --hidden-import PySide6.QtWidgets \
        --hidden-import magika \
        --hidden-import pypandoc \
        "${PROJECT_ROOT}/src/xtomarkdown/__main__.py"

    # Copy PyInstaller output to AppDir
    cp -r dist/xtomarkdown/* AppDir/usr/bin/

    # Copy desktop file, icon, and metainfo
    cp "${SCRIPT_DIR}/${APP_ID}.desktop" AppDir/usr/share/applications/
    cp "${PROJECT_ROOT}/src/xtomarkdown/gui/resources/icons/app-icon.png" "AppDir/usr/share/icons/hicolor/512x512/apps/${APP_ID}.png"
    cp "${SCRIPT_DIR}/${APP_ID}.metainfo.xml" AppDir/usr/share/metainfo/
    # Create appdata.xml symlink for AppStream compatibility
    ln -sf ${APP_ID}.metainfo.xml AppDir/usr/share/metainfo/${APP_ID}.appdata.xml

    # Create AppDir root symlinks
    ln -sf usr/share/applications/${APP_ID}.desktop AppDir/
    ln -sf usr/share/icons/hicolor/512x512/apps/${APP_ID}.png AppDir/
    ln -sf usr/bin/xtomarkdown AppDir/AppRun

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
}

# Main execution
run_quality_checks

if [ "$USE_DOCKER" = true ]; then
    if ! command -v docker &> /dev/null; then
        echo "ERROR: Docker is not installed. Please install Docker or use --no-docker flag."
        exit 1
    fi
    build_in_docker
else
    build_locally
fi
