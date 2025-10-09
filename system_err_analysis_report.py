#!/usr/bin/env python3
"""
System.err Runtime Crash Analysis Report
=========================================

This script provides detailed analysis and actionable recommendations
for the System.err runtime crashes identified in the Android crash monitoring system.
"""

import json
import glob
from collections import Counter, defaultdict
from datetime import datetime

def analyze_system_err_crashes():
    """Analyze System.err crashes and generate recommendations."""
    
    system_err_files = [
        '/Users/deven/android_logs/crash_20251006_223608_644_runtime_error_1C311FDF6000FS.json',
        '/Users/deven/android_logs/crash_20251006_223633_471_runtime_error_1C311FDF6000FS.json',
        '/Users/deven/android_logs/crash_20251006_223633_476_runtime_error_1C311FDF6000FS.json',
        '/Users/deven/android_logs/crash_20251006_223633_487_runtime_error_1C311FDF6000FS.json',
        '/Users/deven/android_logs/crash_20251006_223633_664_runtime_error_1C311FDF6000FS.json',
        '/Users/deven/android_logs/crash_20251006_223633_704_runtime_error_1C311FDF6000FS.json',
        '/Users/deven/android_logs/crash_20251006_223634_225_runtime_error_1C311FDF6000FS.json'
    ]
    
    print("📊 SYSTEM.ERR CRASH ANALYSIS REPORT")
    print("=" * 50)
    print()
    
    # Load and categorize crashes
    hls_crashes = []
    receiver_crashes = []
    
    for file in system_err_files:
        with open(file, 'r') as f:
            crash = json.load(f)
            if 'HLS manifest' in crash['description']:
                hls_crashes.append(crash)
            elif 'Receiver not registered' in crash['description']:
                receiver_crashes.append(crash)
    
    # Sort by timestamp
    hls_crashes.sort(key=lambda x: x['timestamp'])
    receiver_crashes.sort(key=lambda x: x['timestamp'])
    
    print("🔍 CRASH BREAKDOWN:")
    print(f"  • HLS Streaming Errors: {len(hls_crashes)} crashes")
    print(f"  • Receiver Registration Errors: {len(receiver_crashes)} crashes")
    print(f"  • Total System.err crashes: {len(hls_crashes) + len(receiver_crashes)}")
    print()
    
    # Timeline analysis
    print("⏰ CRASH TIMELINE:")
    all_crashes = hls_crashes + receiver_crashes
    all_crashes.sort(key=lambda x: x['timestamp'])
    
    for i, crash in enumerate(all_crashes):
        crash_type = "🎬 HLS" if 'HLS manifest' in crash['description'] else "📡 RECEIVER"
        pid = crash['related_logs'][0]['pid'] if crash['related_logs'] else 'Unknown'
        print(f"  {i+1}. {crash['timestamp']} - {crash_type} - PID {pid}")
    
    print()
    
    # Technical analysis
    print("🔧 TECHNICAL ANALYSIS:")
    print()
    
    print("1️⃣ HLS STREAMING ERRORS (Priority #1 - 6 crashes)")
    print("   Root Cause: Invalid HLS manifest format")
    print("   • Error: 'Invalid HLS manifest: does not start with #EXTM3U'")
    print("   • Location: Aloha Browser (com.aloha.browser)")
    print("   • Pattern: Cascade failure - 6 crashes in ~1 second")
    print("   • Stack: Kotlin coroutines handling video streaming")
    print()
    
    print("2️⃣ RECEIVER REGISTRATION ERROR (Priority #2 - 1 crash)")
    print("   Root Cause: Broadcast receiver lifecycle management")
    print("   • Error: 'Receiver not registered: r8.y4j@2b3b386'")
    print("   • Context: Video decoding/playback completion")
    print("   • Timing: Occurs 24 seconds before HLS cascade")
    print()
    
    generate_recommendations(hls_crashes, receiver_crashes)

def generate_recommendations(hls_crashes, receiver_crashes):
    """Generate specific, actionable recommendations."""
    
    print("🚀 PRIORITY RECOMMENDATIONS:")
    print("=" * 40)
    print()
    
    print("🎯 IMMEDIATE ACTION (High Priority)")
    print("1. HLS Streaming Fix:")
    print("   □ Update Aloha Browser to latest version")
    print("   □ Clear Aloha Browser cache and data:")
    print("     adb shell pm clear com.aloha.browser")
    print("   □ Check if HLS streaming works in other browsers")
    print("   □ Investigate network connectivity during video playback")
    print()
    
    print("2. Video Pipeline Health Check:")
    print("   □ Test video playback in different apps")
    print("   □ Check for corrupted video files/streams")
    print("   □ Verify device storage space (streaming cache)")
    print()
    
    print("🔧 TECHNICAL SOLUTIONS (Medium Priority)")
    print("3. App-Specific Fixes:")
    print("   □ Disable hardware acceleration in Aloha Browser")
    print("   □ Switch to software video decoding temporarily")
    print("   □ Update Android System WebView component")
    print("   □ Check Aloha Browser permissions for storage/network")
    print()
    
    print("4. System-Level Investigation:")
    print("   □ Monitor for memory pressure during video playback")
    print("   □ Check for concurrent media apps causing resource conflicts")
    print("   □ Verify VP9 codec functionality (ExynosC2Vp9DecComponent)")
    print()
    
    print("📋 MONITORING & PREVENTION (Ongoing)")
    print("5. Enhanced Monitoring:")
    print("   □ Add specific HLS manifest validation alerts")
    print("   □ Monitor video codec errors separately")
    print("   □ Track video playback session health metrics")
    print("   □ Set up alerts for cascade failure patterns (>3 crashes in 5s)")
    print()
    
    print("6. Preventive Measures:")
    print("   □ Implement graceful HLS manifest error handling")
    print("   □ Add receiver registration/deregistration logging")
    print("   □ Consider alternative browsers for critical video content")
    print()
    
    print("💡 DEBUGGING COMMANDS:")
    print("   # Check current Aloha Browser status")
    print("   adb shell dumpsys activity com.aloha.browser")
    print()
    print("   # Monitor video-related logs")
    print("   adb logcat | grep -E 'HLS|manifest|codec|video'")
    print()
    print("   # Check system media capabilities")
    print("   adb shell dumpsys media.player")
    print()
    
    # Risk assessment
    print("⚠️  RISK ASSESSMENT:")
    print("   • Impact: MODERATE - Video streaming functionality affected")
    print("   • Frequency: HIGH - 6/7 crashes are HLS-related")
    print("   • User Experience: Degraded video playback in Aloha Browser")
    print("   • System Stability: LOW - Contained to single app")
    print()
    
    print("🎯 SUCCESS METRICS:")
    print("   ✓ Zero HLS manifest errors in 24-hour period")
    print("   ✓ Successful video playback in Aloha Browser")
    print("   ✓ No receiver registration errors")
    print("   ✓ Stable video codec operations")

if __name__ == "__main__":
    analyze_system_err_crashes()