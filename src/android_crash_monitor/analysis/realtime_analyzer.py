#!/usr/bin/env python3
"""
Real-time Pattern Detection Engine

Provides live analysis of crashes as they occur during monitoring,
with immediate alerts and dynamic confidence tracking.
"""

import threading
import time
import queue
from collections import deque, defaultdict
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from .enhanced_pattern_detector import StatisticalPatternDetector, EnhancedPattern, PatternSeverity, PatternType

class AlertLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

@dataclass
class RealTimeAlert:
    """Real-time alert for immediate pattern detection"""
    alert_id: str
    level: AlertLevel
    pattern_name: str
    message: str
    confidence: float
    urgency: int
    timestamp: datetime
    crash_data: Dict
    recommended_action: str
    auto_dismissible: bool = True

@dataclass
class RealtimeStats:
    """Real-time statistics tracking"""
    total_crashes: int = 0
    crashes_last_minute: int = 0
    crashes_last_5min: int = 0
    crashes_last_hour: int = 0
    patterns_detected: int = 0
    alerts_fired: int = 0
    highest_confidence: float = 0.0
    most_critical_pattern: Optional[str] = None
    monitoring_start_time: datetime = field(default_factory=datetime.now)

class RealtimePatternAnalyzer:
    """
    Real-time pattern analyzer that processes crashes as they occur
    and provides immediate alerts for critical patterns
    """
    
    def __init__(self, 
                 buffer_size: int = 500,
                 analysis_window_minutes: int = 30,
                 min_confidence_threshold: float = 0.7,
                 alert_callback: Optional[Callable[[RealTimeAlert], None]] = None):
        
        self.buffer_size = buffer_size
        self.analysis_window_minutes = analysis_window_minutes
        self.min_confidence_threshold = min_confidence_threshold
        self.alert_callback = alert_callback
        
        # Real-time data structures
        self.crash_buffer = deque(maxlen=buffer_size)
        self.crash_queue = queue.Queue()
        self.pattern_history = defaultdict(list)
        self.active_patterns = {}
        self.fired_alerts = []
        self.stats = RealtimeStats()
        
        # Threading control
        self.processing_thread = None
        self.is_running = False
        self.lock = threading.RLock()
        
        # Pattern detector
        self.detector = StatisticalPatternDetector(
            min_pattern_frequency=2,  # Lower threshold for real-time
            confidence_threshold=0.5   # Lower threshold for early detection
        )
        
        # Alert configuration
        self.alert_thresholds = {
            PatternSeverity.LOW: {
                'min_confidence': 0.6,
                'min_frequency': 3,
                'alert_level': AlertLevel.LOW
            },
            PatternSeverity.MEDIUM: {
                'min_confidence': 0.65,
                'min_frequency': 2,
                'alert_level': AlertLevel.MEDIUM
            },
            PatternSeverity.HIGH: {
                'min_confidence': 0.7,
                'min_frequency': 2,
                'alert_level': AlertLevel.HIGH
            },
            PatternSeverity.CRITICAL: {
                'min_confidence': 0.6,  # Lower threshold for critical patterns
                'min_frequency': 1,      # Even single critical crashes matter
                'alert_level': AlertLevel.CRITICAL
            }
        }
        
        # Burst detection settings
        self.burst_threshold = 3  # 3 crashes per minute = burst
        self.cascade_threshold = 2  # 2 different patterns = cascade risk
    
    def start_realtime_analysis(self) -> bool:
        """Start real-time analysis in background thread"""
        if self.is_running:
            return False
        
        self.is_running = True
        self.stats.monitoring_start_time = datetime.now()
        
        self.processing_thread = threading.Thread(
            target=self._process_crashes_continuously,
            daemon=True,
            name="RealtimeAnalyzer"
        )
        self.processing_thread.start()
        
        return True
    
    def stop_realtime_analysis(self) -> bool:
        """Stop real-time analysis"""
        if not self.is_running:
            return False
        
        self.is_running = False
        
        # Signal processing thread to stop
        self.crash_queue.put(None)  # Sentinel value
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        
        return True
    
    def add_crash(self, crash_data: Dict) -> None:
        """Add new crash data for real-time analysis"""
        if not self.is_running:
            return
        
        # Add timestamp if not present
        if 'timestamp' not in crash_data:
            crash_data['timestamp'] = datetime.now().strftime('%m-%d %H:%M:%S.%f')[:-3]
        
        # Queue for processing
        try:
            self.crash_queue.put(crash_data, block=False)
        except queue.Full:
            # Drop oldest crash if queue is full
            try:
                self.crash_queue.get(block=False)
                self.crash_queue.put(crash_data, block=False)
            except queue.Empty:
                pass
    
    def get_realtime_stats(self) -> RealtimeStats:
        """Get current real-time statistics"""
        with self.lock:
            # Update time-based counters
            now = datetime.now()
            
            # Count crashes in different time windows
            self.stats.crashes_last_minute = sum(
                1 for crash in self.crash_buffer
                if self._get_crash_timestamp(crash) and
                (now - self._get_crash_timestamp(crash)).total_seconds() <= 60
            )
            
            self.stats.crashes_last_5min = sum(
                1 for crash in self.crash_buffer
                if self._get_crash_timestamp(crash) and
                (now - self._get_crash_timestamp(crash)).total_seconds() <= 300
            )
            
            self.stats.crashes_last_hour = sum(
                1 for crash in self.crash_buffer
                if self._get_crash_timestamp(crash) and
                (now - self._get_crash_timestamp(crash)).total_seconds() <= 3600
            )
            
            return self.stats
    
    def get_active_patterns(self) -> List[EnhancedPattern]:
        """Get currently active patterns"""
        with self.lock:
            return list(self.active_patterns.values())
    
    def get_recent_alerts(self, limit: int = 10) -> List[RealTimeAlert]:
        """Get most recent alerts"""
        with self.lock:
            return self.fired_alerts[-limit:]
    
    def configure_alert_thresholds(self, 
                                 severity: PatternSeverity,
                                 min_confidence: float,
                                 min_frequency: int,
                                 alert_level: AlertLevel) -> None:
        """Configure alert thresholds for a pattern severity"""
        with self.lock:
            self.alert_thresholds[severity] = {
                'min_confidence': min_confidence,
                'min_frequency': min_frequency,
                'alert_level': alert_level
            }
    
    def _process_crashes_continuously(self) -> None:
        """Continuously process crashes from the queue"""
        while self.is_running:
            try:
                # Get crash from queue (blocking with timeout)
                crash_data = self.crash_queue.get(timeout=1.0)
                
                # Check for stop signal
                if crash_data is None:
                    break
                
                # Process the crash
                self._process_single_crash(crash_data)
                
            except queue.Empty:
                # Timeout - continue monitoring
                continue
            except Exception as e:
                print(f"Error processing crash in real-time: {e}")
                continue
    
    def _process_single_crash(self, crash_data: Dict) -> None:
        """Process a single crash for real-time pattern detection"""
        with self.lock:
            # Add to buffer
            self.crash_buffer.append(crash_data)
            self.stats.total_crashes += 1
            
            # Get recent crashes for analysis (sliding window)
            recent_crashes = self._get_recent_crashes()
            
            # Run pattern detection on recent crashes
            if len(recent_crashes) >= 2:  # Need at least 2 crashes for patterns
                detected_patterns = self.detector.analyze_crash_patterns(recent_crashes)
                
                # Process each detected pattern
                for pattern in detected_patterns:
                    self._update_pattern_tracking(pattern)
                    
                    # Check if pattern should trigger an alert
                    if self._should_trigger_alert(pattern):
                        alert = self._create_alert(pattern, crash_data)
                        self._fire_alert(alert)
                
                # Check for burst patterns
                burst_alert = self._check_burst_pattern(crash_data)
                if burst_alert:
                    self._fire_alert(burst_alert)
                
                # Check for cascade patterns
                cascade_alert = self._check_cascade_pattern()
                if cascade_alert:
                    self._fire_alert(cascade_alert)
            
            # Clean up old data
            self._cleanup_old_data()
    
    def _get_recent_crashes(self) -> List[Dict]:
        """Get crashes from recent analysis window"""
        now = datetime.now()
        cutoff = now - timedelta(minutes=self.analysis_window_minutes)
        
        recent = []
        for crash in reversed(self.crash_buffer):  # Most recent first
            crash_time = self._get_crash_timestamp(crash)
            # If timestamp parsing fails, include the crash anyway (assume it's recent)
            if crash_time is None:
                recent.append(crash)
            elif crash_time >= cutoff:
                recent.append(crash)
            elif crash_time < cutoff:
                break  # Buffer is ordered, so we can stop here
        
        return list(reversed(recent))  # Return in chronological order
    
    def _get_crash_timestamp(self, crash: Dict) -> Optional[datetime]:
        """Parse crash timestamp"""
        timestamp_str = crash.get('timestamp', '')
        if not timestamp_str:
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',  # Try with year first
            '%Y-%m-%d %H:%M:%S',
            '%m-%d %H:%M:%S.%f',
            '%m-%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(timestamp_str.strip(), fmt)
                # For formats without year, assume current year
                if '%Y' not in fmt:
                    parsed = parsed.replace(year=datetime.now().year)
                return parsed
            except ValueError:
                continue
        
        return None
    
    def _update_pattern_tracking(self, pattern: EnhancedPattern) -> None:
        """Update pattern tracking with new detection"""
        pattern_key = pattern.pattern_id
        
        # Update active patterns
        if pattern_key in self.active_patterns:
            # Update existing pattern
            existing = self.active_patterns[pattern_key]
            existing.frequency = pattern.frequency
            existing.confidence_score = pattern.confidence_score
            existing.correlation_strength = pattern.correlation_strength
            existing.temporal_clustering_score = pattern.temporal_clustering_score
        else:
            # New pattern detected
            self.active_patterns[pattern_key] = pattern
            self.stats.patterns_detected += 1
        
        # Track pattern history
        self.pattern_history[pattern_key].append({
            'timestamp': datetime.now(),
            'confidence': pattern.confidence_score,
            'frequency': pattern.frequency,
            'urgency': pattern.urgency_level
        })
        
        # Update stats
        if pattern.confidence_score > self.stats.highest_confidence:
            self.stats.highest_confidence = pattern.confidence_score
            self.stats.most_critical_pattern = pattern.name
    
    def _should_trigger_alert(self, pattern: EnhancedPattern) -> bool:
        """Check if pattern should trigger an alert"""
        
        # Get alert threshold for this pattern severity
        threshold_config = self.alert_thresholds.get(pattern.severity)
        if not threshold_config:
            return False
        
        # Check confidence and frequency thresholds
        if pattern.confidence_score < threshold_config['min_confidence']:
            return False
        
        if pattern.frequency < threshold_config['min_frequency']:
            return False
        
        # Check if we've already alerted for this pattern recently
        pattern_key = pattern.pattern_id
        recent_alerts = [
            alert for alert in self.fired_alerts[-10:]  # Check last 10 alerts
            if alert.pattern_name == pattern_key and
            (datetime.now() - alert.timestamp).total_seconds() < 300  # Within 5 minutes
        ]
        
        # For critical patterns, allow more frequent alerts
        if pattern.severity == PatternSeverity.CRITICAL:
            max_recent_alerts = 2
        else:
            max_recent_alerts = 1
        
        return len(recent_alerts) < max_recent_alerts
    
    def _create_alert(self, pattern: EnhancedPattern, crash_data: Dict) -> RealTimeAlert:
        """Create alert for detected pattern"""
        
        threshold_config = self.alert_thresholds[pattern.severity]
        alert_level = threshold_config['alert_level']
        
        # Generate alert message
        if pattern.severity == PatternSeverity.CRITICAL:
            message = f"🚨 CRITICAL: {pattern.name} detected with {pattern.confidence_score:.1%} confidence"
        elif pattern.severity == PatternSeverity.HIGH:
            message = f"⚠️ HIGH: {pattern.name} pattern detected ({pattern.frequency} occurrences)"
        else:
            message = f"ℹ️ {pattern.severity.name}: {pattern.name} pattern emerging"
        
        # Get recommended action
        recommended_action = "Monitor closely"
        if pattern.recommended_actions:
            recommended_action = pattern.recommended_actions[0]
        
        return RealTimeAlert(
            alert_id=f"{pattern.pattern_id}_{int(time.time())}",
            level=alert_level,
            pattern_name=pattern.pattern_id,
            message=message,
            confidence=pattern.confidence_score,
            urgency=pattern.urgency_level,
            timestamp=datetime.now(),
            crash_data=crash_data,
            recommended_action=recommended_action,
            auto_dismissible=(alert_level.value <= AlertLevel.MEDIUM.value)
        )
    
    def _check_burst_pattern(self, crash_data: Dict) -> Optional[RealTimeAlert]:
        """Check for burst pattern (too many crashes too quickly)"""
        
        # Count crashes in last minute
        now = datetime.now()
        recent_crashes = [
            crash for crash in self.crash_buffer
            if self._get_crash_timestamp(crash) and
            (now - self._get_crash_timestamp(crash)).total_seconds() <= 60
        ]
        
        if len(recent_crashes) >= self.burst_threshold:
            return RealTimeAlert(
                alert_id=f"burst_{int(time.time())}",
                level=AlertLevel.EMERGENCY,
                pattern_name="crash_burst",
                message=f"🚨 EMERGENCY: {len(recent_crashes)} crashes in last minute - BURST DETECTED",
                confidence=0.95,
                urgency=10,
                timestamp=now,
                crash_data=crash_data,
                recommended_action="Immediately restart device to break crash spiral",
                auto_dismissible=False
            )
        
        return None
    
    def _check_cascade_pattern(self) -> Optional[RealTimeAlert]:
        """Check for cascade pattern (multiple different pattern types active)"""
        
        # Count active patterns with high confidence
        high_confidence_patterns = [
            pattern for pattern in self.active_patterns.values()
            if pattern.confidence_score >= 0.7
        ]
        
        if len(high_confidence_patterns) >= self.cascade_threshold:
            pattern_names = [p.name for p in high_confidence_patterns]
            
            return RealTimeAlert(
                alert_id=f"cascade_{int(time.time())}",
                level=AlertLevel.CRITICAL,
                pattern_name="cascade_failure",
                message=f"🔴 CASCADE FAILURE: {len(high_confidence_patterns)} patterns active simultaneously",
                confidence=0.9,
                urgency=9,
                timestamp=datetime.now(),
                crash_data={'patterns': pattern_names},
                recommended_action="System instability detected - restart device immediately",
                auto_dismissible=False
            )
        
        return None
    
    def _fire_alert(self, alert: RealTimeAlert) -> None:
        """Fire an alert and call callback if configured"""
        
        # Add to fired alerts list
        self.fired_alerts.append(alert)
        self.stats.alerts_fired += 1
        
        # Keep only recent alerts in memory
        if len(self.fired_alerts) > 100:
            self.fired_alerts = self.fired_alerts[-50:]  # Keep last 50
        
        # Call alert callback if configured
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Clean up old pattern history and data"""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)  # Keep 1 hour of history
        
        # Clean pattern history
        for pattern_id in list(self.pattern_history.keys()):
            history = self.pattern_history[pattern_id]
            # Keep only recent entries
            recent_history = [
                entry for entry in history
                if entry['timestamp'] >= cutoff
            ]
            
            if recent_history:
                self.pattern_history[pattern_id] = recent_history
            else:
                # Remove pattern if no recent activity
                del self.pattern_history[pattern_id]
                if pattern_id in self.active_patterns:
                    del self.active_patterns[pattern_id]
    
    def export_realtime_state(self) -> Dict:
        """Export current real-time analysis state"""
        with self.lock:
            return {
                'stats': {
                    'total_crashes': self.stats.total_crashes,
                    'crashes_last_minute': self.stats.crashes_last_minute,
                    'crashes_last_5min': self.stats.crashes_last_5min,
                    'crashes_last_hour': self.stats.crashes_last_hour,
                    'patterns_detected': self.stats.patterns_detected,
                    'alerts_fired': self.stats.alerts_fired,
                    'highest_confidence': self.stats.highest_confidence,
                    'most_critical_pattern': self.stats.most_critical_pattern,
                    'monitoring_duration_minutes': (datetime.now() - self.stats.monitoring_start_time).total_seconds() / 60
                },
                'active_patterns': [
                    {
                        'id': p.pattern_id,
                        'name': p.name,
                        'severity': p.severity.name,
                        'confidence': p.confidence_score,
                        'frequency': p.frequency,
                        'urgency': p.urgency_level
                    }
                    for p in self.active_patterns.values()
                ],
                'recent_alerts': [
                    {
                        'id': a.alert_id,
                        'level': a.level.name,
                        'message': a.message,
                        'timestamp': a.timestamp.isoformat(),
                        'confidence': a.confidence,
                        'urgency': a.urgency
                    }
                    for a in self.fired_alerts[-10:]
                ]
            }