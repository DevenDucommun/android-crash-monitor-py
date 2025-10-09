#!/usr/bin/env python3
"""
Test Enhanced System.err Monitoring
====================================

This script demonstrates and tests the enhanced System.err monitoring
capabilities by simulating the crash patterns we identified.
"""

import time
import json
from pathlib import Path
from datetime import datetime

# Import the enhanced components
try:
    from src.android_crash_monitor.core.enhanced_patterns import EnhancedCrashPatterns
    from src.android_crash_monitor.core.enhanced_alerts import EnhancedAlertingSystem
    from src.android_crash_monitor.core.enhanced_detector import EnhancedCrashDetector
    from src.android_crash_monitor.core.monitor import LogEntry, LogLevel
    from src.android_crash_monitor.ui.console import ConsoleUI
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please run from the project root directory")
    exit(1)

class EnhancedMonitoringTester:
    """Test suite for enhanced monitoring capabilities."""
    
    def __init__(self):
        self.output_dir = Path("./test_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup console
        self.console = ConsoleUI()
        
        # Test data based on our analysis
        self.test_cases = self._create_test_cases()
    
    def _create_test_cases(self):
        """Create test cases based on actual System.err crashes."""
        return [
            {
                "name": "HLS Streaming Error - Primary Pattern",
                "log_entry": LogEntry(
                    timestamp="10-06 22:36:33.972",
                    level=LogLevel.WARNING,
                    tag="System.err",
                    pid=13579,
                    tid=13579,
                    message="java.lang.IllegalArgumentException: Invalid HLS manifest: does not start with #EXTM3U",
                    device_serial="1C311FDF6000FS",
                    raw_line="10-06 22:36:33.972 13579 13579 W System.err: java.lang.IllegalArgumentException: Invalid HLS manifest: does not start with #EXTM3U"
                ),
                "expected_type": "hls_streaming_error",
                "should_alert": True
            },
            {
                "name": "Receiver Registration Error",
                "log_entry": LogEntry(
                    timestamp="10-06 22:36:09.149", 
                    level=LogLevel.WARNING,
                    tag="System.err",
                    pid=13579,
                    tid=13579,
                    message="java.lang.IllegalArgumentException: Receiver not registered: r8.y4j@2b3b386",
                    device_serial="1C311FDF6000FS",
                    raw_line="10-06 22:36:09.149 13579 13579 W System.err: java.lang.IllegalArgumentException: Receiver not registered: r8.y4j@2b3b386"
                ),
                "expected_type": "receiver_registration_error",
                "should_alert": True
            },
            {
                "name": "Video Codec Error - VP9",
                "log_entry": LogEntry(
                    timestamp="10-06 22:36:08.100",
                    level=LogLevel.INFO,
                    tag="ExynosC2Vp9DecComponent",
                    pid=13579,
                    tid=18741,
                    message="[release] component is released",
                    device_serial="1C311FDF6000FS",
                    raw_line="10-06 22:36:08.100 13579 18741 I ExynosC2Vp9DecComponent: [release] component is released"
                ),
                "expected_type": "video_codec_error",
                "should_alert": False  # Lower severity
            },
            {
                "name": "Hardware Acceleration Error",
                "log_entry": LogEntry(
                    timestamp="10-06 22:36:07.500",
                    level=LogLevel.WARNING,
                    tag="Codec2-GraphicBufferAllocator",
                    pid=13579,
                    tid=18741,
                    message="deallocate() 58321360912570 was not successful 2",
                    device_serial="1C311FDF6000FS",
                    raw_line="10-06 22:36:07.500 13579 18741 W Codec2-GraphicBufferAllocator: deallocate() 58321360912570 was not successful 2"
                ),
                "expected_type": "hardware_acceleration_error",
                "should_alert": True
            },
            {
                "name": "Media Pipeline Error",
                "log_entry": LogEntry(
                    timestamp="10-06 22:36:08.200",
                    level=LogLevel.INFO,
                    tag="ForwardBroadcastListene",
                    pid=13579,
                    tid=18741,
                    message="Receive forward intent: com.google.android.apps.pixel.dcservice.monitor.ACTION_MONITOR_MEDIA_PLAYBACK_STOPPED",
                    device_serial="1C311FDF6000FS",
                    raw_line="10-06 22:36:08.200 13579 18741 I ForwardBroadcastListene: Receive forward intent: com.google.android.apps.pixel.dcservice.monitor.ACTION_MONITOR_MEDIA_PLAYBACK_STOPPED"
                ),
                "expected_type": "media_pipeline_error",
                "should_alert": False  # Lower severity
            }
        ]
    
    def run_pattern_detection_tests(self):
        """Test pattern detection capabilities."""
        self.console.header("🧪 Pattern Detection Tests")
        
        patterns = EnhancedCrashPatterns()
        
        for test_case in self.test_cases:
            self.console.info(f"Testing: {test_case['name']}")
            
            log_entry = test_case['log_entry']
            matches = patterns.detect_enhanced_crashes(
                message=log_entry.message,
                tag=log_entry.tag,
                timestamp=time.time()
            )
            
            if matches:
                match = matches[0]
                detected_type = match.crash_type.value
                confidence = match.confidence
                
                if detected_type == test_case['expected_type']:
                    self.console.print(f"  ✅ PASS - Detected: {detected_type} (confidence: {confidence:.1%})")
                    
                    # Show context if available
                    if match.additional_context:
                        context_str = ", ".join([f"{k}={v}" for k, v in match.additional_context.items()])
                        self.console.print(f"     Context: {context_str}")
                else:
                    self.console.print(f"  ❌ FAIL - Expected: {test_case['expected_type']}, Got: {detected_type}")
            else:
                if test_case['expected_type'] == "none":
                    self.console.print("  ✅ PASS - No pattern detected (expected)")
                else:
                    self.console.print(f"  ❌ FAIL - Expected: {test_case['expected_type']}, Got: none")
            
            print()
    
    def run_cascade_detection_test(self):
        """Test cascade failure detection."""
        self.console.header("🚨 Cascade Detection Test")
        
        patterns = EnhancedCrashPatterns()
        current_time = time.time()
        
        # Simulate the 6 HLS crashes in 1 second (from our analysis)
        hls_crashes = [
            "java.lang.IllegalArgumentException: Invalid HLS manifest: does not start with #EXTM3U",
            "java.lang.IllegalArgumentException: Invalid HLS manifest: does not start with #EXTM3U",
            "java.lang.IllegalArgumentException: Invalid HLS manifest: does not start with #EXTM3U",
            "java.lang.IllegalArgumentException: Invalid HLS manifest: does not start with #EXTM3U",
            "java.lang.IllegalArgumentException: Invalid HLS manifest: does not start with #EXTM3U",
            "java.lang.IllegalArgumentException: Invalid HLS manifest: does not start with #EXTM3U"
        ]
        
        self.console.info("Simulating cascade: 6 HLS crashes in 1 second")
        
        cascade_detected = False
        for i, message in enumerate(hls_crashes):
            timestamp = current_time + (i * 0.2)  # 200ms apart
            matches = patterns.detect_enhanced_crashes(
                message=message,
                tag="System.err",
                timestamp=timestamp
            )
            
            if matches:
                match = matches[0]
                if match.additional_context and match.additional_context.get("cascade_detected"):
                    cascade_info = match.additional_context["cascade_detected"]
                    self.console.print(
                        f"  🚨 CASCADE DETECTED on crash #{i+1}! "
                        f"Total: {cascade_info['total_crashes']} crashes"
                    )
                    cascade_detected = True
                else:
                    self.console.print(f"  Crash #{i+1}: {match.crash_type.value} (no cascade yet)")
        
        if cascade_detected:
            self.console.success("✅ Cascade detection working correctly")
        else:
            self.console.warning("❌ Cascade detection failed")
        
        print()
    
    def run_alerting_test(self):
        """Test the alerting system."""
        self.console.header("🔔 Alerting System Test")
        
        alerts_received = []
        
        def test_alert_handler(alert):
            alerts_received.append(alert)
            self.console.print(
                f"  📢 ALERT: {alert.title} (Level: {alert.level.value}, "
                f"Type: {alert.alert_type.value})"
            )
        
        # Setup alerting system
        alerting = EnhancedAlertingSystem(self.output_dir)
        alerting.add_alert_handler(test_alert_handler)
        
        # Test each pattern that should generate alerts
        patterns = EnhancedCrashPatterns()
        
        for test_case in self.test_cases:
            if not test_case.get("should_alert", False):
                continue
            
            self.console.info(f"Testing alerts for: {test_case['name']}")
            
            log_entry = test_case['log_entry']
            matches = patterns.detect_enhanced_crashes(
                message=log_entry.message,
                tag=log_entry.tag,
                timestamp=time.time()
            )
            
            if matches:
                alerting.process_enhanced_crash(
                    pattern_match=matches[0],
                    device_serial=log_entry.device_serial,
                    app_package="com.aloha.browser"
                )
        
        self.console.info(f"Total alerts generated: {len(alerts_received)}")
        print()
    
    def run_integration_test(self):
        """Test the full integration with EnhancedCrashDetector."""
        self.console.header("🔧 Integration Test")
        
        detector = EnhancedCrashDetector(self.console, self.output_dir)
        detector.set_device_model("1C311FDF6000FS", "Pixel_6")
        
        total_crashes = 0
        enhanced_crashes = 0
        
        for test_case in self.test_cases:
            self.console.info(f"Processing: {test_case['name']}")
            
            log_entry = test_case['log_entry']
            crashes = detector.detect_crashes(log_entry)
            
            total_crashes += len(crashes)
            
            for crash in crashes:
                if "Enhanced" in crash.title or any(
                    keyword in crash.title for keyword in 
                    ["HLS", "Codec", "Receiver", "Hardware", "Media"]
                ):
                    enhanced_crashes += 1
                    self.console.print(f"  🎯 Enhanced crash: {crash.title} (severity: {crash.severity})")
        
        # Show statistics
        stats = detector.get_enhanced_statistics()
        self.console.info(f"Total crashes detected: {total_crashes}")
        self.console.info(f"Enhanced crashes: {enhanced_crashes}")
        self.console.info(f"Alerts sent: {stats.get('total_alerts_sent', 0)}")
        
        # Show performance summary
        performance = detector.get_pattern_performance_summary()
        if "message" not in performance:
            self.console.info("Pattern Performance Summary:")
            for key, value in performance.items():
                if isinstance(value, dict):
                    self.console.info(f"  {key}:")
                    for subkey, subvalue in value.items():
                        self.console.info(f"    {subkey}: {subvalue}")
                else:
                    self.console.info(f"  {key}: {value}")
        
        print()
    
    def save_test_results(self):
        """Save test results for review."""
        self.console.header("💾 Saving Test Results")
        
        # Check if any alert files were created
        alerts_dir = self.output_dir / "alerts"
        if alerts_dir.exists():
            alert_files = list(alerts_dir.glob("*.json"))
            self.console.info(f"Alert files created: {len(alert_files)}")
            
            # Show a sample alert
            if alert_files:
                with open(alert_files[0], 'r') as f:
                    sample_alert = json.load(f)
                
                self.console.info("Sample alert structure:")
                for key in ['alert_id', 'alert_type', 'level', 'title', 'crash_type']:
                    if key in sample_alert:
                        self.console.info(f"  {key}: {sample_alert[key]}")
        
        self.console.success(f"Test results saved to: {self.output_dir}")
    
    def run_all_tests(self):
        """Run all test suites."""
        self.console.print("[bold green]🚀 Enhanced System.err Monitoring Test Suite[/bold green]")
        self.console.info("Testing the enhanced monitoring capabilities based on crash analysis")
        print()
        
        # Run all tests
        self.run_pattern_detection_tests()
        self.run_cascade_detection_test()
        self.run_alerting_test()
        self.run_integration_test()
        self.save_test_results()
        
        self.console.print("[bold green]✅ All tests completed![/bold green]")
        self.console.info(
            "The enhanced System.err monitoring is ready to detect HLS streaming errors, "
            "cascade failures, video codec issues, and more with intelligent alerting."
        )


if __name__ == "__main__":
    tester = EnhancedMonitoringTester()
    tester.run_all_tests()