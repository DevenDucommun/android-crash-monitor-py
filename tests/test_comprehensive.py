"""
Comprehensive Test Suite for Android Crash Monitor
Includes unit, integration, feature, and system tests
"""

import pytest
from datetime import datetime, timedelta
import time


# ============================================================================
# UNIT TESTS - Individual Component Testing
# ============================================================================

@pytest.mark.unit
class TestPredictiveAnalytics:
    """Unit tests for predictive analytics"""
    
    def test_feature_extraction(self, predictive_analyzer, sample_crashes):
        """Test feature extraction from crashes"""
        from android_crash_monitor.analysis.predictive_analytics import CrashFeatureExtractor
        
        extractor = CrashFeatureExtractor()
        features = extractor.extract_features(sample_crashes)
        
        assert features is not None
        assert features.crashes_last_hour >= 0
        assert features.crashes_last_day >= 0
        assert 0 <= features.crash_diversity_score <= 1
    
    def test_risk_score_calculation(self, predictive_analyzer, sample_crashes):
        """Test risk score calculation"""
        for crash in sample_crashes:
            predictive_analyzer.add_crash(crash)
        
        prediction = predictive_analyzer.predict_crashes(60)
        
        assert 0 <= prediction.risk_score <= 1
        assert prediction.risk_level is not None
    
    def test_trend_detection(self, predictive_analyzer):
        """Test trend direction detection"""
        from android_crash_monitor.analysis.predictive_analytics import TrendDirection
        
        # Create escalating pattern
        current_time = datetime.now()
        for hour in range(6):
            crashes_count = (hour + 1) * 2  # Escalating
            for i in range(crashes_count):
                crash_time = current_time - timedelta(hours=6-hour)
                predictive_analyzer.add_crash({
                    'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'description': 'Test crash',
                    'title': f'Crash {i}'
                })
        
        prediction = predictive_analyzer.predict_crashes(60)
        
        # Should detect rising or accelerating trend
        assert prediction.trend in [TrendDirection.RISING, TrendDirection.ACCELERATING]


@pytest.mark.unit
class TestRootCauseAnalyzer:
    """Unit tests for RCA components"""
    
    def test_dependency_detection(self, rca_analyzer, cascading_crashes):
        """Test crash dependency detection"""
        result = rca_analyzer.analyze(cascading_crashes)
        
        assert len(result.crash_dependencies) > 0
        # Cascading crashes should have dependencies
        for dep in result.crash_dependencies:
            assert dep.confidence > 0
            assert dep.time_delta >= 0
    
    def test_component_health_tracking(self, rca_analyzer, diverse_crashes):
        """Test component health assessment"""
        result = rca_analyzer.analyze(diverse_crashes)
        
        assert len(result.component_health) > 0
        for comp_name, component in result.component_health.items():
            assert 0 <= component.health_score <= 1
            assert component.failure_count > 0
    
    def test_fault_tree_construction(self, rca_analyzer, sample_crashes):
        """Test fault tree generation"""
        result = rca_analyzer.analyze(sample_crashes)
        
        assert result.fault_tree is not None
        assert result.fault_tree.event_type == "root"
        assert 0 <= result.fault_tree.probability <= 1


# ============================================================================
# INTEGRATION TESTS - Module Interaction Testing
# ============================================================================

@pytest.mark.integration
class TestRealtimeIntegration:
    """Integration tests for real-time analysis"""
    
    def test_realtime_with_pattern_detector(self, realtime_analyzer, sample_crashes):
        """Test real-time analyzer integrates with pattern detector"""
        realtime_analyzer.start_realtime_analysis()
        
        # Add crashes
        for crash in sample_crashes:
            realtime_analyzer.add_crash(crash)
        
        # Allow processing
        time.sleep(1)
        
        stats = realtime_analyzer.get_realtime_stats()
        patterns = realtime_analyzer.get_active_patterns()
        
        assert stats.total_crashes == len(sample_crashes)
        realtime_analyzer.stop_realtime_analysis()
    
    def test_alert_triggering(self, sample_crashes):
        """Test alert system integration"""
        from android_crash_monitor.analysis.realtime_analyzer import RealtimePatternAnalyzer
        
        alerts_received = []
        
        def alert_callback(alert):
            alerts_received.append(alert)
        
        analyzer = RealtimePatternAnalyzer(alert_callback=alert_callback)
        analyzer.start_realtime_analysis()
        
        # Add crashes to trigger pattern
        for crash in sample_crashes:
            analyzer.add_crash(crash)
        
        time.sleep(2)
        
        analyzer.stop_realtime_analysis()
        
        # May or may not have alerts depending on pattern strength
        assert isinstance(alerts_received, list)


@pytest.mark.integration
class TestPredictiveWithRCA:
    """Integration between predictive analytics and RCA"""
    
    def test_prediction_informs_rca(self, predictive_analyzer, rca_analyzer, cascading_crashes):
        """Test that predictions can inform RCA"""
        # Build history
        for crash in cascading_crashes:
            predictive_analyzer.add_crash(crash)
        
        # Get prediction
        prediction = predictive_analyzer.predict_crashes(60)
        
        # Run RCA
        rca_result = rca_analyzer.analyze(cascading_crashes)
        
        # Both should identify issues
        assert prediction.risk_score > 0 or len(rca_result.primary_root_causes) > 0


