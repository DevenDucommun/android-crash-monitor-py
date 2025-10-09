#!/usr/bin/env python3
"""
Enhanced Crash Detector Integration
====================================

This module integrates the enhanced System.err patterns and alerting
system into the main crash monitoring framework.

Key features:
- Dual detection: Original patterns + Enhanced System.err patterns
- Enhanced statistics tracking
- Integrated alerting for System.err specific issues
- Console display enhancements for new crash types
"""

import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .monitor import CrashDetector, CrashEvent, LogEntry
from .enhanced_patterns import EnhancedCrashPatterns, EnhancedCrashType, PatternMatch
from .enhanced_alerts import EnhancedAlertingSystem, Alert
from ..ui.console import ConsoleUI


@dataclass
class EnhancedMonitoringStats:
    """Enhanced statistics including System.err specific metrics."""
    # Original stats
    session_id: str
    start_time: str
    end_time: Optional[str]
    uptime_seconds: float
    devices_monitored: List[str]
    reconnection_count: int
    total_logs_processed: int
    logs_per_second: float
    total_crashes: int
    crashes_by_type: Dict[str, int]
    crashes_by_app: Dict[str, int]
    memory_usage_mb: float
    cpu_usage_percent: float
    
    # Enhanced System.err specific stats
    enhanced_crashes_detected: int = 0
    hls_streaming_errors: int = 0
    video_codec_errors: int = 0
    receiver_registration_errors: int = 0
    cascade_failures_detected: int = 0
    hardware_acceleration_errors: int = 0
    media_pipeline_errors: int = 0
    manifest_validation_errors: int = 0
    
    # Alert stats
    total_alerts_sent: int = 0
    critical_alerts_sent: int = 0
    cascade_alerts_sent: int = 0
    rate_limited_alerts: int = 0
    
    # Pattern confidence stats
    high_confidence_detections: int = 0  # > 90%
    medium_confidence_detections: int = 0  # 70-90%
    low_confidence_detections: int = 0  # < 70%


