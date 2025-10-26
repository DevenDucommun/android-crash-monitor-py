#!/usr/bin/env python3
"""
Predictive Crash Analytics Module

Uses machine learning techniques to predict future crashes based on historical
patterns, temporal trends, and system state indicators.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from enum import Enum
import statistics
import math


class RiskLevel(Enum):
    """Risk levels for crash prediction"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class TrendDirection(Enum):
    """Trend direction for crash patterns"""
    DECLINING = -1
    STABLE = 0
    RISING = 1
    ACCELERATING = 2


@dataclass
class CrashFeatures:
    """Extracted features from crash data for ML prediction"""
    # Temporal features
    crashes_last_hour: int = 0
    crashes_last_day: int = 0
    crashes_last_week: int = 0
    hour_of_day: int = 0
    day_of_week: int = 0
    
    # Frequency features
    crash_rate_per_hour: float = 0.0
    crash_acceleration: float = 0.0  # Rate of change
    time_since_last_crash: float = 0.0  # In minutes
    
    # Pattern features
    unique_crash_types: int = 0
    most_common_crash_type: str = ""
    crash_diversity_score: float = 0.0  # Entropy-based
    
    # Severity features
    critical_crash_ratio: float = 0.0
    memory_crash_ratio: float = 0.0
    system_crash_ratio: float = 0.0
    
    # Trend features
    trend_direction: TrendDirection = TrendDirection.STABLE
    trend_strength: float = 0.0  # 0-1
    
    # Cyclic features
    is_peak_hour: bool = False
    is_weekend: bool = False
    
    # Historical comparison
    vs_same_hour_last_week: float = 0.0  # Ratio
    vs_daily_average: float = 0.0  # Ratio


@dataclass
class CrashPrediction:
    """Prediction results for future crash risk"""
    timestamp: datetime = field(default_factory=datetime.now)
    prediction_window: int = 60  # Minutes ahead
    
    # Risk assessment
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1
    
    # Quantitative predictions
    predicted_crash_count: int = 0
    predicted_crash_range: Tuple[int, int] = (0, 0)  # Min, max
    
    # Trend information
    trend: TrendDirection = TrendDirection.STABLE
    trend_strength: float = 0.0
    
    # Contributing factors
    primary_risk_factors: List[str] = field(default_factory=list)
    risk_factor_scores: Dict[str, float] = field(default_factory=dict)
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    urgency_level: int = 1  # 1-10


@dataclass
class PredictionMetrics:
    """Metrics for tracking prediction accuracy"""
    total_predictions: int = 0
    correct_predictions: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    average_error: float = 0.0
    confidence_calibration: float = 0.0  # How well confidence matches accuracy


