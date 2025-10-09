#!/usr/bin/env python3
"""
Crash Analyzer - Comprehensive crash pattern analysis

Based on real-world diagnostic experience from Pixel 6 reboot case study.
Identifies critical patterns like database corruption, cascade failures, 
hardware issues, and system instability indicators.
"""

import json
import glob
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CrashPattern:
    """Represents a detected crash pattern with severity and context."""
    pattern_type: str
    severity: int  # 1-10 scale
    count: int
    description: str
    evidence: List[str]
    recommendation: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class SystemHealthStatus:
    """Overall system health assessment."""
    status: str  # STABLE, DEGRADED, UNSTABLE, CRITICAL
    confidence: float  # 0.0-1.0
    primary_issues: List[CrashPattern]
    cascade_risk: bool
    reboot_risk: bool
    summary: str


class CrashAnalyzer:
    """
    Comprehensive crash analyzer that identifies critical patterns
    and system health issues based on crash log analysis.
    """
    
    # Critical patterns based on Pixel 6 case study
    CRITICAL_PATTERNS = {
        'database_connection_pool': {
            'keywords': ['connection pool', 'Cannot perform this operation because the connection pool has been closed'],
            'severity': 9,
            'risk': 'CRITICAL',
            'description': 'Database connection pool failures - can cause system cascade failures'
        },
        'sqlite_corruption': {
            'keywords': ['sqlite', 'database', 'metadata.db', 'connection pool.*closed.*connections in use'],
            'severity': 8,
            'risk': 'CRITICAL', 
            'description': 'SQLite database corruption - indicates data integrity issues'
        },
        'workmanager_boot_failure': {
            'keywords': ['Cannot initialize WorkManager in direct boot mode'],
            'severity': 9,
            'risk': 'CRITICAL',
            'description': 'WorkManager boot failures - indicates device restart/recovery'
        },
        'google_play_services_failure': {
            'keywords': ['GoogleApiManager', 'com.google.android.gms'],
            'severity': 7,
            'risk': 'HIGH',
            'description': 'Google Play Services instability - can affect core Android functionality'
        },
        'font_system_failure': {
            'keywords': ['FontLog', 'font.*cache', 'Google Sans'],
            'severity': 6,
            'risk': 'MEDIUM',
            'description': 'Font system issues - can cascade to UI rendering problems'
        },
        'hardware_access_failure': {
            'keywords': ['Permission denied.*device', 'hardware.*not found', 'modem', '5G'],
            'severity': 8,
            'risk': 'HIGH',
            'description': 'Hardware access failures - may indicate hardware damage'
        },
        'cascade_failure_pattern': {
            'keywords': [],  # Detected by count analysis
            'severity': 10,
            'risk': 'CRITICAL',
            'description': 'Cascade failure detected - multiple system failures in short time'
        }
    }
    
    def __init__(self, log_directory: Path):
        """Initialize analyzer with log directory."""
        self.log_directory = Path(log_directory)
        self.crashes = []
        self.analysis_results = {}
        
    def load_crashes(self) -> int:
        """Load all crash files from the log directory."""
        crash_files = glob.glob(str(self.log_directory / "crash_*.json"))
        crash_files.sort()
        
        self.crashes = []
        for file_path in crash_files:
            try:
                with open(file_path, 'r') as f:
                    crash = json.load(f)
                    crash['_file_path'] = file_path
                    self.crashes.append(crash)
            except Exception as e:
                logger.warning(f"Failed to load crash file {file_path}: {e}")
                
        logger.info(f"Loaded {len(self.crashes)} crash files")
        return len(self.crashes)
        
    def analyze_crash_patterns(self) -> Dict[str, CrashPattern]:
        """Analyze crashes for critical patterns."""
        patterns = {}
        
        for pattern_name, config in self.CRITICAL_PATTERNS.items():
            if pattern_name == 'cascade_failure_pattern':
                continue  # Handle separately
                
            matches = []
            for crash in self.crashes:
                if self._matches_pattern(crash, config['keywords']):
                    matches.append(crash)
                    
            if matches:
                patterns[pattern_name] = CrashPattern(
                    pattern_type=pattern_name,
                    severity=config['severity'],
                    count=len(matches),
                    description=config['description'],
                    evidence=[f"Found in {len(matches)} crashes" + 
                             (f" (e.g., {matches[0].get('app_name', 'Unknown')})" if matches else "")],
                    recommendation=self._get_recommendation(pattern_name),
                    risk_level=config['risk']
                )
                
        # Check for cascade failures
        cascade_pattern = self._detect_cascade_failures()
        if cascade_pattern:
            patterns['cascade_failure'] = cascade_pattern
            
        return patterns
        
    def _matches_pattern(self, crash: dict, keywords: List[str]) -> bool:
        """Check if crash matches pattern keywords."""
        search_text = " ".join([
            crash.get('description', ''),
            crash.get('title', ''),
            crash.get('app_name', ''),
            " ".join([log.get('message', '') for log in crash.get('related_logs', [])])
        ]).lower()
        
        return any(keyword.lower() in search_text for keyword in keywords)
        
    def _detect_cascade_failures(self) -> Optional[CrashPattern]:
        """Detect cascade failure patterns (many crashes in short time)."""
        if len(self.crashes) < 50:  # Not enough crashes to indicate cascade
            return None
            
        # Group crashes by time windows (5-minute windows)
        time_windows = defaultdict(list)
        
        for crash in self.crashes:
            try:
                # Parse timestamp (format: "MM-DD HH:MM:SS.mmm")
                timestamp_str = crash.get('timestamp', '')
                if not timestamp_str:
                    continue
                    
                # For now, use simplified time window grouping
                time_key = timestamp_str[:10]  # Group by MM-DD HH:MM
                time_windows[time_key].append(crash)
            except Exception:
                continue
                
        # Look for windows with high crash counts
        max_crashes_in_window = max([len(crashes) for crashes in time_windows.values()] + [0])
        
        if max_crashes_in_window >= 20:  # 20+ crashes in 5 minutes = cascade
            return CrashPattern(
                pattern_type='cascade_failure',
                severity=10,
                count=max_crashes_in_window,
                description=f'Cascade failure detected - {max_crashes_in_window} crashes in short time window',
                evidence=[f"Peak: {max_crashes_in_window} crashes in 5-minute window",
                         f"Total time windows with >10 crashes: {sum(1 for crashes in time_windows.values() if len(crashes) > 10)}"],
                recommendation="IMMEDIATE ACTION: Clear system caches, restart services, check for hardware issues",
                risk_level='CRITICAL'
            )
        return None
        
    def _get_recommendation(self, pattern_name: str) -> str:
        """Get specific recommendations for pattern types."""
        recommendations = {
            'database_connection_pool': "Clear Google Play Services data: adb shell pm clear com.google.android.gms",
            'sqlite_corruption': "Clear app caches and restart services to repair database connections",
            'workmanager_boot_failure': "Device restart detected - monitor for hardware issues",
            'google_play_services_failure': "Force stop and clear Google Play Services data",
            'font_system_failure': "Clear font cache: adb shell 'rm -rf /data/system/fonts/cache/*'",
            'hardware_access_failure': "Check for hardware damage or missing components (cellular, sensors)"
        }
        return recommendations.get(pattern_name, "Monitor pattern and investigate root cause")
        
    def analyze_timeline(self) -> Dict[str, any]:
        """Analyze crash timeline for patterns."""
        if not self.crashes:
            return {}
            
        # Group crashes by time periods
        periods = defaultdict(list)
        crash_types_timeline = defaultdict(list)
        
        for crash in self.crashes:
            timestamp = crash.get('timestamp', '')
            if len(timestamp) >= 10:
                period = timestamp[:10]  # MM-DD HH:MM
                periods[period].append(crash)
                crash_types_timeline[period].append(crash.get('crash_type', 'unknown'))
                
        # Find peak crash periods
        peak_period = max(periods.items(), key=lambda x: len(x[1])) if periods else (None, [])
        
        return {
            'total_periods': len(periods),
            'peak_period': {
                'time': peak_period[0],
                'crash_count': len(peak_period[1]),
                'crash_types': Counter(crash_types_timeline.get(peak_period[0], []))
            } if peak_period[0] else None,
            'timeline_summary': {period: len(crashes) for period, crashes in periods.items()}
        }
        
    def analyze_system_components(self) -> Dict[str, int]:
        """Analyze which system components are most affected."""
        app_crashes = Counter()
        system_crashes = Counter()
        
        for crash in self.crashes:
            app_name = crash.get('app_name', 'Unknown')
            crash_type = crash.get('crash_type', 'unknown')
            
            app_crashes[app_name] += 1
            
            # Identify system-critical components
            if any(keyword in app_name.lower() for keyword in 
                   ['libc', 'system', 'google', 'android', 'framework']):
                system_crashes[app_name] += 1
                
        return {
            'most_affected_apps': dict(app_crashes.most_common(10)),
            'system_component_crashes': dict(system_crashes.most_common(5)),
            'total_apps_affected': len(app_crashes)
        }
        
    def assess_system_health(self) -> SystemHealthStatus:
        """Provide overall system health assessment."""
        patterns = self.analyze_crash_patterns()
        timeline = self.analyze_timeline()
        
        # Calculate health score
        health_score = 100
        critical_issues = []
        
        for pattern in patterns.values():
            if pattern.risk_level == 'CRITICAL':
                health_score -= 30
                critical_issues.append(pattern)
            elif pattern.risk_level == 'HIGH':
                health_score -= 15
            elif pattern.risk_level == 'MEDIUM':
                health_score -= 5
                
        # Factor in crash volume
        crash_count = len(self.crashes)
        if crash_count > 100:
            health_score -= 20
        elif crash_count > 50:
            health_score -= 10
            
        # Determine status
        if health_score >= 80:
            status = 'STABLE'
        elif health_score >= 60:
            status = 'DEGRADED'
        elif health_score >= 30:
            status = 'UNSTABLE'
        else:
            status = 'CRITICAL'
            
        # Risk assessments
        cascade_risk = any(p.pattern_type == 'cascade_failure' for p in patterns.values())
        reboot_risk = any(p.pattern_type in ['workmanager_boot_failure', 'database_connection_pool'] 
                         for p in patterns.values())
        
        # Generate summary
        if critical_issues:
            summary = f"CRITICAL: {len(critical_issues)} critical pattern(s) detected. "
            if cascade_risk:
                summary += "Cascade failure risk. "
            if reboot_risk:
                summary += "Device reboot risk. "
            summary += "Immediate action required."
        elif health_score < 80:
            summary = f"System degraded with {crash_count} crashes. Monitor for stability."
        else:
            summary = f"System stable with {crash_count} normal background crashes."
            
        return SystemHealthStatus(
            status=status,
            confidence=min(1.0, len(self.crashes) / 100),  # Higher confidence with more data
            primary_issues=list(patterns.values()),
            cascade_risk=cascade_risk,
            reboot_risk=reboot_risk,
            summary=summary
        )
        
    def generate_analysis_report(self) -> Dict[str, any]:
        """Generate comprehensive analysis report."""
        patterns = self.analyze_crash_patterns()
        timeline = self.analyze_timeline()
        components = self.analyze_system_components()
        health = self.assess_system_health()
        
        return {
            'summary': {
                'total_crashes': len(self.crashes),
                'analysis_timestamp': datetime.now().isoformat(),
                'system_health': {
                    'status': health.status,
                    'confidence': health.confidence,
                    'summary': health.summary
                }
            },
            'critical_patterns': {name: {
                'severity': pattern.severity,
                'count': pattern.count,
                'description': pattern.description,
                'recommendation': pattern.recommendation,
                'risk_level': pattern.risk_level
            } for name, pattern in patterns.items()},
            'timeline_analysis': timeline,
            'component_analysis': components,
            'risk_assessment': {
                'cascade_failure_risk': health.cascade_risk,
                'reboot_risk': health.reboot_risk,
                'immediate_action_needed': health.status in ['CRITICAL', 'UNSTABLE']
            }
        }