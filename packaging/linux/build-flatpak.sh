#!/bin/bash
# Build Flatpak for XtoMarkdown
# Run from the project root directory
#
# Prerequisites:
#   flatpak-builder installed
#   org.kde.Platform and org.kde.Sdk runtime installed:
#     flatpak install flathub org.kde.Platform//6.8 org.kde.Sdk//6.8

set -e

APP_ID="io.github.tx2z.XtoMarkdown"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build/flatpak"

# Read version from pyproject.toml (single source of truth)
VERSION=$(grep -E "^version\s*=" "${PROJECT_ROOT}/pyproject.toml" | sed 's/.*"\(.*\)".*/\1/')
if [ -z "${VERSION}" ]; then
    echo "ERROR: Could not read version from pyproject.toml"
    exit 1
fi

echo "Building Flatpak for ${APP_ID} v${VERSION}..."
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

# Clean and create build directory (preserve .flatpak-builder cache)
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"
rm -rf build-dir repo

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
echo "  flatpak install ${BUILD_DIR}/${APP_ID}-${VERSION}.flatpak"
echo ""
echo "To publish to Flathub, submit a PR to:"
echo "  https://github.com/flathub/flathub"
