#!/bin/bash
# Android Crash Monitor - Simple Run Script
# 
# This script makes it super easy for end users to start monitoring
# without worrying about Python paths or installation details.

set -e

echo "🚀 Android Crash Monitor - Starting..."
echo ""

# Check if acm is available in PATH
if command -v acm >/dev/null 2>&1; then
    echo "✅ ACM found in PATH"
    acm start "$@"
elif [ -f "$HOME/Library/Python/3.9/bin/acm" ]; then
    echo "✅ ACM found in Python user directory"
    export PATH="$HOME/Library/Python/3.9/bin:$PATH"
    acm start "$@"
elif [ -f "./src/android_crash_monitor/cli.py" ]; then
    echo "✅ Running from source directory"
    python3 -m android_crash_monitor.cli start "$@"
else
    echo "❌ Android Crash Monitor not found!"
    echo ""
    echo "Please install it first:"
    echo "  pip3 install -e ."
    echo ""
    echo "Or run from the project directory."
    exit 1
fi