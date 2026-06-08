# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Android Crash Monitor macOS app bundle."""

import os
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['launch-gui.py'],
    pathex=[str(Path('src'))],
    binaries=[],
    datas=[
        ('src/android_crash_monitor', 'android_crash_monitor'),
        ('icons', 'icons'),
    ],
    hiddenimports=[
        'android_crash_monitor',
        'android_crash_monitor.gui',
        'android_crash_monitor.core',
        'android_crash_monitor.core.adb',
        'android_crash_monitor.core.config',
        'android_crash_monitor.core.monitor',
        'android_crash_monitor.core.database',
        'android_crash_monitor.core.doctor',
        'android_crash_monitor.core.user_config',
        'android_crash_monitor.core.enhanced_patterns',
        'android_crash_monitor.core.enhanced_alerts',
        'android_crash_monitor.core.enhanced_detector',
        'android_crash_monitor.analysis',
        'android_crash_monitor.analysis.crash_analyzer',
        'android_crash_monitor.analysis.pattern_detector',
        'android_crash_monitor.analysis.predictive_analytics',
        'android_crash_monitor.analysis.realtime_analyzer',
        'android_crash_monitor.analysis.root_cause_analyzer',
        'android_crash_monitor.analysis.report_generator',
        'android_crash_monitor.ui',
        'android_crash_monitor.ui.console',
        'android_crash_monitor.utils',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'rich',
        'click',
        'pydantic',
        'platformdirs',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Android Crash Monitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Android Crash Monitor',
)

app = BUNDLE(
    coll,
    name='Android Crash Monitor.app',
    icon='icons/app_icon.icns' if os.path.exists('icons/app_icon.icns') else None,
    bundle_identifier='com.devenducommun.android-crash-monitor',
    info_plist={
        'CFBundleName': 'Android Crash Monitor',
        'CFBundleDisplayName': 'Android Crash Monitor',
        'CFBundleVersion': '2.2.0',
        'CFBundleShortVersionString': '2.2.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
    },
)
