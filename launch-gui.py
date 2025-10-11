#!/usr/bin/env python3
"""
Simple GUI launcher for Android Crash Monitor
Double-click this file to start the graphical interface
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

try:
    from android_crash_monitor.gui import main
    print("Starting Android Crash Monitor GUI...")
    main()
except ImportError as e:
    print(f"Error importing GUI module: {e}")
    print("Please make sure all dependencies are installed.")
    input("Press Enter to exit...")
except Exception as e:
    print(f"Error starting GUI: {e}")
    input("Press Enter to exit...")