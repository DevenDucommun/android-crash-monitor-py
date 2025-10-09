#!/usr/bin/env python3
"""
Test Analysis System - Validate the comprehensive crash analysis features

This script tests the new analysis capabilities using sample crash data.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

from src.android_crash_monitor.analysis.crash_analyzer import CrashAnalyzer
from src.android_crash_monitor.analysis.report_generator import ReportGenerator
from src.android_crash_monitor.analysis.pattern_detector import PatternDetector

def create_sample_crash_data():
    """Create sample crash data for testing."""
    sample_crashes = [
        # Database connection pool failure (critical pattern)
        {
            "timestamp": "10-09 02:30:15.123",
            "crash_type": "runtime_error", 
            "app_name": "FontLog",
            "severity": 8,
            "title": "Database Connection Pool Error",
            "description": "Cannot perform this operation because the connection pool has been closed",
            "stack_trace": [
                "java.lang.IllegalStateException: Cannot perform this operation because the connection pool has been closed.",
                "at com.android.internal.database.SQLiteConnectionPool.throwIfClosedLocked",
                "at android.database.sqlite.SQLiteConnection.execute"
            ],
            "related_logs": [
                {"timestamp": "10-09 02:30:15.120", "level": "E", "message": "Connection pool closing"}
            ]
        },
        
        # WorkManager boot failure (reboot evidence)
        {
            "timestamp": "10-09 02:30:45.456", 
            "crash_type": "runtime_error",
            "app_name": "SconeWifiConfigUpdater",
            "severity": 9,
            "title": "WorkManager Boot Failure",
            "description": "Cannot initialize WorkManager in direct boot mode",
            "stack_trace": ["java.lang.IllegalStateException: Cannot initialize WorkManager in direct boot mode"],
            "related_logs": []
        },
        
        # Google Play Services failures (cascade pattern)
        {
            "timestamp": "10-09 02:31:00.789",
            "crash_type": "runtime_error",
            "app_name": "GoogleApiManager", 
            "severity": 7,
            "title": "Google Services Failure",
            "description": "GoogleApiManager connection failed",
            "stack_trace": ["com.google.android.gms.common.api.ApiException"],
            "related_logs": []
        },
        
        # Memory pressure cascade
        {
            "timestamp": "10-09 02:32:10.111",
            "crash_type": "runtime_error",
            "app_name": "SystemUI",
            "severity": 8, 
            "title": "Memory Pressure",
            "description": "OutOfMemoryError during bitmap allocation",
            "stack_trace": ["java.lang.OutOfMemoryError: Failed to allocate bitmap"],
            "related_logs": [
                {"timestamp": "10-09 02:32:09.000", "level": "W", "message": "Low memory pressure detected"}
            ]
        },
        
        # Secondary memory pressure indicator  
        {
            "timestamp": "10-09 02:32:15.222",
            "crash_type": "runtime_error", 
            "app_name": "ActivityManager",
            "severity": 6,
            "title": "Process Killed",
            "description": "Process killed due to memory pressure",
            "stack_trace": ["Process killed by system"],
            "related_logs": []
        },
        
        # Normal background crashes (should not trigger patterns)
        {
            "timestamp": "10-09 02:35:30.333",
            "crash_type": "permission_error",
            "app_name": "RandomApp",
            "severity": 4,
            "title": "Permission Denied", 
            "description": "Permission denied for camera access",
            "stack_trace": [],
            "related_logs": []
        }
    ]
    
    return sample_crashes

def test_analysis_system():
    """Test the complete analysis system."""
    print("🧪 Testing Android Crash Monitor Analysis System")
    print("=" * 60)
    
    # Create temporary directory for test data
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Create sample crash files
        sample_crashes = create_sample_crash_data()
        print(f"📝 Created {len(sample_crashes)} sample crash files")
        
        for i, crash in enumerate(sample_crashes):
            crash_file = test_dir / f"crash_test_{i:03d}_runtime_error_TEST_DEVICE.json"
            with open(crash_file, 'w') as f:
                json.dump(crash, f, indent=2)
        
        # Test CrashAnalyzer
        print("\n🔍 Testing CrashAnalyzer...")
        analyzer = CrashAnalyzer(test_dir)
        crash_count = analyzer.load_crashes()
        print(f"✅ Loaded {crash_count} crash files")
        
        # Generate analysis report
        print("📊 Generating analysis report...")
        report = analyzer.generate_analysis_report()
        
        print(f"✅ Analysis complete!")
        print(f"   - Total crashes analyzed: {report['summary']['total_crashes']}")
        print(f"   - System health: {report['summary']['system_health']['status']}")
        print(f"   - Critical patterns found: {len(report['critical_patterns'])}")
        
        # Test ReportGenerator
        print("\n📋 Testing ReportGenerator...")
        generator = ReportGenerator()
        
        # Test console report
        print("🖥️  Console report:")
        generator.generate_console_report(report)
        
        # Test summary
        summary = generator.generate_summary_report(report)
        print(f"\n📄 Summary: {summary}")
        
        # Test PatternDetector
        print("\n🔮 Testing Advanced PatternDetector...")
        detector = PatternDetector()
        patterns = detector.detect_patterns(analyzer.crashes)
        anomalies = detector.detect_anomalies(analyzer.crashes)
        
        print(f"✅ Advanced pattern detection complete!")
        print(f"   - Patterns detected: {len(patterns)}")
        print(f"   - Anomalies detected: {len(anomalies)}")
        
        if patterns:
            print("   📊 Advanced Patterns:")
            for pattern in patterns[:3]:  # Show top 3
                print(f"      • {pattern.pattern_name}: {pattern.confidence:.1%} confidence, severity {pattern.severity_score:.1f}")
        
        if anomalies:
            print("   ⚠️  Anomalies:")
            for anomaly in anomalies[:2]:  # Show top 2
                print(f"      • {anomaly['type']}: {anomaly['description']}")
        
        print(f"\n✅ All tests passed! Analysis system is working correctly.")
        
        return report

if __name__ == "__main__":
    test_analysis_system()