class CrashFeatureExtractor:
    """Extracts ML features from crash history"""
    
    def __init__(self):
        self.crash_type_keywords = {
            'memory': ['memory', 'heap', 'oom', 'outofmemory', 'allocation'],
            'system': ['system', 'native', 'kernel', 'driver'],
            'database': ['database', 'sqlite', 'sql', 'db'],
            'network': ['network', 'connection', 'socket', 'http'],
            'ui': ['ui', 'view', 'activity', 'fragment', 'render']
        }
    
    def extract_features(self, crashes: List[Dict], current_time: Optional[datetime] = None) -> CrashFeatures:
        """Extract features from crash history"""
        if not crashes:
            return CrashFeatures()
        
        if current_time is None:
            current_time = datetime.now()
        
        features = CrashFeatures()
        
        # Temporal features
        features.hour_of_day = current_time.hour
        features.day_of_week = current_time.weekday()
        features.is_weekend = features.day_of_week >= 5
        features.is_peak_hour = 9 <= features.hour_of_day <= 17
        
        # Time-based crash counts
        features.crashes_last_hour = self._count_crashes_in_window(crashes, current_time, hours=1)
        features.crashes_last_day = self._count_crashes_in_window(crashes, current_time, hours=24)
        features.crashes_last_week = self._count_crashes_in_window(crashes, current_time, hours=168)
        
        # Frequency and rate features
        if features.crashes_last_hour > 0:
            features.crash_rate_per_hour = features.crashes_last_hour
        
        # Crash acceleration (comparing last hour to previous hour)
        crashes_prev_hour = self._count_crashes_in_window(
            crashes, current_time - timedelta(hours=1), hours=1
        )
        if crashes_prev_hour > 0:
            features.crash_acceleration = (features.crashes_last_hour - crashes_prev_hour) / crashes_prev_hour
        else:
            features.crash_acceleration = features.crashes_last_hour
        
        # Time since last crash
        latest_crash = self._get_latest_crash(crashes, current_time)
        if latest_crash:
            features.time_since_last_crash = (current_time - latest_crash).total_seconds() / 60
        
        # Pattern features
        crash_types = self._categorize_crashes(crashes[-100:])  # Last 100 crashes
        features.unique_crash_types = len(crash_types)
        if crash_types:
            features.most_common_crash_type = max(crash_types, key=crash_types.get)
            features.crash_diversity_score = self._calculate_entropy(crash_types)
        
        # Severity features
        recent_crashes = [c for c in crashes if self._is_within_window(c, current_time, hours=24)]
        if recent_crashes:
            features.critical_crash_ratio = self._calculate_critical_ratio(recent_crashes)
            features.memory_crash_ratio = self._calculate_type_ratio(recent_crashes, 'memory')
            features.system_crash_ratio = self._calculate_type_ratio(recent_crashes, 'system')
        
        # Trend analysis
        features.trend_direction, features.trend_strength = self._analyze_trend(crashes, current_time)
        
        # Historical comparison
        features.vs_same_hour_last_week = self._compare_to_last_week(crashes, current_time)
        features.vs_daily_average = self._compare_to_average(crashes, current_time)
        
        return features
    
    def _count_crashes_in_window(self, crashes: List[Dict], end_time: datetime, hours: int) -> int:
        """Count crashes within time window"""
        start_time = end_time - timedelta(hours=hours)
        return sum(1 for crash in crashes if self._is_within_window(crash, end_time, hours=hours))
    
    def _is_within_window(self, crash: Dict, end_time: datetime, hours: int) -> bool:
        """Check if crash is within time window"""
        crash_time = self._parse_timestamp(crash.get('timestamp', ''))
        if not crash_time:
            return False
        start_time = end_time - timedelta(hours=hours)
        return start_time <= crash_time <= end_time
    
    def _get_latest_crash(self, crashes: List[Dict], current_time: datetime) -> Optional[datetime]:
        """Get timestamp of most recent crash"""
        valid_times = []
        for crash in reversed(crashes[-50:]):  # Check last 50
            crash_time = self._parse_timestamp(crash.get('timestamp', ''))
            if crash_time and crash_time <= current_time:
                valid_times.append(crash_time)
        return max(valid_times) if valid_times else None
    
    def _categorize_crashes(self, crashes: List[Dict]) -> Dict[str, int]:
        """Categorize crashes by type"""
        categories = defaultdict(int)
        for crash in crashes:
            desc = crash.get('description', '').lower()
            categorized = False
            for category, keywords in self.crash_type_keywords.items():
                if any(kw in desc for kw in keywords):
                    categories[category] += 1
                    categorized = True
                    break
            if not categorized:
                categories['other'] += 1
        return dict(categories)
    
    def _calculate_entropy(self, distribution: Dict[str, int]) -> float:
        """Calculate Shannon entropy for crash type distribution"""
        total = sum(distribution.values())
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in distribution.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Normalize to 0-1
        max_entropy = math.log2(len(distribution)) if len(distribution) > 1 else 1
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _calculate_critical_ratio(self, crashes: List[Dict]) -> float:
        """Calculate ratio of critical crashes"""
        if not crashes:
            return 0.0
        critical_keywords = ['fatal', 'critical', 'crash', 'exception', 'error']
        critical_count = sum(
            1 for crash in crashes
            if any(kw in crash.get('description', '').lower() for kw in critical_keywords)
        )
        return critical_count / len(crashes)
    
    def _calculate_type_ratio(self, crashes: List[Dict], crash_type: str) -> float:
        """Calculate ratio of specific crash type"""
        if not crashes or crash_type not in self.crash_type_keywords:
            return 0.0
        keywords = self.crash_type_keywords[crash_type]
        type_count = sum(
            1 for crash in crashes
            if any(kw in crash.get('description', '').lower() for kw in keywords)
        )
        return type_count / len(crashes)
    
    def _analyze_trend(self, crashes: List[Dict], current_time: datetime) -> Tuple[TrendDirection, float]:
        """Analyze crash trend using linear regression"""
        # Get hourly crash counts for last 24 hours
        hourly_counts = []
        for i in range(24):
            hour_end = current_time - timedelta(hours=i)
            count = self._count_crashes_in_window(crashes, hour_end, hours=1)
            hourly_counts.append(count)
        
        hourly_counts.reverse()  # Oldest to newest
        
        if not hourly_counts or max(hourly_counts) == 0:
            return TrendDirection.STABLE, 0.0
        
        # Simple linear regression
        n = len(hourly_counts)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(hourly_counts)
        
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(hourly_counts))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator > 0 else 0
        
        # Normalize slope to strength (0-1)
        # Use y_mean as reference for slope significance
        slope_significance = abs(slope) / y_mean if y_mean > 0 else abs(slope)
        strength = min(slope_significance, 1.0)
        
        # Determine direction based on slope
        if slope < -0.1:
            direction = TrendDirection.DECLINING
        elif slope > 0.3:
            direction = TrendDirection.ACCELERATING
        elif slope > 0.05:
            direction = TrendDirection.RISING
        else:
            direction = TrendDirection.STABLE
        
        return direction, strength
    
    def _compare_to_last_week(self, crashes: List[Dict], current_time: datetime) -> float:
        """Compare current hour to same hour last week"""
        current_hour_count = self._count_crashes_in_window(crashes, current_time, hours=1)
        last_week_time = current_time - timedelta(days=7)
        last_week_count = self._count_crashes_in_window(crashes, last_week_time, hours=1)
        
        if last_week_count == 0:
            return current_hour_count  # Return absolute if no baseline
        return current_hour_count / last_week_count
    
    def _compare_to_average(self, crashes: List[Dict], current_time: datetime) -> float:
        """Compare current rate to daily average"""
        current_count = self._count_crashes_in_window(crashes, current_time, hours=1)
        daily_count = self._count_crashes_in_window(crashes, current_time, hours=24)
        daily_avg = daily_count / 24 if daily_count > 0 else 0
        
        if daily_avg == 0:
            return current_count
        return current_count / daily_avg
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse crash timestamp"""
        if not timestamp_str:
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%m-%d %H:%M:%S.%f',
            '%m-%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(timestamp_str.strip(), fmt)
                # If year not in timestamp, assume current year
                if parsed.year == 1900:
                    parsed = parsed.replace(year=datetime.now().year)
                return parsed
            except ValueError:
                continue
        
        return None


class PredictiveCrashAnalyzer:
    """Main predictive analytics engine"""
    
    def __init__(self, history_size: int = 10000):
        self.feature_extractor = CrashFeatureExtractor()
        self.crash_history = deque(maxlen=history_size)
        self.prediction_history = []
        self.metrics = PredictionMetrics()
        
        # Model parameters (tunable weights)
        self.weights = {
            'crash_rate': 0.25,
            'acceleration': 0.20,
            'trend': 0.15,
            'recent_severity': 0.15,
            'historical_comparison': 0.15,
            'time_patterns': 0.10
        }
    
    def add_crash(self, crash_data: Dict) -> None:
        """Add crash to history"""
        self.crash_history.append(crash_data)
    
    def predict_crashes(self, prediction_window: int = 60) -> CrashPrediction:
        """
        Predict crash risk for the next N minutes
        
        Args:
            prediction_window: Minutes ahead to predict
        
        Returns:
            CrashPrediction with risk assessment and recommendations
        """
        current_time = datetime.now()
        
        # Extract features
        features = self.feature_extractor.extract_features(list(self.crash_history), current_time)
        
        # Calculate risk score using weighted features
        risk_score = self._calculate_risk_score(features)
        confidence = self._calculate_confidence(features)
        
        # Determine risk level
        risk_level = self._risk_score_to_level(risk_score)
        
        # Predict crash count
        predicted_count, prediction_range = self._predict_crash_count(features, prediction_window)
        
        # Identify risk factors
        risk_factors, factor_scores = self._identify_risk_factors(features)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(features, risk_level)
        
        # Calculate urgency
        urgency = self._calculate_urgency(risk_score, features.trend_direction, features.crash_acceleration)
        
        prediction = CrashPrediction(
            timestamp=current_time,
            prediction_window=prediction_window,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            predicted_crash_count=predicted_count,
            predicted_crash_range=prediction_range,
            trend=features.trend_direction,
            trend_strength=features.trend_strength,
            primary_risk_factors=risk_factors,
            risk_factor_scores=factor_scores,
            recommended_actions=recommendations,
            urgency_level=urgency
        )
        
        self.prediction_history.append(prediction)
        return prediction
    
    def _calculate_risk_score(self, features: CrashFeatures) -> float:
        """Calculate overall risk score from features"""
        scores = {}
        
        # Crash rate score (normalized)
        scores['crash_rate'] = min(features.crash_rate_per_hour / 10, 1.0)
        
        # Acceleration score
        if features.crash_acceleration > 0:
            scores['acceleration'] = min(features.crash_acceleration / 2, 1.0)
        else:
            scores['acceleration'] = 0.0
        
        # Trend score
        trend_values = {
            TrendDirection.DECLINING: 0.2,
            TrendDirection.STABLE: 0.4,
            TrendDirection.RISING: 0.7,
            TrendDirection.ACCELERATING: 1.0
        }
        scores['trend'] = trend_values[features.trend_direction] * features.trend_strength
        
        # Severity score
        scores['recent_severity'] = (
            features.critical_crash_ratio * 0.5 +
            features.memory_crash_ratio * 0.3 +
            features.system_crash_ratio * 0.2
        )
        
        # Historical comparison score
        hist_score = 0.0
        if features.vs_daily_average > 1.5:
            hist_score += 0.5
        if features.vs_same_hour_last_week > 1.5:
            hist_score += 0.5
        scores['historical_comparison'] = min(hist_score, 1.0)
        
        # Time pattern score
        time_score = 0.0
        if features.is_peak_hour:
            time_score += 0.3
        if features.time_since_last_crash < 5:  # Less than 5 minutes
            time_score += 0.7
        scores['time_patterns'] = min(time_score, 1.0)
        
        # Weighted average
        risk_score = sum(scores[k] * self.weights[k] for k in scores)
        
        return min(risk_score, 1.0)
    
    def _calculate_confidence(self, features: CrashFeatures) -> float:
        """Calculate prediction confidence based on data quality"""
        confidence = 0.5  # Base confidence
        
        # More data = more confidence
        if features.crashes_last_week > 100:
            confidence += 0.2
        elif features.crashes_last_week > 50:
            confidence += 0.1
        
        # Clear trend = more confidence
        if features.trend_strength > 0.7:
            confidence += 0.15
        
        # Recent data = more confidence
        if features.time_since_last_crash < 30:
            confidence += 0.1
        
        # Consistent patterns = more confidence
        if features.crash_diversity_score < 0.5:  # Low diversity = consistent
            confidence += 0.05
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _risk_score_to_level(self, risk_score: float) -> RiskLevel:
        """Convert risk score to risk level"""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW
    
    def _predict_crash_count(self, features: CrashFeatures, window: int) -> Tuple[int, Tuple[int, int]]:
        """Predict number of crashes in time window"""
        # Base prediction on current rate
        hourly_rate = features.crash_rate_per_hour
        window_hours = window / 60
        
        base_prediction = hourly_rate * window_hours
        
        # Adjust for trend
        if features.trend_direction == TrendDirection.ACCELERATING:
            base_prediction *= 1.5
        elif features.trend_direction == TrendDirection.RISING:
            base_prediction *= 1.2
        elif features.trend_direction == TrendDirection.DECLINING:
            base_prediction *= 0.7
        
        # Adjust for acceleration
        if features.crash_acceleration > 0:
            base_prediction *= (1 + features.crash_acceleration * 0.3)
        
        predicted = max(0, int(round(base_prediction)))
        
        # Calculate confidence interval (rough estimate)
        margin = max(1, int(predicted * 0.3))
        prediction_range = (max(0, predicted - margin), predicted + margin)
        
        return predicted, prediction_range
    
    def _identify_risk_factors(self, features: CrashFeatures) -> Tuple[List[str], Dict[str, float]]:
        """Identify primary risk factors"""
        factors = {}
        
        if features.crash_rate_per_hour > 5:
            factors['High crash frequency'] = min(features.crash_rate_per_hour / 10, 1.0)
        
        if features.crash_acceleration > 1.0:
            factors['Accelerating crash rate'] = min(features.crash_acceleration / 3, 1.0)
        
        if features.trend_direction in [TrendDirection.RISING, TrendDirection.ACCELERATING]:
            factors['Rising trend'] = features.trend_strength
        
        if features.critical_crash_ratio > 0.5:
            factors['High severity crashes'] = features.critical_crash_ratio
        
        if features.memory_crash_ratio > 0.3:
            factors['Memory issues'] = features.memory_crash_ratio
        
        if features.vs_daily_average > 2.0:
            factors['Unusual for this time'] = min(features.vs_daily_average / 5, 1.0)
        
        if features.time_since_last_crash < 5:
            factors['Very recent crashes'] = 1.0 - (features.time_since_last_crash / 5)
        
        if features.crash_diversity_score > 0.7:
            factors['Multiple crash types'] = features.crash_diversity_score
        
        # Sort by score
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        primary_factors = [f[0] for f in sorted_factors[:3]]
        
        return primary_factors, factors
    
    def _generate_recommendations(self, features: CrashFeatures, risk_level: RiskLevel) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recommendations.append("Immediate investigation required")
            recommendations.append("Review recent code changes and deployments")
        
        if features.memory_crash_ratio > 0.3:
            recommendations.append("Investigate memory leaks and heap usage")
        
        if features.system_crash_ratio > 0.3:
            recommendations.append("Check system resources and native code")
        
        if features.crash_diversity_score > 0.7:
            recommendations.append("Multiple issue types detected - broad investigation needed")
        
        if features.trend_direction in [TrendDirection.RISING, TrendDirection.ACCELERATING]:
            recommendations.append("Trend is worsening - consider rollback or hotfix")
        
        if features.vs_same_hour_last_week > 2.0:
            recommendations.append("Unusual spike compared to last week - check recent changes")
        
        if features.crash_rate_per_hour > 10:
            recommendations.append("Critical crash rate - enable additional logging")
        
        if not recommendations:
            recommendations.append("Monitor situation - current risk is manageable")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _calculate_urgency(self, risk_score: float, trend: TrendDirection, acceleration: float) -> int:
        """Calculate urgency level (1-10)"""
        # Base urgency from risk score
        urgency = risk_score * 7
        
        # Increase urgency for bad trends
        if trend == TrendDirection.ACCELERATING:
            urgency += 2
        elif trend == TrendDirection.RISING:
            urgency += 1
        
        # Increase urgency for high acceleration
        if acceleration > 2.0:
            urgency += 1
        
        return min(10, max(1, int(round(urgency))))
    
    def get_prediction_metrics(self) -> PredictionMetrics:
        """Get prediction accuracy metrics"""
        return self.metrics
    
    def validate_prediction(self, prediction: CrashPrediction, actual_crashes: int) -> None:
        """Validate a prediction against actual outcome"""
        self.metrics.total_predictions += 1
        
        predicted_min, predicted_max = prediction.predicted_crash_range
        
        # Check if actual falls within predicted range
        if predicted_min <= actual_crashes <= predicted_max:
            self.metrics.correct_predictions += 1
        elif actual_crashes < predicted_min:
            self.metrics.false_positives += 1
        else:
            self.metrics.false_negatives += 1
        
        # Update average error
        error = abs(prediction.predicted_crash_count - actual_crashes)
        prev_total = self.metrics.total_predictions - 1
        self.metrics.average_error = (
            (self.metrics.average_error * prev_total + error) / self.metrics.total_predictions
        )
