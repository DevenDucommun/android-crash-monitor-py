#!/bin/bash
# Android Crash Monitor - Easy Installer
# For non-technical users who just want it to work!

set -e

echo "📱 Android Crash Monitor - Easy Installer"
echo "=========================================="
echo ""
echo "This will automatically install everything needed to monitor your Android device."
echo "No technical knowledge required!"
echo ""

# Detect operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    echo "🍎 Detected: macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "🐧 Detected: Linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
    echo "🪟 Detected: Windows"
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "Please try manual installation from README.md"
    exit 1
fi

echo ""
echo "Installing required components..."
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python
install_python() {
    echo "📦 Installing Python with modern Tcl/Tk..."
    
    if [[ "$OS" == "mac" ]]; then
        if command_exists brew; then
            # Install Python with modern Tcl/Tk (fixes deprecation warning)
            brew install python-tk
            echo "✅ Installed modern Python with up-to-date Tcl/Tk (no deprecation warnings)"
        else
            echo "⚠️  Homebrew not found. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install python-tk
            echo "✅ Installed modern Python with up-to-date Tcl/Tk"
        fi
    elif [[ "$OS" == "linux" ]]; then
        if command_exists apt; then
            sudo apt update
            sudo apt install -y python3 python3-pip python3-tk
        elif command_exists dnf; then
            sudo dnf install -y python3 python3-pip python3-tkinter
        elif command_exists pacman; then
            sudo pacman -S python python-pip tk
        else
            echo "❌ Package manager not found. Please install Python 3 manually."
            exit 1
        fi
    elif [[ "$OS" == "windows" ]]; then
        echo "🪟 Windows detected. Please install Python from:"
        echo "   https://www.python.org/downloads/"
        echo "   Make sure to check 'Add Python to PATH' during installation."
        echo ""
        read -p "Press Enter after installing Python..."
    fi
}

# Function to install ADB
install_adb() {
    echo "📦 Installing ADB (Android Debug Bridge)..."
    
    if [[ "$OS" == "mac" ]]; then
        if command_exists brew; then
            brew install android-platform-tools
        else
            echo "❌ Homebrew required for ADB installation"
            exit 1
        fi
    elif [[ "$OS" == "linux" ]]; then
        if command_exists apt; then
            sudo apt install -y android-tools-adb
        elif command_exists dnf; then
            sudo dnf install -y android-tools
        elif command_exists pacman; then
            sudo pacman -S android-tools
        else
            echo "❌ Package manager not found. Please install ADB manually."
            exit 1
        fi
    elif [[ "$OS" == "windows" ]]; then
        echo "🪟 For Windows, ADB will be downloaded automatically when needed."
    fi
}

# Check and install Python
if ! command_exists python3; then
    install_python
else
    echo "✅ Python 3 is already installed"
fi

# Check and install pip
if ! command_exists pip3; then
    echo "📦 Installing pip..."
    python3 -m ensurepip --upgrade
else
    echo "✅ pip is already installed"
fi

# Install Android Crash Monitor
echo "📦 Installing Android Crash Monitor..."
if [[ -f "setup.py" ]]; then
    # Install from local source
    pip3 install -e .
else
    # Install from PyPI (when available)
    pip3 install android-crash-monitor
fi

# Check and install ADB
if ! command_exists adb; then
    install_adb
else
    echo "✅ ADB is already installed"
fi

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "🚀 How to Start:"
echo "   • Double-click 'launch-gui.py' for graphical interface"
echo "   • OR run 'acm start' in terminal for one-command setup"
echo "   • OR run 'acm gui' in terminal for graphical interface"
echo ""
echo "📖 Next Steps:"
echo "   1. Connect your Android device via USB"
echo "   2. Enable USB Debugging on your device:"
echo "      - Settings > About Phone > Tap 'Build Number' 7 times"
echo "      - Settings > Developer Options > Turn on 'USB Debugging'"
echo "   3. Launch the app and click 'Setup Device'"
echo ""
echo "📚 Need Help?"
echo "   • Read SIMPLE_USER_GUIDE.md for detailed instructions"
echo "   • Visit: https://github.com/DevenDucommun/android-crash-monitor-py"
echo ""
echo "✨ Enjoy monitoring your Android device!"