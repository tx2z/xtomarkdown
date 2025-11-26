#!/bin/bash
# Build Flatpak for XtoMarkdown
# Run from the project root directory
#
# Prerequisites:
#   flatpak-builder installed
#   org.kde.Platform and org.kde.Sdk runtime installed:
#     flatpak install flathub org.kde.Platform//6.7 org.kde.Sdk//6.7

set -e

APP_ID="com.github.tx2z.XtoMarkdown"
VERSION="1.0.0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build/flatpak"

echo "Building Flatpak for ${APP_ID} v${VERSION}..."

# Clean and create build directory
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Build Flatpak
echo "Running flatpak-builder..."
flatpak-builder --force-clean \
    --repo=repo \
    --state-dir=.flatpak-builder \
    build-dir \
    "${SCRIPT_DIR}/${APP_ID}.yml"

# Create single-file bundle
echo "Creating bundle..."
flatpak build-bundle repo "${APP_ID}-${VERSION}.flatpak" "${APP_ID}"

echo ""
echo "Flatpak bundle created: ${BUILD_DIR}/${APP_ID}-${VERSION}.flatpak"
echo ""
echo "To install locally:"
echo "  flatpak install ${APP_ID}-${VERSION}.flatpak"
echo ""
echo "To publish to Flathub, submit a PR to:"
echo "  https://github.com/flathub/flathub"