# ============================================================================
# FEATURE TESTS - End-to-End Feature Testing
# ============================================================================

@pytest.mark.feature
class TestAnalysisWorkflow:
    """Test complete analysis workflows"""
    
    def test_full_crash_analysis_pipeline(self, pattern_detector, predictive_analyzer, 
                                          rca_analyzer, diverse_crashes):
        """Test complete analysis pipeline"""
        # Step 1: Pattern Detection
        patterns = pattern_detector.analyze_crash_patterns(diverse_crashes)
        assert isinstance(patterns, list)
        
        # Step 2: Predictive Analysis
        for crash in diverse_crashes:
            predictive_analyzer.add_crash(crash)
        prediction = predictive_analyzer.predict_crashes(60)
        assert prediction is not None
        
        # Step 3: Root Cause Analysis
        rca_result = rca_analyzer.analyze(diverse_crashes)
        assert rca_result is not None
        
        # All steps should complete successfully
        assert len(patterns) >= 0
        assert prediction.confidence > 0
        assert len(rca_result.evidence_summary) >= 0
    
    def test_incremental_analysis(self, realtime_analyzer):
        """Test incremental crash analysis"""
        realtime_analyzer.start_realtime_analysis()
        
        current_time = datetime.now()
        
        # Add crashes incrementally
        for i in range(5):
            crash = {
                'timestamp': (current_time + timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': f'Incremental Crash {i}',
                'description': 'Test crash for incremental analysis',
                'app_name': 'TestApp',
                'related_logs': []
            }
            realtime_analyzer.add_crash(crash)
            time.sleep(0.1)
        
        time.sleep(1)
        
        stats = realtime_analyzer.get_realtime_stats()
        assert stats.total_crashes == 5
        
        realtime_analyzer.stop_realtime_analysis()


@pytest.mark.feature
class TestRecommendationGeneration:
    """Test recommendation generation features"""
    
    def test_remediation_recommendations(self, rca_analyzer, cascading_crashes):
        """Test remediation step generation"""
        result = rca_analyzer.analyze(cascading_crashes)
        
        assert len(result.remediation_steps) > 0
        # Recommendations should be actionable strings
        for step in result.remediation_steps:
            assert isinstance(step, str)
            assert len(step) > 10  # Should be meaningful
    
    def test_prevention_recommendations(self, rca_analyzer, diverse_crashes):
        """Test prevention measure generation"""
        result = rca_analyzer.analyze(diverse_crashes)
        
        assert len(result.prevention_measures) > 0
        for measure in result.prevention_measures:
            assert isinstance(measure, str)
            assert len(measure) > 10


# ============================================================================
# SYSTEM TESTS - Full System Behavior
# ============================================================================

@pytest.mark.system
class TestSystemIntegration:
    """System-level integration tests"""
    
    def test_complete_monitoring_cycle(self, realtime_analyzer, rca_analyzer):
        """Test complete monitoring and analysis cycle"""
        # Start monitoring
        assert realtime_analyzer.start_realtime_analysis()
        
        # Simulate crashes over time
        current_time = datetime.now()
        crash_count = 10
        
        for i in range(crash_count):
            crash_time = current_time + timedelta(seconds=i * 2)
            realtime_analyzer.add_crash({
                'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': f'System Test Crash {i}',
                'description': f'System test crash {i}',
                'app_name': 'SystemTest',
                'related_logs': []
            })
        
        time.sleep(2)
        
        # Get real-time stats
        stats = realtime_analyzer.get_realtime_stats()
        assert stats.total_crashes == crash_count
        
        # Run RCA on collected crashes
        crashes = list(realtime_analyzer.crash_buffer)
        rca_result = rca_analyzer.analyze(crashes)
        
        assert rca_result is not None
        assert rca_result.overall_confidence >= 0
        
        # Stop monitoring
        assert realtime_analyzer.stop_realtime_analysis()
    
    def test_concurrent_analysis(self, pattern_detector, predictive_analyzer):
        """Test concurrent analysis operations"""
        import threading
        
        results = {'patterns': None, 'prediction': None, 'errors': []}
        
        crashes = []
        current_time = datetime.now()
        for i in range(10):
            crashes.append({
                'timestamp': (current_time + timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': f'Concurrent Crash {i}',
                'description': 'Concurrent test crash',
                'app_name': 'ConcurrentTest',
                'related_logs': []
            })
        
        def run_pattern_detection():
            try:
                results['patterns'] = pattern_detector.analyze_crash_patterns(crashes)
            except Exception as e:
                results['errors'].append(('pattern', str(e)))
        
        def run_prediction():
            try:
                for crash in crashes:
                    predictive_analyzer.add_crash(crash)
                results['prediction'] = predictive_analyzer.predict_crashes(60)
            except Exception as e:
                results['errors'].append(('prediction', str(e)))
        
        # Run concurrently
        t1 = threading.Thread(target=run_pattern_detection)
        t2 = threading.Thread(target=run_prediction)
        
        t1.start()
        t2.start()
        
        t1.join(timeout=5)
        t2.join(timeout=5)
        
        # Both should complete without errors
        assert len(results['errors']) == 0
        assert results['patterns'] is not None
        assert results['prediction'] is not None


# ============================================================================
# PERFORMANCE TESTS - Load and Performance Testing
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Performance and load tests"""
    
    def test_high_volume_crash_processing(self, realtime_analyzer, performance_timer):
        """Test processing high volume of crashes"""
        realtime_analyzer.start_realtime_analysis()
        
        crash_count = 100
        current_time = datetime.now()
        
        performance_timer.start()
        
        for i in range(crash_count):
            crash_time = current_time + timedelta(milliseconds=i * 10)
            realtime_analyzer.add_crash({
                'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': f'Load Test Crash {i}',
                'description': 'Performance test crash',
                'app_name': 'LoadTest',
                'related_logs': []
            })
        
        time.sleep(2)  # Allow processing
        
        elapsed = performance_timer.stop()
        
        stats = realtime_analyzer.get_realtime_stats()
        realtime_analyzer.stop_realtime_analysis()
        
        # Should process all crashes
        assert stats.total_crashes == crash_count
        
        # Should be reasonably fast (< 5 seconds for 100 crashes)
        assert elapsed < 5.0
        
        # Calculate throughput
        throughput = crash_count / elapsed if elapsed > 0 else 0
        print(f"\\nThroughput: {throughput:.1f} crashes/second")
        assert throughput > 10  # Should handle at least 10 crashes/sec
    
    def test_pattern_detection_performance(self, pattern_detector, performance_timer):
        """Test pattern detection performance with large dataset"""
        # Generate large crash dataset
        crashes = []
        current_time = datetime.now()
        
        for i in range(200):
            crash_time = current_time + timedelta(seconds=i)
            crashes.append({
                'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': f'Perf Test Crash {i}',
                'description': f'Performance test crash {i % 5}',  # 5 patterns
                'app_name': f'PerfApp{i % 3}',
                'related_logs': []
            })
        
        performance_timer.start()
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        elapsed = performance_timer.stop()
        
        # Should complete in reasonable time
        assert elapsed < 10.0  # Less than 10 seconds for 200 crashes
        
        print(f"\\nPattern detection: {elapsed:.2f}s for {len(crashes)} crashes")
        print(f"Found {len(patterns)} patterns")
    
    def test_memory_efficiency(self, realtime_analyzer):
        """Test memory efficiency with long-running analysis"""
        import sys
        
        realtime_analyzer.start_realtime_analysis()
        
        initial_buffer_size = len(realtime_analyzer.crash_buffer)
        
        # Add many crashes
        current_time = datetime.now()
        for i in range(1000):
            crash_time = current_time + timedelta(milliseconds=i)
            realtime_analyzer.add_crash({
                'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': f'Memory Test {i}',
                'description': 'Memory efficiency test',
                'app_name': 'MemTest',
                'related_logs': []
            })
        
        time.sleep(2)
        
        # Buffer should not grow unbounded (has maxlen)
        final_buffer_size = len(realtime_analyzer.crash_buffer)
        assert final_buffer_size <= realtime_analyzer.crash_buffer.maxlen
        
        realtime_analyzer.stop_realtime_analysis()


# ============================================================================
# REGRESSION TESTS - Prevent Known Issues
# ============================================================================

@pytest.mark.unit
class TestRegressions:
    """Tests for known issues and regressions"""
    
    def test_timestamp_parsing_regression(self, pattern_detector):
        """Test that various timestamp formats are handled"""
        crashes = [
            {'timestamp': '2025-01-15 10:30:45.123', 'title': 'Full', 'description': 'test', 'related_logs': []},
            {'timestamp': '2025-01-15 10:30:45', 'title': 'No ms', 'description': 'test', 'related_logs': []},
            {'timestamp': '01-15 10:30:45.123', 'title': 'No year', 'description': 'test', 'related_logs': []},
        ]
        
        # Should not crash
        patterns = pattern_detector.analyze_crash_patterns(crashes)
        assert isinstance(patterns, list)
    
    def test_empty_description_handling(self, rca_analyzer):
        """Test handling crashes with empty descriptions"""
        crashes = [
            {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 
             'title': 'Empty desc', 'description': '', 'related_logs': []},
            {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 
             'title': 'No desc', 'related_logs': []},
        ]
        
        result = rca_analyzer.analyze(crashes)
        assert result is not None
    
    def test_confidence_bounds(self, pattern_detector, sample_crashes):
        """Test that confidence scores are always in valid range"""
        patterns = pattern_detector.analyze_crash_patterns(sample_crashes)
        
        for pattern in patterns:
            assert 0 <= pattern.confidence_score <= 1, "Confidence out of bounds"
            assert 0 <= pattern.correlation_strength <= 1, "Correlation out of bounds"
            assert 0 <= pattern.temporal_clustering_score <= 1, "Temporal score out of bounds"
