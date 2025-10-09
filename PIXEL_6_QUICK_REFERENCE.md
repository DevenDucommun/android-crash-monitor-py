# Pixel 6 Quick Reference Guide
**Device:** Google Pixel 6 (SERIAL_REDACTED) - WiFi Only
**Status:** Stable after 5G hardware failure resolution

## 🚨 If Reboots Return

### Immediate Diagnosis Commands
```bash
# 1. Start monitoring to capture live crashes
cd /Users/deven/Projects/android-crash-monitor-py  
acm start

# 2. Let it run until crash/reboot occurs, then press Ctrl+C

# 3. Analyze the crash pattern
python3 analyze_recent_crash.py
```

### Red Flags to Look For
- **Database connection pool failures** (FontLog, SQLite)
- **WorkManager initialization errors** (boot restart evidence)
- **Cascade failures** (100+ crashes in short period)
- **Google Play Services crashes** (metadata.db corruption)

## 🛠️ Emergency Fixes (Copy/Paste Ready)

### Critical Database Repair
```bash
adb shell pm clear com.google.android.gms
adb shell am force-stop com.google.android.gms
adb shell am force-stop com.android.providers.fonts
adb shell 'rm -rf /data/system/fonts/cache/*'
adb shell pm trim-caches 1000M
```

### Cellular Service Reset (5G Hardware Missing)
```bash
adb shell settings put global airplane_mode_radios "cell"
adb shell settings put global preferred_network_mode 9
adb shell am force-stop com.android.phone
adb shell pm disable-user com.android.stk
```

### WiFi Recovery
```bash
adb shell pm clear com.android.settings
adb shell svc wifi enable
```

## 📊 Normal vs Problematic Crash Patterns

### ✅ Normal (WiFi-Only Device)
- Permission errors trying to access missing cellular hardware
- Individual app runtime exceptions
- Network timeouts for cellular services
- **NO REBOOTS** - device stays stable

### 🚨 Problematic (Database Corruption)
- Multiple database connection failures
- Font system cascade errors
- Google Play Services metadata.db errors
- WorkManager boot initialization failures
- **DEVICE REBOOTS**

## 🔍 Quick Health Check
```bash
# Check if device is online
adb devices

# Look at recent crash count
ls "/Users/deven/Library/Application Support/android-crash-monitor/logs" | wc -l

# Check cellular services are disabled
adb shell settings get global airplane_mode_radios
```

## 📱 Known Device Configuration
- **Network:** WiFi-only (cellular hardware removed)
- **Services:** Cellular services disabled in software
- **Databases:** Google Play Services cleared and stable
- **Font System:** Cache cleared and functional  
- **Storage:** 146GB available (plenty of space)

## 📞 When to Investigate Further
- Device reboots return
- New cascade failure patterns (50+ crashes/minute)
- Database connection pool errors reappear
- System becomes unresponsive

---
**Last Updated:** October 9, 2025  
**Full Report:** PIXEL_6_REBOOT_DIAGNOSIS_COMPLETE.md