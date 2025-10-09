#!/usr/bin/env python3
"""
Enhanced Alerting System for System.err Monitoring
===================================================

This module provides specialized alerting for System.err crashes with:

- Severity-based alert levels
- Cascade failure detection and notifications
- HLS streaming error tracking
- Video codec health alerts
- Rate limiting to prevent alert spam
- Alert aggregation and summarization
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from .enhanced_patterns import EnhancedCrashType, PatternMatch


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts we can send."""
    SINGLE_CRASH = "single_crash"
    CASCADE_FAILURE = "cascade_failure"
    HLS_STREAMING_DOWN = "hls_streaming_down"
    VIDEO_CODEC_FAILURE = "video_codec_failure"
    SYSTEM_INSTABILITY = "system_instability"
    RATE_THRESHOLD_EXCEEDED = "rate_threshold_exceeded"


@dataclass
class Alert:
    """Represents an alert to be sent."""
    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    timestamp: str
    device_serial: str
    
    # Context information
    crash_type: Optional[str] = None
    app_package: Optional[str] = None
    severity: Optional[int] = None
    
    # Aggregation information
    crash_count: int = 1
    time_window_minutes: int = 1
    
    # Additional metadata
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> dict:
        result = asdict(self)
        result['alert_type'] = self.alert_type.value
        result['level'] = self.level.value
        return result


@dataclass
class AlertRule:
    """Configuration for alert rules."""
    crash_type: EnhancedCrashType
    alert_type: AlertType
    level: AlertLevel
    rate_limit_minutes: int
    cascade_threshold: int
    enabled: bool = True


class RateLimiter:
    """Rate limiting to prevent alert spam."""
    
    def __init__(self):
        self.alert_history: Dict[str, float] = {}  # alert_key -> last_sent_timestamp
    
    def can_send_alert(self, alert_key: str, rate_limit_minutes: int) -> bool:
        """Check if an alert can be sent based on rate limiting."""
        now = time.time()
        last_sent = self.alert_history.get(alert_key, 0)
        
        if now - last_sent >= (rate_limit_minutes * 60):
            self.alert_history[alert_key] = now
            return True
        
        return False
    
    def cleanup_old_entries(self, max_age_hours: int = 24):
        """Clean up old rate limiting entries."""
        cutoff = time.time() - (max_age_hours * 3600)
        self.alert_history = {
            key: timestamp for key, timestamp in self.alert_history.items()
            if timestamp > cutoff
        }


class AlertAggregator:
    """Aggregates multiple similar alerts to reduce noise."""
    
    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.pending_alerts: Dict[str, List[Alert]] = {}  # aggregation_key -> alerts
    
    def add_alert(self, alert: Alert) -> Optional[Alert]:
        """Add alert to aggregator, return aggregated alert if ready."""
        # Create aggregation key based on alert type and context
        agg_key = self._get_aggregation_key(alert)
        
        # Add to pending alerts
        if agg_key not in self.pending_alerts:
            self.pending_alerts[agg_key] = []
        
        self.pending_alerts[agg_key].append(alert)
        
        # Check if we should aggregate and send
        return self._check_for_aggregation(agg_key)
    
    def _get_aggregation_key(self, alert: Alert) -> str:
        """Generate aggregation key for similar alerts."""
        return f"{alert.alert_type.value}_{alert.crash_type}_{alert.device_serial}"
    
    def _check_for_aggregation(self, agg_key: str) -> Optional[Alert]:
        """Check if alerts should be aggregated and return aggregated alert."""
        alerts = self.pending_alerts.get(agg_key, [])
        if not alerts:
            return None
        
        # Get the first alert to determine timing
        first_alert = alerts[0]
        first_time = datetime.fromisoformat(first_alert.timestamp.replace('Z', '+00:00'))
        now = datetime.now()
        
        # Check if window has elapsed or we have enough alerts
        time_elapsed = (now - first_time).total_seconds() / 60
        should_aggregate = (
            time_elapsed >= self.window_minutes or 
            len(alerts) >= 5  # Aggregate after 5 similar alerts
        )
        
        if should_aggregate:
            aggregated = self._create_aggregated_alert(alerts)
            del self.pending_alerts[agg_key]  # Clear pending alerts
            return aggregated
        
        return None
    
    def _create_aggregated_alert(self, alerts: List[Alert]) -> Alert:
        """Create an aggregated alert from multiple similar alerts."""
        first_alert = alerts[0]
        count = len(alerts)
        
        # Calculate time window
        timestamps = [datetime.fromisoformat(a.timestamp.replace('Z', '+00:00')) for a in alerts]
        time_span = (max(timestamps) - min(timestamps)).total_seconds() / 60
        
        # Create aggregated alert
        aggregated = Alert(
            alert_id=f"agg_{first_alert.alert_id}_{count}",
            alert_type=first_alert.alert_type,
            level=self._escalate_level_for_aggregation(first_alert.level),
            title=f"Multiple {first_alert.crash_type} errors detected",
            message=f"Detected {count} similar errors in {time_span:.1f} minutes. "
                   f"Original error: {first_alert.message[:100]}...",
            timestamp=datetime.now().isoformat(),
            device_serial=first_alert.device_serial,
            crash_type=first_alert.crash_type,
            app_package=first_alert.app_package,
            severity=max(a.severity or 0 for a in alerts),
            crash_count=count,
            time_window_minutes=int(time_span),
            metadata={
                "aggregated_alerts": [a.alert_id for a in alerts],
                "original_alert_count": count
            }
        )
        
        return aggregated
    
    def _escalate_level_for_aggregation(self, original_level: AlertLevel) -> AlertLevel:
        """Escalate alert level for aggregated alerts."""
        escalation_map = {
            AlertLevel.INFO: AlertLevel.WARNING,
            AlertLevel.WARNING: AlertLevel.ERROR,
            AlertLevel.ERROR: AlertLevel.CRITICAL,
            AlertLevel.CRITICAL: AlertLevel.CRITICAL  # Already at max
        }
        return escalation_map.get(original_level, original_level)


