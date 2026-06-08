#!/bin/bash
set -e

VERSION="2.1.0"

echo "Building macOS Installer for Android Crash Monitor v${VERSION}"
echo "=========================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[build]"

# Create app icon
echo "Creating app icon..."
python create_icon.py

# Clean previous builds
rm -rf build/ dist/ *.dmg

# Build the app bundle
echo "Building macOS app bundle..."
pyinstaller build_app.spec

# Build the DMG installer
echo "Creating DMG installer..."
dmgbuild -s dmg_settings.py "Android Crash Monitor" "AndroidCrashMonitor-${VERSION}.dmg"

echo ""
echo "Build complete:"
echo "  App Bundle: dist/Android Crash Monitor.app"
echo "  Installer:  AndroidCrashMonitor-${VERSION}.dmg ($(du -h "AndroidCrashMonitor-${VERSION}.dmg" | cut -f1))"
echo ""
echo "To create a GitHub release with this installer:"
echo "  gh release create v${VERSION} AndroidCrashMonitor-${VERSION}.dmg --generate-notes"
