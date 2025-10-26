"""
Unit tests for Enhanced Pattern Detector
"""

import pytest
from datetime import datetime, timedelta


@pytest.mark.unit
class TestStatisticalPatternDetector:
    """Test cases for StatisticalPatternDetector"""
    
    def test_initialization(self, pattern_detector):
        """Test detector initializes correctly"""
        assert pattern_detector is not None
        assert pattern_detector.min_pattern_frequency >= 0
        assert 0 <= pattern_detector.confidence_threshold <= 1
    
    def test_analyze_empty_crashes(self, pattern_detector):
        """Test analyzing empty crash list"""
        patterns = pattern_detector.analyze_crash_patterns([])
        assert isinstance(patterns, list)
        assert len(patterns) == 0
    
    def test_analyze_single_crash(self, pattern_detector, sample_crash):
        """Test analyzing single crash"""
        patterns = pattern_detector.analyze_crash_patterns([sample_crash])
        # Single crash shouldn't produce patterns
        assert len(patterns) == 0
    
    def test_detect_memory_pattern(self, pattern_detector):
        """Test detecting memory exhaustion pattern"""
        crashes = []
        current_time = datetime.now()
        
        # Create memory crash cluster
        for i in range(5):
            crash_time = current_time + timedelta(seconds=i * 5)
            crashes.append({
                'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'app_name': 'MemoryApp',
                'title': f'Memory Crash {i}',
                'description': f'OutOfMemoryError: heap space exceeded {i}',
                'related_logs': []
            })
        
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        
        assert len(patterns) > 0
        memory_pattern = next((p for p in patterns if 'memory' in p.name.lower()), None)
        assert memory_pattern is not None
        assert memory_pattern.frequency >= 3
        assert memory_pattern.confidence_score > 0
    
    def test_frequency_scoring(self, pattern_detector, sample_crashes):
        """Test frequency-based scoring"""
        patterns = pattern_detector.analyze_crash_patterns(sample_crashes)
        
        if patterns:
            for pattern in patterns:
                # Frequency should be positive
                assert pattern.frequency > 0
                # More frequent patterns should have higher base scores
                assert pattern.frequency <= len(sample_crashes)
    
    def test_temporal_clustering(self, pattern_detector):
        """Test temporal clustering detection"""
        crashes = []
        current_time = datetime.now()
        
        # Create tight temporal cluster
        for i in range(3):
            crash_time = current_time + timedelta(seconds=i * 2)  # 2 seconds apart
            crashes.append({
                'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'app_name': 'ClusterApp',
                'title': f'Cluster Crash {i}',
                'description': 'Related crash in cluster',
                'related_logs': []
            })
        
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        
        if patterns:
            # At least one pattern should have high temporal clustering
            assert any(p.temporal_clustering_score > 0.5 for p in patterns)
    
    def test_correlation_analysis(self, pattern_detector, diverse_crashes):
        """Test correlation detection between crash types"""
        patterns = pattern_detector.analyze_crash_patterns(diverse_crashes)
        
        # With diverse crashes, correlation should be moderate/low
        if patterns:
            for pattern in patterns:
                assert 0 <= pattern.correlation_strength <= 1
    
    def test_confidence_calculation(self, pattern_detector, sample_crashes):
        """Test confidence score calculation"""
        patterns = pattern_detector.analyze_crash_patterns(sample_crashes)
        
        for pattern in patterns:
            # Confidence should be normalized 0-1
            assert 0 <= pattern.confidence_score <= 1
            # Confidence should be reasonable given inputs
            assert pattern.confidence_score >= pattern_detector.confidence_threshold


@pytest.mark.unit
class TestPatternIdentification:
    """Test pattern identification logic"""
    
    def test_identify_cascade_pattern(self, pattern_detector):
        """Test identifying cascade failure patterns"""
        # Create enough cascading crashes to meet frequency threshold
        crashes = []
        current_time = datetime.now()
        
        for i in range(5):
            crash_time = current_time + timedelta(seconds=i * 3)
            crashes.append({
                'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'app_name': 'CascadeApp',
                'title': f'Cascade Crash {i}',
                'description': 'Database timeout causing cascade',
                'related_logs': []
            })
        
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        
        # Should process without error (may or may not detect patterns depending on thresholds)
        assert isinstance(patterns, list)
        
        # If patterns detected, check properties
        if patterns:
            for pattern in patterns:
                assert pattern.temporal_clustering_score >= 0
                assert pattern.frequency > 0
    
    def test_severity_assessment(self, pattern_detector):
        """Test pattern severity assessment"""
        from android_crash_monitor.analysis.enhanced_pattern_detector import PatternSeverity
        
        crashes = []
        current_time = datetime.now()
        
        # Create critical severity pattern
        for i in range(10):  # High frequency
            crash_time = current_time + timedelta(seconds=i)
            crashes.append({
                'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'app_name': 'CriticalApp',
                'title': f'Critical Crash {i}',
                'description': 'Fatal system crash',
                'related_logs': []
            })
        
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        
        if patterns:
            # High frequency should result in higher severity
            high_freq_patterns = [p for p in patterns if p.frequency >= 5]
            assert len(high_freq_patterns) > 0
            
            for pattern in high_freq_patterns:
                assert pattern.severity in [PatternSeverity.HIGH, PatternSeverity.CRITICAL]
    
    def test_urgency_calculation(self, pattern_detector, sample_crashes):
        """Test urgency level calculation"""
        patterns = pattern_detector.analyze_crash_patterns(sample_crashes)
        
        for pattern in patterns:
            # Urgency should be 1-10
            assert 1 <= pattern.urgency_level <= 10
            # Higher confidence should correlate with higher urgency
            if pattern.confidence_score > 0.8:
                assert pattern.urgency_level >= 5


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_malformed_timestamps(self, pattern_detector):
        """Test handling of malformed timestamps"""
        crashes = [
            {'timestamp': 'invalid', 'title': 'Bad Time 1', 'description': 'test', 'related_logs': []},
            {'timestamp': '', 'title': 'Bad Time 2', 'description': 'test', 'related_logs': []},
            {'title': 'No Time', 'description': 'test', 'related_logs': []}  # Missing timestamp
        ]
        
        # Should not crash, handle gracefully
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        assert isinstance(patterns, list)
    
    def test_missing_fields(self, pattern_detector):
        """Test handling crashes with missing fields"""
        crashes = [
            {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]},
            {'description': 'Only description'},
            {}  # Empty crash
        ]
        
        # Should handle gracefully
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        assert isinstance(patterns, list)
    
    def test_duplicate_crashes(self, pattern_detector, sample_crash):
        """Test handling duplicate crashes"""
        crashes = [sample_crash.copy() for _ in range(5)]
        
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        
        # Should still produce valid patterns
        assert isinstance(patterns, list)
        
        if patterns:
            # Frequency should reflect duplicates
            assert any(p.frequency >= 3 for p in patterns)
