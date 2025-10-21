#!/usr/bin/env python3
"""
Enhanced Crash Analyzer Integration

Combines the enhanced statistical pattern detection with existing analysis systems
to provide comprehensive crash analysis with improved accuracy and insights.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path
from datetime import datetime

from .enhanced_pattern_detector import StatisticalPatternDetector, EnhancedPattern, PatternSeverity, PatternType
from .crash_analyzer import CrashAnalyzer, CrashPattern, SystemHealthStatus
from ..plain_language import PlainLanguageExplainer, PlainExplanation

@dataclass
class EnhancedAnalysisResult:
    """Comprehensive analysis result combining enhanced and traditional methods"""
    
    # Enhanced statistical patterns
    enhanced_patterns: List[EnhancedPattern]
    
    # Traditional simple patterns (for backward compatibility)
    simple_patterns: Dict[str, CrashPattern]
    
    # Overall assessment
    system_health: SystemHealthStatus
    
    # Confidence metrics
    overall_confidence: float
    analysis_quality_score: float
    
    # Plain language summary
    user_friendly_summary: str
    detailed_recommendations: List[str]
    
    # Metadata
    analysis_timestamp: datetime
    total_crashes_analyzed: int
    analysis_duration_seconds: float

class EnhancedCrashAnalyzer:
    """
    Comprehensive crash analyzer that combines enhanced statistical detection
    with traditional pattern matching for maximum accuracy and insight.
    """
    
    def __init__(self, log_directory: Path, 
                 confidence_threshold: float = 0.6,
                 min_pattern_frequency: int = 3):
        
        self.log_directory = Path(log_directory)
        self.confidence_threshold = confidence_threshold
        
        # Initialize analyzers
        self.enhanced_detector = StatisticalPatternDetector(
            min_pattern_frequency=min_pattern_frequency,
            confidence_threshold=confidence_threshold
        )
        
        self.simple_analyzer = CrashAnalyzer(log_directory)
        self.plain_explainer = PlainLanguageExplainer()
        
        # Analysis cache
        self._cached_results = None
        self._cache_timestamp = None
    
    def analyze_comprehensive(self, force_refresh: bool = False) -> EnhancedAnalysisResult:
        """
        Perform comprehensive analysis using both enhanced and traditional methods
        """
        start_time = datetime.now()
        
        # Check cache
        if not force_refresh and self._cached_results and self._cache_timestamp:
            cache_age = (datetime.now() - self._cache_timestamp).total_seconds()
            if cache_age < 300:  # 5-minute cache
                return self._cached_results
        
        # Load crash data
        crash_count = self.simple_analyzer.load_crashes()
        if crash_count == 0:
            return self._create_empty_result(start_time)
        
        crashes = self.simple_analyzer.crashes
        
        # Run enhanced statistical analysis
        enhanced_patterns = self.enhanced_detector.analyze_crash_patterns(crashes)
        
        # Run traditional analysis for comparison
        simple_patterns = self.simple_analyzer.analyze_crash_patterns()
        
        # Assess overall system health
        system_health = self._assess_system_health(enhanced_patterns, simple_patterns, crashes)
        
        # Calculate confidence metrics
        overall_confidence, quality_score = self._calculate_analysis_confidence(
            enhanced_patterns, simple_patterns, crashes
        )
        
        # Generate user-friendly summary and recommendations
        summary, recommendations = self._generate_comprehensive_summary(
            enhanced_patterns, simple_patterns, system_health
        )
        
        # Create comprehensive result
        analysis_duration = (datetime.now() - start_time).total_seconds()
        
        result = EnhancedAnalysisResult(
            enhanced_patterns=enhanced_patterns,
            simple_patterns=simple_patterns,
            system_health=system_health,
            overall_confidence=overall_confidence,
            analysis_quality_score=quality_score,
            user_friendly_summary=summary,
            detailed_recommendations=recommendations,
            analysis_timestamp=datetime.now(),
            total_crashes_analyzed=crash_count,
            analysis_duration_seconds=analysis_duration
        )
        
        # Cache result
        self._cached_results = result
        self._cache_timestamp = datetime.now()
        
        return result
    
    def get_priority_issues(self, max_issues: int = 5) -> List[EnhancedPattern]:
        """Get the most critical issues that need immediate attention"""
        result = self.analyze_comprehensive()
        
        # Sort by urgency and confidence
        priority_patterns = sorted(
            result.enhanced_patterns,
            key=lambda p: (p.urgency_level, p.confidence_score, p.severity.value),
            reverse=True
        )
        
        return priority_patterns[:max_issues]
    
    def get_plain_language_report(self) -> str:
        """Generate a comprehensive plain-language report for end users"""
        result = self.analyze_comprehensive()
        
        # Start with health summary
        report_parts = [
            "# 📱 Your Device Analysis Report\n",
            f"**Analysis completed:** {result.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Crashes analyzed:** {result.total_crashes_analyzed}",
            f"**Analysis confidence:** {result.overall_confidence:.1%}\n"
        ]
        
        # Add system health assessment
        health_emoji = {
            "STABLE": "🟢",
            "DEGRADED": "🟡", 
            "UNSTABLE": "🟠",
            "CRITICAL": "🔴"
        }.get(result.system_health.status, "⚪")
        
        report_parts.extend([
            f"## {health_emoji} Device Health: {result.system_health.status}",
            f"**Confidence:** {result.system_health.confidence:.1%}",
            f"**Summary:** {result.system_health.summary}\n"
        ])
        
        # Add enhanced patterns found
        if result.enhanced_patterns:
            report_parts.append("## 🔍 Issues Detected (Enhanced Analysis)\n")
            
            for i, pattern in enumerate(result.enhanced_patterns[:5], 1):
                severity_emoji = {
                    PatternSeverity.LOW: "🟢",
                    PatternSeverity.MEDIUM: "🟡",
                    PatternSeverity.HIGH: "🟠", 
                    PatternSeverity.CRITICAL: "🔴"
                }.get(pattern.severity, "⚪")
                
                report_parts.extend([
                    f"### {i}. {severity_emoji} {pattern.name}",
                    f"**Confidence:** {pattern.confidence_score:.1%} | **Urgency:** {pattern.urgency_level}/10",
                    f"**Description:** {pattern.description}",
                    f"**Frequency:** {pattern.frequency} occurrences\n",
                    "**Evidence:**"
                ])
                
                for evidence in pattern.evidence:
                    report_parts.append(f"• {evidence}")
                
                report_parts.extend([
                    "\n**Recommended Actions:**"
                ])
                
                for action in pattern.recommended_actions:
                    report_parts.append(f"• {action}")
                
                report_parts.append("")
        
        # Add comprehensive recommendations
        if result.detailed_recommendations:
            report_parts.extend([
                "## 💡 Priority Action Plan\n"
            ])
            
            for i, recommendation in enumerate(result.detailed_recommendations, 1):
                report_parts.append(f"{i}. {recommendation}")
        
        # Add technical summary if simple patterns were found
        if result.simple_patterns:
            report_parts.extend([
                "\n## 🔧 Technical Details (Traditional Analysis)",
                f"Found {len(result.simple_patterns)} traditional patterns for verification:\n"
            ])
            
            for pattern_name, pattern in result.simple_patterns.items():
                report_parts.extend([
                    f"• **{pattern_name.replace('_', ' ').title()}:** {pattern.count} occurrences",
                    f"  Risk: {pattern.risk_level} | {pattern.description}"
                ])
        
        # Footer
        report_parts.extend([
            "\n---",
            "**Need Help?**",
            "• This analysis combines advanced statistical detection with traditional methods",
            "• Higher confidence scores indicate more reliable diagnoses", 
            "• Focus on issues with urgency level 7+ first",
            "• Contact support if critical issues persist after following recommendations\n"
        ])
        
        return "\n".join(report_parts)
    
    def export_analysis_json(self, output_path: Path) -> bool:
        """Export comprehensive analysis to JSON format"""
        try:
            result = self.analyze_comprehensive()
            
            # Convert to serializable format
            export_data = {
                "analysis_metadata": {
                    "timestamp": result.analysis_timestamp.isoformat(),
                    "crashes_analyzed": result.total_crashes_analyzed,
                    "analysis_duration_seconds": result.analysis_duration_seconds,
                    "overall_confidence": result.overall_confidence,
                    "quality_score": result.analysis_quality_score
                },
                "system_health": {
                    "status": result.system_health.status,
                    "confidence": result.system_health.confidence,
                    "cascade_risk": result.system_health.cascade_risk,
                    "reboot_risk": result.system_health.reboot_risk,
                    "summary": result.system_health.summary
                },
                "enhanced_patterns": [
                    {
                        "pattern_id": p.pattern_id,
                        "name": p.name,
                        "type": p.pattern_type.value,
                        "description": p.description,
                        "frequency": p.frequency,
                        "confidence_score": p.confidence_score,
                        "correlation_strength": p.correlation_strength,
                        "temporal_clustering_score": p.temporal_clustering_score,
                        "severity": p.severity.name,
                        "urgency_level": p.urgency_level,
                        "evidence": p.evidence,
                        "recommended_actions": p.recommended_actions
                    }
                    for p in result.enhanced_patterns
                ],
                "simple_patterns": {
                    name: {
                        "count": pattern.count,
                        "severity": pattern.severity,
                        "risk_level": pattern.risk_level,
                        "description": pattern.description,
                        "recommendation": pattern.recommendation
                    }
                    for name, pattern in result.simple_patterns.items()
                },
                "summary": result.user_friendly_summary,
                "recommendations": result.detailed_recommendations
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting analysis: {e}")
            return False
    
    def _create_empty_result(self, start_time: datetime) -> EnhancedAnalysisResult:
        """Create result for when no crashes are found"""
        return EnhancedAnalysisResult(
            enhanced_patterns=[],
            simple_patterns={},
            system_health=SystemHealthStatus(
                status="STABLE",
                confidence=1.0,
                primary_issues=[],
                cascade_risk=False,
                reboot_risk=False,
                summary="No crashes detected - device appears healthy"
            ),
            overall_confidence=1.0,
            analysis_quality_score=1.0,
            user_friendly_summary="🟢 Great news! No crashes or issues detected. Your device is running smoothly.",
            detailed_recommendations=["Keep your device updated", "Regularly restart your device", "Monitor storage space"],
            analysis_timestamp=datetime.now(),
            total_crashes_analyzed=0,
            analysis_duration_seconds=(datetime.now() - start_time).total_seconds()
        )
    
    def _assess_system_health(self, enhanced_patterns: List[EnhancedPattern], 
                            simple_patterns: Dict[str, CrashPattern], 
                            crashes: List[Dict]) -> SystemHealthStatus:
        """Assess overall system health based on all analysis results"""
        
        # Count critical issues
        critical_enhanced = sum(1 for p in enhanced_patterns if p.severity == PatternSeverity.CRITICAL)
        high_enhanced = sum(1 for p in enhanced_patterns if p.severity == PatternSeverity.HIGH)
        
        critical_simple = sum(1 for p in simple_patterns.values() if p.risk_level == "CRITICAL")
        high_simple = sum(1 for p in simple_patterns.values() if p.risk_level == "HIGH")
        
        # Assess cascade risk
        cascade_patterns = [p for p in enhanced_patterns if p.pattern_type == PatternType.CASCADE]
        burst_patterns = [p for p in enhanced_patterns if p.pattern_type == PatternType.BURST]
        
        cascade_risk = len(cascade_patterns) > 0 or len(burst_patterns) > 0
        
        # Assess reboot risk  
        memory_patterns = [p for p in enhanced_patterns if 'memory' in p.pattern_id.lower()]
        hardware_patterns = [p for p in enhanced_patterns if 'hardware' in p.pattern_id.lower()]
        
        reboot_risk = (len(memory_patterns) > 0 and 
                      any(p.severity == PatternSeverity.CRITICAL for p in memory_patterns)) or \
                     (len(hardware_patterns) > 0)
        
        # Determine overall status
        total_critical = critical_enhanced + critical_simple
        total_high = high_enhanced + high_simple
        
        if total_critical >= 2 or cascade_risk:
            status = "CRITICAL"
            confidence = 0.9
            summary = f"Critical system issues detected. {total_critical} critical patterns found."
        elif total_critical >= 1 or total_high >= 3:
            status = "UNSTABLE" 
            confidence = 0.8
            summary = f"System instability detected. {total_critical + total_high} high-severity patterns found."
        elif total_high >= 1 or len(enhanced_patterns) >= 3:
            status = "DEGRADED"
            confidence = 0.7
            summary = f"System performance degraded. {len(enhanced_patterns)} patterns detected."
        else:
            status = "STABLE"
            confidence = 0.85
            summary = "System appears stable with minor or no issues detected."
        
        # Convert patterns for health status
        primary_issues = []
        for pattern in enhanced_patterns[:3]:  # Top 3 issues
            primary_issues.append(CrashPattern(
                pattern_type=pattern.pattern_id,
                severity=pattern.urgency_level,
                count=pattern.frequency,
                description=pattern.description,
                evidence=pattern.evidence,
                recommendation=pattern.recommended_actions[0] if pattern.recommended_actions else "Monitor closely",
                risk_level=pattern.severity.name
            ))
        
        return SystemHealthStatus(
            status=status,
            confidence=confidence,
            primary_issues=primary_issues,
            cascade_risk=cascade_risk,
            reboot_risk=reboot_risk,
            summary=summary
        )
    
    def _calculate_analysis_confidence(self, enhanced_patterns: List[EnhancedPattern],
                                     simple_patterns: Dict[str, CrashPattern],
                                     crashes: List[Dict]) -> Tuple[float, float]:
        """Calculate overall confidence in the analysis"""
        
        if not enhanced_patterns and not simple_patterns:
            return 0.95, 0.9  # High confidence in "no issues" finding
        
        # Enhanced pattern confidence (weighted by pattern strength)
        if enhanced_patterns:
            enhanced_confidence = sum(p.confidence_score * p.frequency for p in enhanced_patterns) / \
                                sum(p.frequency for p in enhanced_patterns)
        else:
            enhanced_confidence = 0.0
        
        # Simple pattern confidence (based on frequency)
        if simple_patterns:
            simple_confidence = min(0.8, len(simple_patterns) / 10)  # Cap at 0.8
        else:
            simple_confidence = 0.0
        
        # Overall confidence (favor enhanced patterns)
        overall_confidence = enhanced_confidence * 0.7 + simple_confidence * 0.3
        
        # Quality score based on data completeness
        crashes_with_timestamps = sum(1 for c in crashes if c.get('timestamp'))
        data_completeness = crashes_with_timestamps / len(crashes) if crashes else 1.0
        
        pattern_coverage = len(enhanced_patterns) / max(1, len(crashes) // 10)  # Expect ~1 pattern per 10 crashes
        pattern_coverage = min(1.0, pattern_coverage)
        
        quality_score = (data_completeness * 0.6 + pattern_coverage * 0.4)
        
        return overall_confidence, quality_score
    
    def _generate_comprehensive_summary(self, enhanced_patterns: List[EnhancedPattern],
                                      simple_patterns: Dict[str, CrashPattern],
                                      system_health: SystemHealthStatus) -> Tuple[str, List[str]]:
        """Generate user-friendly summary and recommendations"""
        
        if not enhanced_patterns and not simple_patterns:
            return (
                "🟢 Your device is running smoothly with no significant issues detected.",
                [
                    "Continue regular device maintenance",
                    "Keep apps and system updated", 
                    "Restart device weekly for optimal performance"
                ]
            )
        
        # Generate summary based on most critical patterns
        critical_patterns = [p for p in enhanced_patterns if p.severity == PatternSeverity.CRITICAL]
        high_patterns = [p for p in enhanced_patterns if p.severity == PatternSeverity.HIGH]
        
        if critical_patterns:
            summary = f"🔴 Critical issues detected! {len(critical_patterns)} critical patterns need immediate attention."
        elif high_patterns:
            summary = f"🟠 High priority issues found. {len(high_patterns)} patterns require attention soon."
        elif enhanced_patterns:
            summary = f"🟡 {len(enhanced_patterns)} patterns detected. Monitor and address when convenient."
        else:
            summary = f"🟢 Traditional analysis found {len(simple_patterns)} minor patterns to monitor."
        
        # Generate prioritized recommendations
        recommendations = []
        
        # Add urgent recommendations first
        urgent_patterns = [p for p in enhanced_patterns if p.urgency_level >= 8]
        for pattern in urgent_patterns[:3]:  # Top 3 urgent
            if pattern.recommended_actions:
                recommendations.append(f"URGENT - {pattern.name}: {pattern.recommended_actions[0]}")
        
        # Add high priority recommendations
        high_priority_patterns = [p for p in enhanced_patterns if 5 <= p.urgency_level < 8]
        for pattern in high_priority_patterns[:2]:  # Top 2 high priority
            if pattern.recommended_actions:
                recommendations.append(f"High Priority - {pattern.name}: {pattern.recommended_actions[0]}")
        
        # Add system health recommendations
        if system_health.cascade_risk:
            recommendations.append("System Risk: Restart device immediately to prevent cascade failures")
        if system_health.reboot_risk:
            recommendations.append("Hardware Risk: Monitor device temperature and check for hardware issues")
        
        # Add general maintenance if no specific recommendations
        if not recommendations:
            recommendations.extend([
                "Restart device to clear temporary issues",
                "Update all applications from app store", 
                "Clear storage space if device is full"
            ])
        
        return summary, recommendations[:5]  # Limit to top 5 recommendations