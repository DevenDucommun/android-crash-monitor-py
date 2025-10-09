#!/usr/bin/env python3
"""
Pattern Detector - Advanced crash pattern recognition

Uses machine learning-like approaches and statistical analysis to detect
complex crash patterns and correlations.
"""

import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PatternMatch:
    """Represents a detected pattern match."""
    pattern_name: str
    confidence: float  # 0.0-1.0
    evidence: List[str]
    frequency: int
    severity_score: float
    metadata: Dict[str, any]


class PatternDetector:
    """
    Advanced pattern detection using statistical analysis and heuristics
    to identify complex crash patterns and correlations.
    """
    
    # Advanced pattern definitions with regex and correlation rules
    ADVANCED_PATTERNS = {
        'memory_pressure_cascade': {
            'primary_indicators': [
                r'OutOfMemoryError',
                r'memory.*pressure',
                r'Low.*memory',
                r'GC.*overhead'
            ],
            'secondary_indicators': [
                r'Activity.*not responding',
                r'Process.*killed',
                r'Unable to create new native thread'
            ],
            'correlation_threshold': 0.7,
            'time_window_minutes': 10
        },
        'network_connectivity_storm': {
            'primary_indicators': [
                r'Network.*unreachable',
                r'Connection.*refused',
                r'SSL.*handshake.*failed',
                r'Timeout.*connecting'
            ],
            'secondary_indicators': [
                r'DNS.*resolution.*failed',
                r'Certificate.*error',
                r'Socket.*exception'
            ],
            'correlation_threshold': 0.6,
            'time_window_minutes': 5
        },
        'service_binding_failure_chain': {
            'primary_indicators': [
                r'Unable to bind.*service',
                r'Service.*connection.*lost',
                r'Binder.*transaction.*failed'
            ],
            'secondary_indicators': [
                r'DeadObjectException',
                r'RemoteException',
                r'Service.*not found'
            ],
            'correlation_threshold': 0.8,
            'time_window_minutes': 3
        },
        'ui_thread_blocking_pattern': {
            'primary_indicators': [
                r'ANR in.*main',
                r'UI thread.*blocked',
                r'Choreographer.*skipped.*frames'
            ],
            'secondary_indicators': [
                r'long running.*operation',
                r'blocking.*UI.*thread',
                r'StrictMode.*violation'
            ],
            'correlation_threshold': 0.5,
            'time_window_minutes': 2
        },
        'storage_exhaustion_cascade': {
            'primary_indicators': [
                r'No space left',
                r'ENOSPC',
                r'Disk.*full',
                r'Storage.*exhausted'
            ],
            'secondary_indicators': [
                r'Cache.*directory.*full',
                r'Unable.*write.*file',
                r'SQLite.*disk.*full'
            ],
            'correlation_threshold': 0.9,
            'time_window_minutes': 15
        }
    }
    
    def __init__(self):
        """Initialize pattern detector."""
        self.compiled_patterns = {}
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        for pattern_name, config in self.ADVANCED_PATTERNS.items():
            self.compiled_patterns[pattern_name] = {
                'primary': [re.compile(pattern, re.IGNORECASE) 
                           for pattern in config['primary_indicators']],
                'secondary': [re.compile(pattern, re.IGNORECASE) 
                             for pattern in config['secondary_indicators']],
                'config': config
            }
            
    def detect_patterns(self, crashes: List[Dict]) -> List[PatternMatch]:
        """Detect advanced patterns in crash data."""
        matches = []
        
        for pattern_name, compiled_pattern in self.compiled_patterns.items():
            match = self._detect_pattern(pattern_name, compiled_pattern, crashes)
            if match:
                matches.append(match)
                
        # Sort by confidence and severity
        matches.sort(key=lambda x: (x.confidence * x.severity_score), reverse=True)
        return matches
        
    def _detect_pattern(self, pattern_name: str, compiled_pattern: Dict, 
                       crashes: List[Dict]) -> Optional[PatternMatch]:
        """Detect a specific pattern in crashes."""
        primary_matches = []
        secondary_matches = []
        
        # Find all crashes matching primary and secondary indicators
        for crash in crashes:
            crash_text = self._extract_crash_text(crash)
            
            # Check primary indicators
            for regex in compiled_pattern['primary']:
                if regex.search(crash_text):
                    primary_matches.append(crash)
                    break
                    
            # Check secondary indicators
            for regex in compiled_pattern['secondary']:
                if regex.search(crash_text):
                    secondary_matches.append(crash)
                    break
                    
        if not primary_matches:
            return None
            
        # Calculate correlation and temporal clustering
        config = compiled_pattern['config']
        correlation = self._calculate_correlation(
            primary_matches, secondary_matches, 
            config['time_window_minutes']
        )
        
        if correlation < config['correlation_threshold']:
            return None
            
        # Calculate confidence based on multiple factors
        confidence = self._calculate_confidence(
            primary_matches, secondary_matches, correlation
        )
        
        # Calculate severity score
        severity_score = self._calculate_severity_score(
            pattern_name, len(primary_matches), correlation
        )
        
        # Generate evidence
        evidence = self._generate_evidence(
            pattern_name, primary_matches, secondary_matches, correlation
        )
        
        return PatternMatch(
            pattern_name=pattern_name,
            confidence=confidence,
            evidence=evidence,
            frequency=len(primary_matches),
            severity_score=severity_score,
            metadata={
                'primary_matches': len(primary_matches),
                'secondary_matches': len(secondary_matches),
                'correlation': correlation,
                'time_span_minutes': self._calculate_time_span(primary_matches)
            }
        )
        
    def _extract_crash_text(self, crash: Dict) -> str:
        """Extract searchable text from crash data."""
        texts = [
            crash.get('description', ''),
            crash.get('title', ''),
            crash.get('app_name', ''),
        ]
        
        # Add related log messages
        for log_entry in crash.get('related_logs', []):
            texts.append(log_entry.get('message', ''))
            
        # Add stack trace
        if crash.get('stack_trace'):
            texts.extend(crash['stack_trace'])
            
        return ' '.join(texts)
        
    def _calculate_correlation(self, primary_matches: List[Dict], 
                             secondary_matches: List[Dict], 
                             time_window_minutes: int) -> float:
        """Calculate temporal correlation between primary and secondary matches."""
        if not primary_matches or not secondary_matches:
            return 0.0
            
        # Parse timestamps and create time windows
        primary_times = []
        secondary_times = []
        
        for crash in primary_matches:
            timestamp = self._parse_timestamp(crash.get('timestamp', ''))
            if timestamp:
                primary_times.append(timestamp)
                
        for crash in secondary_matches:
            timestamp = self._parse_timestamp(crash.get('timestamp', ''))
            if timestamp:
                secondary_times.append(timestamp)
                
        if not primary_times or not secondary_times:
            return 0.0
            
        # Count correlated events (secondary events within time window of primary)
        correlated_count = 0
        time_window = timedelta(minutes=time_window_minutes)
        
        for primary_time in primary_times:
            for secondary_time in secondary_times:
                if abs(secondary_time - primary_time) <= time_window:
                    correlated_count += 1
                    break
                    
        # Calculate correlation ratio
        correlation = correlated_count / len(primary_times)
        return min(1.0, correlation)  # Cap at 1.0
        
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return None
            
        try:
            # Handle format: "MM-DD HH:MM:SS.mmm"
            if len(timestamp_str) >= 15:
                # Assume current year
                year = datetime.now().year
                month_day_time = timestamp_str[:15]  # "MM-DD HH:MM:SS"
                full_timestamp = f"{year}-{month_day_time}"
                return datetime.strptime(full_timestamp, "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
            
        return None
        
    def _calculate_confidence(self, primary_matches: List[Dict], 
                            secondary_matches: List[Dict], 
                            correlation: float) -> float:
        """Calculate confidence score for pattern match."""
        # Base confidence from correlation
        confidence = correlation
        
        # Boost confidence based on frequency
        frequency_boost = min(0.3, len(primary_matches) / 20.0)  # Max 30% boost
        confidence += frequency_boost
        
        # Boost confidence if secondary indicators present
        if secondary_matches:
            secondary_boost = min(0.2, len(secondary_matches) / 10.0)  # Max 20% boost
            confidence += secondary_boost
            
        return min(1.0, confidence)  # Cap at 1.0
        
    def _calculate_severity_score(self, pattern_name: str, frequency: int, 
                                correlation: float) -> float:
        """Calculate severity score for pattern."""
        base_severities = {
            'memory_pressure_cascade': 8.5,
            'network_connectivity_storm': 6.0,
            'service_binding_failure_chain': 7.5,
            'ui_thread_blocking_pattern': 7.0,
            'storage_exhaustion_cascade': 9.0
        }
        
        base_severity = base_severities.get(pattern_name, 5.0)
        
        # Adjust based on frequency and correlation
        frequency_multiplier = min(1.5, 1.0 + (frequency / 20.0))
        correlation_multiplier = 0.5 + (correlation * 0.5)
        
        severity = base_severity * frequency_multiplier * correlation_multiplier
        return min(10.0, severity)  # Cap at 10.0
        
    def _generate_evidence(self, pattern_name: str, primary_matches: List[Dict],
                          secondary_matches: List[Dict], correlation: float) -> List[str]:
        """Generate evidence list for pattern match."""
        evidence = []
        
        evidence.append(f"Primary indicators found in {len(primary_matches)} crashes")
        
        if secondary_matches:
            evidence.append(f"Secondary indicators found in {len(secondary_matches)} crashes")
            
        evidence.append(f"Temporal correlation: {correlation:.1%}")
        
        # Add specific examples
        if primary_matches:
            first_app = primary_matches[0].get('app_name', 'Unknown')
            evidence.append(f"Example affected component: {first_app}")
            
        # Add time span information
        time_span = self._calculate_time_span(primary_matches)
        if time_span > 0:
            evidence.append(f"Pattern occurs over {time_span:.1f} minute time span")
            
        return evidence
        
    def _calculate_time_span(self, matches: List[Dict]) -> float:
        """Calculate time span of matches in minutes."""
        timestamps = []
        
        for match in matches:
            timestamp = self._parse_timestamp(match.get('timestamp', ''))
            if timestamp:
                timestamps.append(timestamp)
                
        if len(timestamps) < 2:
            return 0.0
            
        time_span = max(timestamps) - min(timestamps)
        return time_span.total_seconds() / 60.0  # Convert to minutes
        
    def detect_anomalies(self, crashes: List[Dict]) -> List[Dict[str, any]]:
        """Detect statistical anomalies in crash data."""
        anomalies = []
        
        # Detect frequency anomalies
        app_frequencies = Counter(crash.get('app_name', 'Unknown') for crash in crashes)
        frequency_anomalies = self._detect_frequency_anomalies(app_frequencies)
        anomalies.extend(frequency_anomalies)
        
        # Detect timing anomalies
        timing_anomalies = self._detect_timing_anomalies(crashes)
        anomalies.extend(timing_anomalies)
        
        return anomalies
        
    def _detect_frequency_anomalies(self, frequencies: Counter) -> List[Dict[str, any]]:
        """Detect apps with unusually high crash frequencies."""
        if not frequencies:
            return []
            
        values = list(frequencies.values())
        mean_freq = sum(values) / len(values)
        std_dev = math.sqrt(sum((x - mean_freq) ** 2 for x in values) / len(values))
        
        anomalies = []
        threshold = mean_freq + (2 * std_dev)  # 2 standard deviations
        
        for app, freq in frequencies.items():
            if freq > threshold and freq > 5:  # At least 5 crashes
                anomalies.append({
                    'type': 'frequency_anomaly',
                    'app_name': app,
                    'crash_count': freq,
                    'severity': min(10.0, freq / mean_freq),
                    'description': f'{app} has {freq} crashes (expected ~{mean_freq:.1f})'
                })
                
        return anomalies
        
    def _detect_timing_anomalies(self, crashes: List[Dict]) -> List[Dict[str, any]]:
        """Detect unusual timing patterns in crashes."""
        # Group crashes by hour to detect timing patterns
        hour_counts = defaultdict(int)
        
        for crash in crashes:
            timestamp = self._parse_timestamp(crash.get('timestamp', ''))
            if timestamp:
                hour_counts[timestamp.hour] += 1
                
        if not hour_counts:
            return []
            
        # Find hours with significantly more crashes
        values = list(hour_counts.values())
        if not values:
            return []
            
        mean_hourly = sum(values) / len(values)
        anomalies = []
        
        for hour, count in hour_counts.items():
            if count > mean_hourly * 3:  # 3x the average
                anomalies.append({
                    'type': 'timing_anomaly',
                    'hour': hour,
                    'crash_count': count,
                    'severity': min(10.0, count / mean_hourly),
                    'description': f'Hour {hour}:00 has {count} crashes (avg: {mean_hourly:.1f})'
                })
                
        return anomalies