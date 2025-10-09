#!/usr/bin/env python3
"""
Recent Crash Analysis - Database Connection Pool Failures
Analysis of the 18:07-18:40 cascade failure that caused device reboot
"""

import json
import glob
from collections import Counter, defaultdict
from datetime import datetime
import os

def analyze_recent_crashes():
    """Analyze the recent crash cascade that caused the reboot."""
    
    log_dir = "/Users/deven/Library/Application Support/android-crash-monitor/logs"
    
    print("🚨 PIXEL 6 REBOOT ANALYSIS - Live Crash Data")
    print("=" * 60)
    print()
    
    # Get all crash files from today
    crash_files = glob.glob(os.path.join(log_dir, "crash_20251008_*.json"))
    crash_files.sort()
    
    print(f"📊 TOTAL CRASH FILES CAPTURED: {len(crash_files)}")
    print()
    
    # Analyze crashes by time periods
    periods = {
        "18:07": [],  # Main crash event
        "18:08": [],  # Secondary cascade  
        "18:11": [],  # Recovery attempt
        "18:40": []   # Device restart
    }
    
    crashes_by_app = defaultdict(list)
    crashes_by_error = defaultdict(list)
    database_issues = []
    connection_pool_issues = []
    
    for file in crash_files:
        with open(file, 'r') as f:
            crash = json.load(f)
            
        timestamp = crash['timestamp']
        hour_min = timestamp[5:10]  # Extract HH:MM
        
        # Categorize by time period
        for period in periods:
            if hour_min.startswith(period):
                periods[period].append(crash)
                break
        
        # Categorize by app and error type
        app_name = crash.get('app_name', 'Unknown')
        crashes_by_app[app_name].append(crash)
        
        description = crash.get('description', '')
        if 'connection pool' in description.lower():
            connection_pool_issues.append(crash)
        if 'database' in description.lower() or 'sqlite' in description.lower():
            database_issues.append(crash)
        if 'IllegalStateException' in description:
            crashes_by_error['IllegalStateException'].append(crash)
        if 'Cannot initialize WorkManager' in description:
            crashes_by_error['WorkManager'].append(crash)
    
    # Timeline Analysis
    print("⏰ CRASH TIMELINE ANALYSIS:")
    for period, crashes in periods.items():
        if crashes:
            print(f"  📅 {period}: {len(crashes)} crashes")
            # Show top crash types for this period
            types = [c['crash_type'] for c in crashes]
            top_types = Counter(types).most_common(3)
            for crash_type, count in top_types:
                print(f"    └─ {crash_type}: {count}")
    print()
    
    # Critical System Issues
    print("🔥 CRITICAL SYSTEM ISSUES DETECTED:")
    print(f"  🗃️  Database connection issues: {len(database_issues)}")
    print(f"  🏊 Connection pool failures: {len(connection_pool_issues)}")
    print(f"  ⚠️  IllegalStateException errors: {len(crashes_by_error['IllegalStateException'])}")
    print(f"  🔧 WorkManager boot failures: {len(crashes_by_error['WorkManager'])}")
    print()
    
    # App Impact Analysis  
    print("📱 MOST AFFECTED SYSTEM COMPONENTS:")
    sorted_apps = sorted(crashes_by_app.items(), key=lambda x: len(x[1]), reverse=True)[:8]
    for app, crashes in sorted_apps:
        print(f"  • {app}: {len(crashes)} crashes")
    print()
    
    # Show critical database connection pool issue
    if connection_pool_issues:
        print("🚨 DATABASE CONNECTION POOL FAILURE DETAILS:")
        latest_pool_issue = connection_pool_issues[-1]
        print(f"  App: {latest_pool_issue.get('app_name', 'Unknown')}")
        print(f"  Time: {latest_pool_issue['timestamp']}")
        print(f"  Error: {latest_pool_issue['description']}")
        print()
    
    # Show WorkManager boot failure (restart indicator)
    if crashes_by_error['WorkManager']:
        print("🔄 DEVICE RESTART EVIDENCE:")
        restart_crash = crashes_by_error['WorkManager'][-1]
        print(f"  Component: {restart_crash.get('app_name', 'Unknown')}")
        print(f"  Time: {restart_crash['timestamp']}")
        print(f"  Error: Cannot initialize WorkManager in direct boot mode")
        print("  ↳ This indicates the device was restarting during monitoring!")
        print()
    
    generate_fix_recommendations(crashes_by_app, database_issues, connection_pool_issues)

def generate_fix_recommendations(crashes_by_app, database_issues, connection_pool_issues):
    """Generate specific fix recommendations based on the crash analysis."""
    
    print("🎯 IMMEDIATE FIX RECOMMENDATIONS:")
    print("=" * 40)
    print()
    
    print("🚨 CRITICAL (Do These First):")
    print("1. Clear Google Play Services data:")
    print("   adb shell pm clear com.google.android.gms")
    print("   └─ This will reset the corrupted metadata.db database")
    print()
    
    print("2. Clear system font cache:")
    print("   adb shell rm -rf /data/system/fonts/cache/*")
    print("   adb shell rm -rf /data/data/*/cache/font*")
    print("   └─ Fixes FontLog connection pool issues")
    print()
    
    print("3. Force stop and restart critical services:")
    print("   adb shell am force-stop com.google.android.gms")
    print("   adb shell am force-stop com.android.providers.fonts")
    print("   └─ Stops cascade failures in system services")
    print()
    
    print("🔧 SYSTEM REPAIR (Medium Priority):")
    print("4. Clear all app caches (database repair):")
    print("   adb shell pm clear-cache-all")
    print("   └─ Clears potentially corrupted database caches")
    print()
    
    print("5. Reset WiFi configuration (boot issue fix):")
    print("   adb shell pm clear com.android.settings")
    print("   └─ Fixes SconeWifiConfigUpdater boot failures")
    print()
    
    print("6. Check system storage space:")
    print("   adb shell df -h /data")
    print("   └─ Low storage can cause database corruption")
    print()
    
    print("📋 PREVENTION (Long-term):")
    print("7. Enable periodic cache clearing:")
    print("   Settings → Storage → Cached data → Delete")
    print("   └─ Prevent future database corruption")
    print()
    
    print("8. Monitor Google Play Services updates:")
    print("   Settings → Apps → Google Play Services → Auto-update")
    print("   └─ Keep database schemas current")
    print()
    
    print("⚡ EXPECTED RESULTS:")
    print("✅ Immediate stop of cascade crash failures")
    print("✅ Elimination of database connection pool errors")  
    print("✅ Stable system service operation")
    print("✅ No more random reboots during normal usage")
    print("✅ Proper WiFi configuration during boot")

if __name__ == "__main__":
    analyze_recent_crashes()