class EnhancedCrashDetector(CrashDetector):
    """Enhanced crash detector with System.err specific patterns."""
    
    def __init__(self, console: ConsoleUI, output_dir: Path):
        super().__init__()
        
        self.console = console
        self.output_dir = output_dir
        
        # Enhanced components
        self.enhanced_patterns = EnhancedCrashPatterns()
        self.alerting_system = EnhancedAlertingSystem(output_dir)
        
        # Enhanced statistics
        self.enhanced_stats = {
            "enhanced_crashes_detected": 0,
            "hls_streaming_errors": 0,
            "video_codec_errors": 0,
            "receiver_registration_errors": 0,
            "cascade_failures_detected": 0,
            "hardware_acceleration_errors": 0,
            "media_pipeline_errors": 0,
            "manifest_validation_errors": 0,
            "total_alerts_sent": 0,
            "critical_alerts_sent": 0,
            "cascade_alerts_sent": 0,
            "rate_limited_alerts": 0,
            "high_confidence_detections": 0,
            "medium_confidence_detections": 0,
            "low_confidence_detections": 0
        }
        
        # Setup console alert handler
        self.alerting_system.add_alert_handler(self._console_alert_handler)
        
        # Device model cache for context
        self.device_models: Dict[str, str] = {}
    
    def detect_crashes(self, log_entry: LogEntry) -> List[CrashEvent]:
        """Enhanced crash detection with both original and System.err patterns."""
        # Get original crash detections
        original_crashes = super().detect_crashes(log_entry)
        
        # Enhanced detection for System.err specific patterns
        enhanced_matches = self._detect_enhanced_patterns(log_entry)
        
        # Process enhanced matches
        enhanced_crashes = []
        for match in enhanced_matches:
            # Create enhanced crash event
            enhanced_crash = self._create_enhanced_crash_event(log_entry, match)
            enhanced_crashes.append(enhanced_crash)
            
            # Update enhanced statistics
            self._update_enhanced_stats(match)
            
            # Process alert if needed
            self._process_enhanced_alert(match, log_entry)
        
        # Combine all crashes
        all_crashes = original_crashes + enhanced_crashes
        
        return all_crashes
    
    def _detect_enhanced_patterns(self, log_entry: LogEntry) -> List[PatternMatch]:
        """Detect enhanced System.err patterns."""
        # Convert timestamp to float for cascade detection
        try:
            # Parse MM-dd HH:MM:SS.sss format and convert to timestamp
            time_parts = log_entry.timestamp.split('.')
            time_base = time_parts[0]  # MM-dd HH:MM:SS
            milliseconds = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            # Create a rough timestamp (using current year as approximation)
            from datetime import datetime
            current_year = datetime.now().year
            timestamp_str = f"{current_year}-{time_base}.{milliseconds:03d}"
            parsed_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            timestamp = parsed_time.timestamp()
        except:
            timestamp = time.time()  # Fallback to current time
        
        return self.enhanced_patterns.detect_enhanced_crashes(
            message=log_entry.message,
            tag=log_entry.tag,
            timestamp=timestamp
        )
    
    def _create_enhanced_crash_event(self, log_entry: LogEntry, 
                                   match: PatternMatch) -> CrashEvent:
        """Create a CrashEvent from an enhanced pattern match."""
        from .monitor import CrashType
        
        # Map enhanced crash type to original crash type for compatibility
        crash_type_mapping = {
            EnhancedCrashType.HLS_STREAMING_ERROR: CrashType.RUNTIME_ERROR,
            EnhancedCrashType.VIDEO_CODEC_ERROR: CrashType.RUNTIME_ERROR,
            EnhancedCrashType.RECEIVER_REGISTRATION_ERROR: CrashType.RUNTIME_ERROR,
            EnhancedCrashType.MEDIA_PIPELINE_ERROR: CrashType.RUNTIME_ERROR,
            EnhancedCrashType.HARDWARE_ACCELERATION_ERROR: CrashType.RUNTIME_ERROR,
            EnhancedCrashType.MANIFEST_VALIDATION_ERROR: CrashType.RUNTIME_ERROR,
        }
        
        original_crash_type = crash_type_mapping.get(
            match.crash_type, CrashType.RUNTIME_ERROR
        )
        
        # Extract app information from context if available
        context = match.additional_context or {}
        app_package = context.get("likely_app")
        app_name = context.get("likely_app", log_entry.tag)
        
        # Use enhanced severity if available
        severity = match.severity_override if match.severity_override else 6
        
        # Create title and description
        title = self._generate_enhanced_crash_title(match, log_entry)
        description = self._generate_enhanced_crash_description(match, log_entry)
        
        # Get related logs with enhanced context
        related_logs = self._get_related_logs(log_entry, context_lines=15)
        
        # Extract stack trace
        stack_trace = self._extract_enhanced_stack_trace(related_logs, match)
        
        # Create session ID
        session_id = f"{int(time.time())}_{log_entry.device_serial}"
        
        return CrashEvent(
            timestamp=log_entry.timestamp,
            crash_type=original_crash_type,
            app_package=app_package,
            app_name=app_name,
            severity=severity,
            title=title,
            description=description,
            stack_trace=stack_trace,
            related_logs=related_logs,
            device_serial=log_entry.device_serial,
            device_model=self.device_models.get(log_entry.device_serial),
            session_id=session_id,
            detection_patterns=[match.pattern],
            first_seen=log_entry.timestamp
        )
    
    def _generate_enhanced_crash_title(self, match: PatternMatch, 
                                     log_entry: LogEntry) -> str:
        """Generate title for enhanced crash."""
        titles = {
            EnhancedCrashType.HLS_STREAMING_ERROR: "HLS Streaming Error",
            EnhancedCrashType.VIDEO_CODEC_ERROR: "Video Codec Error",
            EnhancedCrashType.RECEIVER_REGISTRATION_ERROR: "Broadcast Receiver Error",
            EnhancedCrashType.MEDIA_PIPELINE_ERROR: "Media Pipeline Error",
            EnhancedCrashType.HARDWARE_ACCELERATION_ERROR: "Hardware Acceleration Error",
            EnhancedCrashType.MANIFEST_VALIDATION_ERROR: "Media Manifest Error",
        }
        
        base_title = titles.get(match.crash_type, "Enhanced Runtime Error")
        
        # Add app context if available
        context = match.additional_context or {}
        if "likely_app" in context:
            app_name = context["likely_app"].split('.')[-1] if '.' in context["likely_app"] else context["likely_app"]
            return f"{base_title} ({app_name})"
        
        return f"{base_title} ({log_entry.tag})"
    
    def _generate_enhanced_crash_description(self, match: PatternMatch, 
                                           log_entry: LogEntry) -> str:
        """Generate description for enhanced crash."""
        base_description = log_entry.message[:200] + "..." if len(log_entry.message) > 200 else log_entry.message
        
        # Add enhanced context information
        context = match.additional_context or {}
        enhancements = []
        
        if "streaming_protocol" in context:
            enhancements.append(f"Protocol: {context['streaming_protocol']}")
        
        if "codec_type" in context:
            enhancements.append(f"Codec: {context['codec_type']}")
        
        if "receiver_class" in context:
            enhancements.append(f"Receiver: {context['receiver_class']}")
        
        if match.confidence:
            enhancements.append(f"Confidence: {match.confidence:.1%}")
        
        if "cascade_detected" in context:
            cascade_info = context["cascade_detected"]
            enhancements.append(
                f"CASCADE: {cascade_info.get('total_crashes', 0)} crashes in "
                f"{cascade_info.get('time_window', 0)}s"
            )
        
        if enhancements:
            return f"{base_description} | {' | '.join(enhancements)}"
        
        return base_description
    
    def _extract_enhanced_stack_trace(self, related_logs: List[LogEntry], 
                                    match: PatternMatch) -> List[str]:
        """Extract stack trace with enhanced context awareness."""
        stack_trace = []
        
        # Use original stack trace extraction
        original_trace = self._extract_stack_trace(related_logs)
        if original_trace:
            return original_trace
        
        # For System.err crashes, look for specific patterns
        if match.crash_type == EnhancedCrashType.HLS_STREAMING_ERROR:
            # Look for Kotlin coroutines stack traces
            for log in related_logs:
                if any(keyword in log.message for keyword in 
                       ["kotlinx.coroutines", "invokeSuspend", "resumeWith"]):
                    stack_trace.append(log.message)
        
        elif match.crash_type == EnhancedCrashType.VIDEO_CODEC_ERROR:
            # Look for codec-specific traces
            for log in related_logs:
                if any(keyword in log.message for keyword in 
                       ["Codec", "Buffer", "MediaFormat", "Surface"]):
                    stack_trace.append(log.message)
        
        return stack_trace or [match.pattern]  # Fallback to pattern if no trace found
    
    def _update_enhanced_stats(self, match: PatternMatch):
        """Update enhanced statistics based on pattern match."""
        self.enhanced_stats["enhanced_crashes_detected"] += 1
        
        # Update by crash type
        crash_type_stats = {
            EnhancedCrashType.HLS_STREAMING_ERROR: "hls_streaming_errors",
            EnhancedCrashType.VIDEO_CODEC_ERROR: "video_codec_errors", 
            EnhancedCrashType.RECEIVER_REGISTRATION_ERROR: "receiver_registration_errors",
            EnhancedCrashType.MEDIA_PIPELINE_ERROR: "media_pipeline_errors",
            EnhancedCrashType.HARDWARE_ACCELERATION_ERROR: "hardware_acceleration_errors",
            EnhancedCrashType.MANIFEST_VALIDATION_ERROR: "manifest_validation_errors",
        }
        
        stat_key = crash_type_stats.get(match.crash_type)
        if stat_key:
            self.enhanced_stats[stat_key] += 1
        
        # Update confidence stats
        if match.confidence >= 0.9:
            self.enhanced_stats["high_confidence_detections"] += 1
        elif match.confidence >= 0.7:
            self.enhanced_stats["medium_confidence_detections"] += 1
        else:
            self.enhanced_stats["low_confidence_detections"] += 1
        
        # Update cascade stats
        if match.additional_context and match.additional_context.get("cascade_detected"):
            self.enhanced_stats["cascade_failures_detected"] += 1
    
    def _process_enhanced_alert(self, match: PatternMatch, log_entry: LogEntry):
        """Process alerts for enhanced crashes."""
        # Extract app package from context or log
        app_package = None
        if match.additional_context:
            app_package = match.additional_context.get("likely_app")
        
        if not app_package:
            # Try to extract from log entry tag or message
            if "." in log_entry.tag and len(log_entry.tag.split(".")) >= 3:
                app_package = log_entry.tag
        
        # Process through alerting system
        self.alerting_system.process_enhanced_crash(
            pattern_match=match,
            device_serial=log_entry.device_serial,
            app_package=app_package
        )
    
    def _console_alert_handler(self, alert: Alert):
        """Handle alerts by displaying them in console."""
        # Update alert statistics
        self.enhanced_stats["total_alerts_sent"] += 1
        
        if alert.level.value == "critical":
            self.enhanced_stats["critical_alerts_sent"] += 1
        
        if "cascade" in alert.alert_type.value:
            self.enhanced_stats["cascade_alerts_sent"] += 1
        
        # Display alert in console with appropriate styling
        alert_colors = {
            "info": "blue",
            "warning": "yellow", 
            "error": "red",
            "critical": "bright_red"
        }
        
        color = alert_colors.get(alert.level.value, "white")
        
        # Create alert prefix based on type
        alert_prefixes = {
            "cascade_failure": "🚨 CASCADE",
            "hls_streaming_down": "📺 HLS",
            "video_codec_failure": "🎥 CODEC",
            "system_instability": "⚠️  SYSTEM",
            "single_crash": "💥 CRASH"
        }
        
        prefix = alert_prefixes.get(alert.alert_type.value, "🔔 ALERT")
        
        # Display the alert
        self.console.print(
            f"[{color}]{prefix}[/{color}] "
            f"[bold]{alert.title}[/bold] "
            f"(Severity: {alert.severity or 'N/A'}/10)"
        )
        
        # Show additional info for cascade failures
        if alert.alert_type.value == "cascade_failure" and alert.crash_count > 1:
            self.console.print(
                f"  └─ {alert.crash_count} crashes in {alert.time_window_minutes} min(s)"
            )
    
    def set_device_model(self, device_serial: str, model: str):
        """Set device model for context."""
        self.device_models[device_serial] = model
    
    def get_enhanced_statistics(self) -> Dict:
        """Get enhanced monitoring statistics."""
        # Get alerting system stats
        alert_stats = self.alerting_system.get_alert_statistics()
        
        # Get pattern matching stats
        pattern_stats = self.enhanced_patterns.get_pattern_stats()
        
        return {
            **self.enhanced_stats,
            "alert_system": alert_stats,
            "pattern_matching": pattern_stats
        }
    
    def get_pattern_performance_summary(self) -> Dict:
        """Get summary of pattern matching performance."""
        stats = self.get_enhanced_statistics()
        
        total_enhanced = stats["enhanced_crashes_detected"]
        if total_enhanced == 0:
            return {"message": "No enhanced crashes detected yet"}
        
        # Calculate confidence distribution
        high_conf_pct = (stats["high_confidence_detections"] / total_enhanced) * 100
        medium_conf_pct = (stats["medium_confidence_detections"] / total_enhanced) * 100
        low_conf_pct = (stats["low_confidence_detections"] / total_enhanced) * 100
        
        # Calculate alert efficiency
        alert_rate = (stats["total_alerts_sent"] / total_enhanced) * 100
        
        return {
            "total_enhanced_crashes": total_enhanced,
            "cascade_failures": stats["cascade_failures_detected"],
            "confidence_distribution": {
                "high": f"{high_conf_pct:.1f}%",
                "medium": f"{medium_conf_pct:.1f}%", 
                "low": f"{low_conf_pct:.1f}%"
            },
            "alert_efficiency": f"{alert_rate:.1f}%",
            "top_crash_types": {
                "HLS Streaming": stats["hls_streaming_errors"],
                "Video Codec": stats["video_codec_errors"],
                "Receiver Registration": stats["receiver_registration_errors"],
                "Hardware Acceleration": stats["hardware_acceleration_errors"]
            }
        }