class EnhancedAlertingSystem:
    """Enhanced alerting system for System.err monitoring."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.rate_limiter = RateLimiter()
        self.aggregator = AlertAggregator()
        
        # Alert handlers
        self.alert_handlers: List[Callable[[Alert], None]] = []
        
        # Alert rules configuration
        self.alert_rules = self._create_default_rules()
        
        # Statistics
        self.alert_stats = {
            "total_alerts": 0,
            "alerts_by_type": {},
            "alerts_by_level": {},
            "rate_limited_alerts": 0,
            "aggregated_alerts": 0
        }
    
    def _create_default_rules(self) -> Dict[EnhancedCrashType, AlertRule]:
        """Create default alert rules for enhanced crash types."""
        return {
            EnhancedCrashType.HLS_STREAMING_ERROR: AlertRule(
                crash_type=EnhancedCrashType.HLS_STREAMING_ERROR,
                alert_type=AlertType.HLS_STREAMING_DOWN,
                level=AlertLevel.ERROR,
                rate_limit_minutes=2,  # Allow alerts every 2 minutes
                cascade_threshold=3
            ),
            
            EnhancedCrashType.VIDEO_CODEC_ERROR: AlertRule(
                crash_type=EnhancedCrashType.VIDEO_CODEC_ERROR,
                alert_type=AlertType.VIDEO_CODEC_FAILURE,
                level=AlertLevel.WARNING,
                rate_limit_minutes=5,
                cascade_threshold=2
            ),
            
            EnhancedCrashType.RECEIVER_REGISTRATION_ERROR: AlertRule(
                crash_type=EnhancedCrashType.RECEIVER_REGISTRATION_ERROR,
                alert_type=AlertType.SINGLE_CRASH,
                level=AlertLevel.WARNING,
                rate_limit_minutes=10,
                cascade_threshold=3
            ),
            
            EnhancedCrashType.MEDIA_PIPELINE_ERROR: AlertRule(
                crash_type=EnhancedCrashType.MEDIA_PIPELINE_ERROR,
                alert_type=AlertType.SINGLE_CRASH,
                level=AlertLevel.WARNING,
                rate_limit_minutes=5,
                cascade_threshold=3
            ),
            
            EnhancedCrashType.HARDWARE_ACCELERATION_ERROR: AlertRule(
                crash_type=EnhancedCrashType.HARDWARE_ACCELERATION_ERROR,
                alert_type=AlertType.SYSTEM_INSTABILITY,
                level=AlertLevel.ERROR,
                rate_limit_minutes=3,
                cascade_threshold=2
            ),
            
            EnhancedCrashType.MANIFEST_VALIDATION_ERROR: AlertRule(
                crash_type=EnhancedCrashType.MANIFEST_VALIDATION_ERROR,
                alert_type=AlertType.SINGLE_CRASH,
                level=AlertLevel.WARNING,
                rate_limit_minutes=10,
                cascade_threshold=3
            )
        }
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
    
    def process_enhanced_crash(self, pattern_match: PatternMatch, 
                              device_serial: str, app_package: Optional[str] = None):
        """Process an enhanced crash detection and generate alerts if needed."""
        crash_type = pattern_match.crash_type
        rule = self.alert_rules.get(crash_type)
        
        if not rule or not rule.enabled:
            return
        
        # Check for cascade failure
        is_cascade = pattern_match.additional_context and \
                    pattern_match.additional_context.get("cascade_detected")
        
        if is_cascade:
            self._handle_cascade_alert(pattern_match, device_serial, app_package, rule)
        else:
            self._handle_single_crash_alert(pattern_match, device_serial, app_package, rule)
    
    def _handle_single_crash_alert(self, pattern_match: PatternMatch, 
                                  device_serial: str, app_package: Optional[str], 
                                  rule: AlertRule):
        """Handle alert for a single crash."""
        crash_type = pattern_match.crash_type
        
        # Create rate limiting key
        rate_key = f"{crash_type.value}_{device_serial}_{app_package or 'unknown'}"
        
        # Check rate limiting
        if not self.rate_limiter.can_send_alert(rate_key, rule.rate_limit_minutes):
            self.alert_stats["rate_limited_alerts"] += 1
            return
        
        # Create alert
        alert = Alert(
            alert_id=f"crash_{int(time.time() * 1000)}_{device_serial}",
            alert_type=rule.alert_type,
            level=rule.level,
            title=self._generate_alert_title(crash_type, is_cascade=False),
            message=self._generate_alert_message(pattern_match, is_cascade=False),
            timestamp=datetime.now().isoformat(),
            device_serial=device_serial,
            crash_type=crash_type.value,
            app_package=app_package,
            severity=pattern_match.severity_override,
            metadata=pattern_match.additional_context
        )
        
        # Try aggregation
        aggregated_alert = self.aggregator.add_alert(alert)
        if aggregated_alert:
            self._send_alert(aggregated_alert)
            self.alert_stats["aggregated_alerts"] += 1
        else:
            # Send individual alert for high severity issues
            if rule.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                self._send_alert(alert)
    
    def _handle_cascade_alert(self, pattern_match: PatternMatch, 
                             device_serial: str, app_package: Optional[str], 
                             rule: AlertRule):
        """Handle alert for cascade failure."""
        crash_type = pattern_match.crash_type
        cascade_info = pattern_match.additional_context.get("cascade_detected", {})
        
        # Create high-priority alert for cascade
        alert = Alert(
            alert_id=f"cascade_{int(time.time() * 1000)}_{device_serial}",
            alert_type=AlertType.CASCADE_FAILURE,
            level=AlertLevel.CRITICAL,  # Cascade failures are always critical
            title=f"CASCADE FAILURE: {crash_type.value} errors",
            message=self._generate_cascade_message(pattern_match, cascade_info),
            timestamp=datetime.now().isoformat(),
            device_serial=device_serial,
            crash_type=crash_type.value,
            app_package=app_package,
            severity=10,  # Maximum severity for cascade
            crash_count=cascade_info.get("total_crashes", 1),
            time_window_minutes=cascade_info.get("time_window", 5) / 60,
            metadata={
                "cascade_info": cascade_info,
                "original_context": pattern_match.additional_context
            }
        )
        
        # Send cascade alert immediately (no aggregation/rate limiting)
        self._send_alert(alert)
    
    def _generate_alert_title(self, crash_type: EnhancedCrashType, is_cascade: bool) -> str:
        """Generate alert title based on crash type."""
        titles = {
            EnhancedCrashType.HLS_STREAMING_ERROR: "HLS Streaming Failure",
            EnhancedCrashType.VIDEO_CODEC_ERROR: "Video Codec Error",
            EnhancedCrashType.RECEIVER_REGISTRATION_ERROR: "Receiver Registration Issue",
            EnhancedCrashType.MEDIA_PIPELINE_ERROR: "Media Pipeline Error",
            EnhancedCrashType.HARDWARE_ACCELERATION_ERROR: "Hardware Acceleration Failure",
            EnhancedCrashType.MANIFEST_VALIDATION_ERROR: "Media Manifest Validation Error"
        }
        
        base_title = titles.get(crash_type, "Enhanced Crash Detected")
        return f"CASCADE: {base_title}" if is_cascade else base_title
    
    def _generate_alert_message(self, pattern_match: PatternMatch, is_cascade: bool) -> str:
        """Generate detailed alert message."""
        crash_type = pattern_match.crash_type
        context = pattern_match.additional_context or {}
        
        base_messages = {
            EnhancedCrashType.HLS_STREAMING_ERROR: 
                f"HLS streaming error detected. Pattern: {pattern_match.pattern[:50]}... "
                f"This typically indicates video playback issues in browsers or media apps.",
            
            EnhancedCrashType.VIDEO_CODEC_ERROR:
                f"Video codec error detected. Pattern: {pattern_match.pattern[:50]}... "
                f"This may affect video playback performance and quality.",
            
            EnhancedCrashType.RECEIVER_REGISTRATION_ERROR:
                f"Broadcast receiver registration error. Pattern: {pattern_match.pattern[:50]}... "
                f"This indicates app lifecycle management issues.",
            
            EnhancedCrashType.MEDIA_PIPELINE_ERROR:
                f"Media pipeline error detected. Pattern: {pattern_match.pattern[:50]}... "
                f"This affects media playback functionality.",
            
            EnhancedCrashType.HARDWARE_ACCELERATION_ERROR:
                f"Hardware acceleration error detected. Pattern: {pattern_match.pattern[:50]}... "
                f"This may degrade system graphics performance.",
            
            EnhancedCrashType.MANIFEST_VALIDATION_ERROR:
                f"Media manifest validation error. Pattern: {pattern_match.pattern[:50]}... "
                f"This indicates issues with media content format validation."
        }
        
        message = base_messages.get(crash_type, f"Enhanced crash detected: {pattern_match.pattern[:100]}...")
        
        # Add context information
        if "likely_app" in context:
            message += f" Likely app: {context['likely_app']}"
        
        if "codec_type" in context:
            message += f" Codec: {context['codec_type']}"
        
        if "streaming_protocol" in context:
            message += f" Protocol: {context['streaming_protocol']}"
        
        message += f" Confidence: {pattern_match.confidence:.1%}"
        
        return message
    
    def _generate_cascade_message(self, pattern_match: PatternMatch, 
                                 cascade_info: Dict) -> str:
        """Generate message for cascade failure."""
        crash_count = cascade_info.get("total_crashes", 0)
        time_window = cascade_info.get("time_window", 5)
        dominant_type = cascade_info.get("dominant_type", "unknown")
        
        message = (
            f"CASCADE FAILURE DETECTED: {crash_count} crashes in {time_window} seconds. "
            f"Dominant type: {dominant_type}. "
            f"This indicates a serious system instability issue requiring immediate attention."
        )
        
        context = pattern_match.additional_context or {}
        if "likely_app" in context:
            message += f" Primary app affected: {context['likely_app']}"
        
        return message
    
    def _send_alert(self, alert: Alert):
        """Send alert through all registered handlers."""
        # Update statistics
        self.alert_stats["total_alerts"] += 1
        
        alert_type_str = alert.alert_type.value
        self.alert_stats["alerts_by_type"][alert_type_str] = \
            self.alert_stats["alerts_by_type"].get(alert_type_str, 0) + 1
        
        level_str = alert.level.value
        self.alert_stats["alerts_by_level"][level_str] = \
            self.alert_stats["alerts_by_level"].get(level_str, 0) + 1
        
        # Save alert to file
        self._save_alert(alert)
        
        # Send to handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                # Log error but continue with other handlers
                print(f"Alert handler error: {e}")
    
    def _save_alert(self, alert: Alert):
        """Save alert to file for audit trail."""
        try:
            alerts_dir = self.output_dir / "alerts"
            alerts_dir.mkdir(exist_ok=True)
            
            filename = f"alert_{alert.alert_id}.json"
            filepath = alerts_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(alert.to_dict(), f, indent=2, default=str)
                
        except Exception as e:
            print(f"Failed to save alert: {e}")
    
    def get_alert_statistics(self) -> Dict:
        """Get alert system statistics."""
        # Clean up old rate limiter entries
        self.rate_limiter.cleanup_old_entries()
        
        return {
            **self.alert_stats,
            "rate_limiter_entries": len(self.rate_limiter.alert_history),
            "pending_aggregations": len(self.aggregator.pending_alerts),
            "active_alert_rules": len([r for r in self.alert_rules.values() if r.enabled])
        }
    
    def update_alert_rule(self, crash_type: EnhancedCrashType, **kwargs):
        """Update an alert rule configuration."""
        if crash_type not in self.alert_rules:
            return
        
        rule = self.alert_rules[crash_type]
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)