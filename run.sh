#!/bin/bash
# Android Crash Monitor - Quick Start Script

set -e

echo "🚀 Android Crash Monitor"

# Try different ways to run the monitor
if command -v acm >/dev/null 2>&1; then
    acm start "$@"
elif [ -f "$HOME/Library/Python/3.9/bin/acm" ]; then
    export PATH="$HOME/Library/Python/3.9/bin:$PATH"
    acm start "$@"
elif [ -f "./src/android_crash_monitor/cli.py" ]; then
    python3 -m android_crash_monitor.cli start "$@"
else
    echo "❌ Installation not found"
    echo ""
    echo "Run from project directory or install with: pip3 install -e ."
    exit 1
fi
