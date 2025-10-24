#!/usr/bin/env python3
"""
Enhanced Statistical Pattern Detector

Advanced crash pattern recognition using:
- Statistical correlation analysis
- Temporal clustering 
- Multi-factor confidence scoring
- Frequency-based pattern detection
- Burst pattern identification
"""

import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

class PatternSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class PatternType(Enum):
    SIMPLE = "simple"
    CORRELATED = "correlated"
    TEMPORAL = "temporal"
    BURST = "burst"
    CASCADE = "cascade"

@dataclass
class EnhancedPattern:
    """Represents an enhanced pattern match with statistical confidence"""
    pattern_id: str
    pattern_type: PatternType
    name: str
    description: str
    
    # Statistical metrics
    frequency: int
    confidence_score: float  # 0.0-1.0
    correlation_strength: float  # 0.0-1.0
    temporal_clustering_score: float  # 0.0-1.0
    severity: PatternSeverity
    
    # Evidence and context
    evidence: List[str] = field(default_factory=list)
    affected_crashes: List[Dict] = field(default_factory=list)
    time_windows: List[Tuple[datetime, datetime]] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    urgency_level: int = 0  # 1-10 scale

class StatisticalPatternDetector:
    """
    Enhanced pattern detector using statistical analysis and machine learning techniques
    """
    
    def __init__(self, min_pattern_frequency: int = 3, confidence_threshold: float = 0.6):
        self.min_pattern_frequency = min_pattern_frequency
        self.confidence_threshold = confidence_threshold
        
        # Pattern definitions with statistical weights
        self.pattern_definitions = {
            'memory_exhaustion_cascade': {
                'primary_indicators': [
                    (r'OutOfMemoryError', 1.0),
                    (r'GC.*overhead.*limit.*exceeded', 0.9),
                    (r'Unable to create new native thread', 0.8),
                    (r'java.lang.OutOfMemoryError', 1.0)
                ],
                'secondary_indicators': [
                    (r'Activity.*not responding', 0.7),
                    (r'Process.*killed.*low memory', 0.8),
                    (r'Heap.*size.*exceeded', 0.6),
                    (r'Native allocation.*failed', 0.7)
                ],
                'correlation_weight': 0.8,
                'temporal_window_minutes': 10,
                'severity': PatternSeverity.CRITICAL
            },
            
            'database_corruption_spiral': {
                'primary_indicators': [
                    (r'SQLiteException', 0.9),
                    (r'database.*corrupt', 1.0),
                    (r'connection pool.*closed', 0.8),
                    (r'database.*locked', 0.7)
                ],
                'secondary_indicators': [
                    (r'I/O.*error', 0.6),
                    (r'disk.*full', 0.8),
                    (r'metadata.*corrupted', 0.9),
                    (r'integrity.*check.*failed', 0.9)
                ],
                'correlation_weight': 0.85,
                'temporal_window_minutes': 15,
                'severity': PatternSeverity.HIGH
            },
            
            'service_binding_failure_chain': {
                'primary_indicators': [
                    (r'Unable to bind.*service', 0.9),
                    (r'ServiceConnection.*leaked', 0.8),
                    (r'Binder.*transaction.*failed', 0.8),
                    (r'DeadObjectException', 0.9)
                ],
                'secondary_indicators': [
                    (r'RemoteException', 0.6),
                    (r'Service.*not.*found', 0.7),
                    (r'Context.*leak', 0.5),
                    (r'IPC.*failed', 0.7)
                ],
                'correlation_weight': 0.75,
                'temporal_window_minutes': 5,
                'severity': PatternSeverity.HIGH
            },
            
            'network_connectivity_storm': {
                'primary_indicators': [
                    (r'Network.*unreachable', 0.8),
                    (r'Connection.*timed out', 0.7),
                    (r'SSL.*handshake.*failed', 0.8),
                    (r'DNS.*resolution.*failed', 0.7)
                ],
                'secondary_indicators': [
                    (r'Socket.*exception', 0.6),
                    (r'Certificate.*expired', 0.7),
                    (r'Connection.*refused', 0.6),
                    (r'No.*network.*available', 0.8)
                ],
                'correlation_weight': 0.7,
                'temporal_window_minutes': 8,
                'severity': PatternSeverity.MEDIUM
            },
            
            'ui_thread_blocking_cascade': {
                'primary_indicators': [
                    (r'ANR in.*main', 1.0),
                    (r'UI thread.*blocked', 0.9),
                    (r'Choreographer.*skipped.*frames', 0.7),
                    (r'StrictMode.*violation', 0.6)
                ],
                'secondary_indicators': [
                    (r'long running.*operation', 0.7),
                    (r'Main thread.*database', 0.8),
                    (r'NetworkOnMainThreadException', 0.9),
                    (r'blocking.*call.*main.*thread', 0.8)
                ],
                'correlation_weight': 0.8,
                'temporal_window_minutes': 3,
                'severity': PatternSeverity.HIGH
            },
            
            'hardware_failure_pattern': {
                'primary_indicators': [
                    (r'Camera.*service.*died', 0.9),
                    (r'Sensor.*not.*available', 0.8),
                    (r'Hardware.*not.*found', 0.9),
                    (r'Permission denied.*dev', 0.7)
                ],
                'secondary_indicators': [
                    (r'Media.*server.*died', 0.7),
                    (r'Audio.*service.*crash', 0.6),
                    (r'Graphics.*driver.*error', 0.8),
                    (r'Thermal.*shutdown', 0.9)
                ],
                'correlation_weight': 0.6,
                'temporal_window_minutes': 20,
                'severity': PatternSeverity.CRITICAL
            }
        }
        
        # Compile regex patterns for performance
        self.compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        for pattern_id, config in self.pattern_definitions.items():
            self.compiled_patterns[pattern_id] = {
                'primary': [(re.compile(pattern, re.IGNORECASE), weight) 
                           for pattern, weight in config['primary_indicators']],
                'secondary': [(re.compile(pattern, re.IGNORECASE), weight) 
                             for pattern, weight in config['secondary_indicators']],
                'config': config
            }
    
    def analyze_crash_patterns(self, crashes: List[Dict]) -> List[EnhancedPattern]:
        """
        Analyze crashes and detect enhanced patterns using statistical methods
        """
        if not crashes:
            return []
        
        detected_patterns = []
        
        # Process each pattern definition
        for pattern_id, compiled_config in self.compiled_patterns.items():
            pattern = self._detect_enhanced_pattern(pattern_id, compiled_config, crashes)
            if pattern and pattern.confidence_score >= self.confidence_threshold:
                detected_patterns.append(pattern)
        
        # Detect burst patterns (high frequency in short time)
        burst_patterns = self._detect_burst_patterns(crashes)
        detected_patterns.extend(burst_patterns)
        
        # Detect cascade patterns (multiple pattern types occurring together)
        cascade_patterns = self._detect_cascade_patterns(detected_patterns, crashes)
        detected_patterns.extend(cascade_patterns)
        
        # Sort by severity and confidence
        detected_patterns.sort(
            key=lambda p: (p.severity.value, p.confidence_score), 
            reverse=True
        )
        
        return detected_patterns
    
    def _detect_enhanced_pattern(self, pattern_id: str, compiled_config: Dict, 
                                crashes: List[Dict]) -> Optional[EnhancedPattern]:
        """Detect a specific pattern using enhanced statistical analysis"""
        
        primary_matches = []
        secondary_matches = []
        primary_scores = []
        secondary_scores = []
        
        # Find crashes matching primary and secondary indicators
        for crash in crashes:
            crash_text = self._extract_crash_text(crash)
            
            # Check primary indicators with weighted scoring
            primary_score = 0
            for regex, weight in compiled_config['primary']:
                if regex.search(crash_text):
                    primary_matches.append(crash)
                    primary_score = max(primary_score, weight)
            
            if primary_score > 0:
                primary_scores.append(primary_score)
            
            # Check secondary indicators
            secondary_score = 0
            for regex, weight in compiled_config['secondary']:
                if regex.search(crash_text):
                    secondary_matches.append(crash)
                    secondary_score = max(secondary_score, weight)
            
            if secondary_score > 0:
                secondary_scores.append(secondary_score)
        
        # Skip if not enough primary matches
        if len(primary_matches) < self.min_pattern_frequency:
            return None
        
        config = compiled_config['config']
        
        # Calculate statistical metrics
        frequency_score = self._calculate_frequency_score(len(primary_matches), len(crashes))
        correlation_score = self._calculate_correlation_score(
            primary_matches, secondary_matches, config['temporal_window_minutes']
        )
        temporal_score = self._calculate_temporal_clustering_score(
            primary_matches, config['temporal_window_minutes']
        )
        
        # Calculate overall confidence using weighted average
        confidence = self._calculate_confidence_score(
            frequency_score, correlation_score, temporal_score, primary_scores, secondary_scores
        )
        
        if confidence < self.confidence_threshold:
            return None
        
        # Generate evidence
        evidence = self._generate_statistical_evidence(
            pattern_id, primary_matches, secondary_matches, 
            frequency_score, correlation_score, temporal_score
        )
        
        # Determine recommendations
        recommendations = self._get_pattern_recommendations(pattern_id, confidence, len(primary_matches))
        
        return EnhancedPattern(
            pattern_id=pattern_id,
            pattern_type=PatternType.CORRELATED,
            name=pattern_id.replace('_', ' ').title(),
            description=f"Statistical detection of {pattern_id} with {confidence:.1%} confidence",
            frequency=len(primary_matches),
            confidence_score=confidence,
            correlation_strength=correlation_score,
            temporal_clustering_score=temporal_score,
            severity=config['severity'],
            evidence=evidence,
            affected_crashes=primary_matches,
            recommended_actions=recommendations,
            urgency_level=self._calculate_urgency(config['severity'], confidence, len(primary_matches))
        )
    
    def _detect_burst_patterns(self, crashes: List[Dict]) -> List[EnhancedPattern]:
        """Detect burst patterns - high frequency crashes in short time windows"""
        if len(crashes) < 10:
            return []
        
        burst_patterns = []
        
        # Group crashes by time windows (1-minute windows)
        time_windows = defaultdict(list)
        
        for crash in crashes:
            timestamp = self._parse_timestamp(crash.get('timestamp', ''))
            if timestamp:
                # Create 1-minute time buckets
                time_key = timestamp.replace(second=0, microsecond=0)
                time_windows[time_key].append(crash)
        
        # Find burst windows (>= 5 crashes per minute)
        burst_threshold = 5
        burst_windows = []
        
        for time_key, window_crashes in time_windows.items():
            if len(window_crashes) >= burst_threshold:
                burst_windows.append((time_key, window_crashes))
        
        if burst_windows:
            # Calculate burst pattern statistics
            total_burst_crashes = sum(len(crashes) for _, crashes in burst_windows)
            max_burst_size = max(len(crashes) for _, crashes in burst_windows)
            
            severity = PatternSeverity.CRITICAL if max_burst_size >= 20 else PatternSeverity.HIGH
            confidence = min(0.9, (total_burst_crashes / len(crashes)) * 2)
            
            burst_pattern = EnhancedPattern(
                pattern_id='burst_pattern',
                pattern_type=PatternType.BURST,
                name='Crash Burst Pattern',
                description=f'High-frequency crash bursts detected: {len(burst_windows)} burst windows',
                frequency=total_burst_crashes,
                confidence_score=confidence,
                correlation_strength=0.8,
                temporal_clustering_score=0.9,
                severity=severity,
                evidence=[
                    f"Detected {len(burst_windows)} burst windows",
                    f"Maximum {max_burst_size} crashes in 1 minute",
                    f"Total {total_burst_crashes} crashes in burst windows",
                    f"Burst periods: {', '.join([str(t) for t, _ in burst_windows[:3]])}"
                ],
                recommended_actions=[
                    "Immediately restart device to break crash spiral",
                    "Check system resources and clear memory/storage",
                    "Monitor device temperature and check for thermal issues",
                    "Consider factory reset if bursts continue"
                ],
                urgency_level=9 if severity == PatternSeverity.CRITICAL else 7
            )
            
            burst_patterns.append(burst_pattern)
        
        return burst_patterns
    
    def _detect_cascade_patterns(self, detected_patterns: List[EnhancedPattern], 
                                crashes: List[Dict]) -> List[EnhancedPattern]:
        """Detect cascade patterns where multiple pattern types occur together"""
        if len(detected_patterns) < 2:
            return []
        
        cascade_patterns = []
        
        # Look for overlapping time windows between different patterns
        for i, pattern1 in enumerate(detected_patterns):
            for pattern2 in detected_patterns[i+1:]:
                if pattern1.pattern_id == pattern2.pattern_id:
                    continue
                
                # Calculate temporal overlap
                overlap_score = self._calculate_pattern_overlap(pattern1, pattern2)
                
                if overlap_score >= 0.5:  # 50% overlap threshold
                    cascade_confidence = (pattern1.confidence_score + pattern2.confidence_score) / 2
                    cascade_severity = max(pattern1.severity, pattern2.severity)
                    
                    cascade_pattern = EnhancedPattern(
                        pattern_id=f'cascade_{pattern1.pattern_id}_{pattern2.pattern_id}',
                        pattern_type=PatternType.CASCADE,
                        name=f'Cascade: {pattern1.name} + {pattern2.name}',
                        description=f'Cascade failure involving {pattern1.name} and {pattern2.name}',
                        frequency=pattern1.frequency + pattern2.frequency,
                        confidence_score=cascade_confidence,
                        correlation_strength=overlap_score,
                        temporal_clustering_score=max(pattern1.temporal_clustering_score, 
                                                    pattern2.temporal_clustering_score),
                        severity=cascade_severity,
                        evidence=[
                            f"Pattern overlap: {overlap_score:.1%}",
                            f"Combined frequency: {pattern1.frequency + pattern2.frequency} crashes",
                            f"Primary patterns: {pattern1.name}, {pattern2.name}"
                        ],
                        recommended_actions=[
                            "URGENT: Address cascade failure immediately",
                            "Restart device and clear all system caches",
                            "Check for hardware issues if multiple patterns persist",
                            "Consider professional device diagnosis"
                        ],
                        urgency_level=10
                    )
                    
                    cascade_patterns.append(cascade_pattern)
                    break  # Only create one cascade per pattern
        
        return cascade_patterns
    
    def _extract_crash_text(self, crash: Dict) -> str:
        """Extract searchable text from crash data"""
        text_parts = [
            crash.get('title', ''),
            crash.get('description', ''),
            crash.get('app_name', ''),
            crash.get('package_name', ''),
            crash.get('stack_trace', ''),
            ' '.join([log.get('message', '') for log in crash.get('related_logs', [])])
        ]
        return ' '.join(text_parts).lower()
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None
        
        # Try different timestamp formats (prefer formats with year)
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
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
    
    def _calculate_frequency_score(self, pattern_matches: int, total_crashes: int) -> float:
        """Calculate frequency-based score (0.0-1.0)"""
        if total_crashes == 0:
            return 0.0
        
        frequency_ratio = pattern_matches / total_crashes
        # Use logarithmic scaling to prevent over-weighting high frequencies
        return min(1.0, math.log(1 + frequency_ratio * 10) / math.log(11))
    
    def _calculate_correlation_score(self, primary_matches: List[Dict], 
                                   secondary_matches: List[Dict], 
                                   time_window_minutes: int) -> float:
        """Calculate correlation score between primary and secondary indicators"""
        if not primary_matches or not secondary_matches:
            return 0.0
        
        # Simple correlation based on temporal proximity
        correlation_count = 0
        time_window = timedelta(minutes=time_window_minutes)
        
        for primary_crash in primary_matches:
            primary_time = self._parse_timestamp(primary_crash.get('timestamp', ''))
            if not primary_time:
                continue
            
            for secondary_crash in secondary_matches:
                secondary_time = self._parse_timestamp(secondary_crash.get('timestamp', ''))
                if not secondary_time:
                    continue
                
                if abs(primary_time - secondary_time) <= time_window:
                    correlation_count += 1
                    break
        
        return min(1.0, correlation_count / len(primary_matches))
    
    def _calculate_temporal_clustering_score(self, matches: List[Dict], 
                                           window_minutes: int) -> float:
        """Calculate how clustered the crashes are in time"""
        if len(matches) < 2:
            return 0.0
        
        timestamps = []
        for crash in matches:
            ts = self._parse_timestamp(crash.get('timestamp', ''))
            if ts:
                timestamps.append(ts)
        
        if len(timestamps) < 2:
            return 0.0
        
        timestamps.sort()
        
        # Calculate clustering using coefficient of variation of time intervals
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return 0.0
        
        mean_interval = statistics.mean(intervals)
        if mean_interval == 0:
            return 1.0
        
        stdev_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
        coefficient_of_variation = stdev_interval / mean_interval if mean_interval > 0 else 0
        
        # Lower CV = more clustered = higher score
        clustering_score = max(0.0, 1.0 - (coefficient_of_variation / 2.0))
        return min(1.0, clustering_score)
    
    def _calculate_confidence_score(self, frequency_score: float, correlation_score: float,
                                   temporal_score: float, primary_scores: List[float],
                                   secondary_scores: List[float]) -> float:
        """Calculate overall confidence using weighted metrics"""
        
        # Base score from statistical metrics
        base_score = (frequency_score * 0.3 + 
                     correlation_score * 0.3 + 
                     temporal_score * 0.2)
        
        # Quality score from pattern matching strength
        avg_primary_score = statistics.mean(primary_scores) if primary_scores else 0
        avg_secondary_score = statistics.mean(secondary_scores) if secondary_scores else 0
        quality_score = (avg_primary_score * 0.15 + avg_secondary_score * 0.05)
        
        return min(1.0, base_score + quality_score)
    
    def _generate_statistical_evidence(self, pattern_id: str, primary_matches: List[Dict],
                                     secondary_matches: List[Dict], frequency_score: float,
                                     correlation_score: float, temporal_score: float) -> List[str]:
        """Generate evidence list with statistical details"""
        evidence = [
            f"Pattern frequency: {len(primary_matches)} occurrences",
            f"Frequency score: {frequency_score:.2f}",
            f"Correlation strength: {correlation_score:.2f}",
            f"Temporal clustering: {temporal_score:.2f}"
        ]
        
        if secondary_matches:
            evidence.append(f"Supporting evidence: {len(secondary_matches)} related crashes")
        
        # Add specific examples
        if primary_matches:
            example_apps = list(set(crash.get('app_name', 'Unknown') for crash in primary_matches[:3]))
            evidence.append(f"Affected apps: {', '.join(example_apps)}")
        
        return evidence
    
    def _calculate_pattern_overlap(self, pattern1: EnhancedPattern, 
                                  pattern2: EnhancedPattern) -> float:
        """Calculate temporal overlap between two patterns"""
        # Simple overlap calculation based on affected crashes timing
        timestamps1 = set()
        timestamps2 = set()
        
        for crash in pattern1.affected_crashes:
            ts = self._parse_timestamp(crash.get('timestamp', ''))
            if ts:
                # Round to minute for overlap calculation
                timestamps1.add(ts.replace(second=0, microsecond=0))
        
        for crash in pattern2.affected_crashes:
            ts = self._parse_timestamp(crash.get('timestamp', ''))
            if ts:
                timestamps2.add(ts.replace(second=0, microsecond=0))
        
        if not timestamps1 or not timestamps2:
            return 0.0
        
        overlap = len(timestamps1.intersection(timestamps2))
        union = len(timestamps1.union(timestamps2))
        
        return overlap / union if union > 0 else 0.0
    
    def _get_pattern_recommendations(self, pattern_id: str, confidence: float, 
                                   frequency: int) -> List[str]:
        """Get specific recommendations for each pattern type"""
        
        recommendations = {
            'memory_exhaustion_cascade': [
                "Close unused applications immediately",
                "Clear app caches and temporary files", 
                "Restart device to free memory",
                "Check for memory-hungry apps in Settings > Battery"
            ],
            'database_corruption_spiral': [
                "Back up important data immediately",
                "Clear app data for affected applications",
                "Run disk cleanup and check storage space",
                "Consider factory reset if corruption persists"
            ],
            'service_binding_failure_chain': [
                "Restart device to reset service bindings",
                "Clear system cache partition",
                "Update affected apps from Play Store",
                "Check for system software updates"
            ],
            'network_connectivity_storm': [
                "Reset network settings",
                "Toggle Wi-Fi and mobile data off/on",
                "Clear DNS cache and network configurations",
                "Check with network provider for service issues"
            ],
            'ui_thread_blocking_cascade': [
                "Force close problematic apps",
                "Clear app caches for affected apps",
                "Avoid network operations on main thread",
                "Update apps that show ANR patterns"
            ],
            'hardware_failure_pattern': [
                "Restart device immediately",
                "Check device temperature and cooling",
                "Test hardware features individually",
                "Contact manufacturer if issues persist"
            ]
        }
        
        base_recommendations = recommendations.get(pattern_id, [
            "Monitor crash patterns closely",
            "Restart device to clear temporary issues",
            "Update all applications",
            "Consider professional diagnosis if issues persist"
        ])
        
        # Add urgency-based recommendations
        if confidence > 0.8 and frequency > 10:
            base_recommendations.insert(0, "URGENT: Address this issue immediately")
        elif confidence > 0.6 and frequency > 5:
            base_recommendations.insert(0, "HIGH PRIORITY: Address this issue soon")
        
        return base_recommendations
    
    def _calculate_urgency(self, severity: PatternSeverity, confidence: float, 
                          frequency: int) -> int:
        """Calculate urgency level (1-10 scale)"""
        base_urgency = severity.value * 2  # 2, 4, 6, 8
        confidence_boost = int(confidence * 3)  # 0-3
        frequency_boost = min(2, frequency // 5)  # 0-2
        
        return min(10, base_urgency + confidence_boost + frequency_boost)