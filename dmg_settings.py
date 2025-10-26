# -*- coding: utf-8 -*-
"""
DMG build settings for Android Crash Monitor
"""

import os
from pathlib import Path

# Basic settings
format = 'UDBZ'  # Compressed format
size = None      # Automatic size

# Files to include
files = [
    'dist/Android Crash Monitor.app'
]

# Symlink to Applications folder
symlinks = {
    'Applications': '/Applications'
}

# Volume name
volume_name = 'Android Crash Monitor'

# DMG settings
settings = {
    'filename': 'AndroidCrashMonitor-2.0.0.dmg',
    'volume_name': volume_name,
    'format': format,
    'size': size,
    'files': files,
    'symlinks': symlinks,
}

# Window appearance
window_rect = ((200, 120), (640, 360))
default_view = 'icon-view'
show_toolbar = False
show_tab_view = False
show_path_bar = False
show_sidebar = False
sidebar_width = 180

# Icon arrangement
arrange_by = None
grid_offset = (0, 0)
grid_spacing = 100
scroll_position = (0, 0)
label_pos = 'bottom'  # or 'right'
text_size = 16
icon_size = 128

# Window background
background_picture = None  # We can add a custom background image later

# Icon positions
icon_locations = {
    'Android Crash Monitor.app': (150, 150),
    'Applications': (450, 150)
}

# License agreement (optional)
license = {
    'default-language': 'en_US',
    'licenses': {
        'en_US': 'LICENSE'  # If we have a LICENSE file
    }
}