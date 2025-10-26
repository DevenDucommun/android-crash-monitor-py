#!/bin/bash
set -e

echo "🚀 Building macOS Installer for Android Crash Monitor"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    /opt/homebrew/bin/python3 -m venv venv || python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
pip install pyinstaller dmgbuild Pillow

# Create app icon
echo -e "${YELLOW}Creating app icon...${NC}"
python create_icon.py

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.dmg

# Build the app bundle
echo -e "${YELLOW}Building macOS app bundle...${NC}"
pyinstaller build_app.spec

# Build the DMG installer
echo -e "${YELLOW}Creating DMG installer...${NC}"
dmgbuild -s dmg_settings.py "Android Crash Monitor" AndroidCrashMonitor-2.0.0.dmg

# Show results
echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""
echo "Files created:"
echo "  📱 App Bundle: dist/Android Crash Monitor.app"
echo "  💿 Installer:  AndroidCrashMonitor-2.0.0.dmg ($(du -h AndroidCrashMonitor-2.0.0.dmg | cut -f1))"
echo ""
echo "To test the installer:"
echo "  open AndroidCrashMonitor-2.0.0.dmg"
echo ""
echo "To install the app:"
echo "  1. Open the DMG"
echo "  2. Drag 'Android Crash Monitor' to the Applications folder"
echo "  3. Launch from Launchpad or Applications folder"
echo ""
echo -e "${GREEN}🎉 Ready for distribution!${NC}"