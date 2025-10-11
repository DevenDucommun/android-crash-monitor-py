#!/usr/bin/env python3
"""
Simple GUI launcher for Android Crash Monitor
Double-click this file to start the graphical interface
"""

import sys
import os
from pathlib import Path

# On macOS, prefer Homebrew Python over system Python to avoid tkinter deprecation
if sys.platform == 'darwin' and 'Xcode' in sys.executable:
    # Try to find Homebrew Python (both Intel and Apple Silicon paths)
    homebrew_paths = [
        '/opt/homebrew/bin/python3',  # Apple Silicon
        '/usr/local/bin/python3'      # Intel
    ]
    
    for homebrew_python in homebrew_paths:
        if os.path.exists(homebrew_python):
            print(f"Found modern Python: {homebrew_python}")
            print("Using Homebrew Python to avoid tkinter deprecation warnings...")
            # Re-execute with Homebrew Python
            os.execv(homebrew_python, [homebrew_python] + sys.argv)
            break
    else:
        print("⚠️  Warning: Using system Python with deprecated Tcl/Tk")
        print("   For best experience, install: brew install python-tk")
        print("   This will eliminate deprecation warnings.\n")

# Suppress macOS tkinter deprecation warning as fallback
os.environ['TK_SILENCE_DEPRECATION'] = '1'

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