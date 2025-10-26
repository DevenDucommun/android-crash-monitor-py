#!/usr/bin/env python3
"""
Test Predictive Crash Analytics System

Tests the ML-based crash prediction engine
"""

from datetime import datetime, timedelta
import time


def test_feature_extraction():
    """Test feature extraction from crash data"""
    print("🔬 Testing Feature Extraction")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.predictive_analytics import (
            CrashFeatureExtractor, TrendDirection
        )
        
        extractor = CrashFeatureExtractor()
        
        # Generate test crash data with temporal pattern
        current_time = datetime.now()
        crashes = []
        
        # Create escalating pattern over 24 hours
        for hour in range(24):
            crash_time = current_time - timedelta(hours=23-hour)
            num_crashes = 1 + (hour // 4)  # Escalating: 1,1,1,1,2,2,2,2,3...
            
            for i in range(num_crashes):
                crashes.append({
                    'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'app_name': f'TestApp{i % 3}',
                    'description': 'OutOfMemoryError: heap space exceeded' if i % 2 == 0 else 'System crash',
                    'title': f'Crash {len(crashes)}',
                    'related_logs': [{'message': 'Error occurred', 'level': 'ERROR'}]
                })
        
        print(f"Generated {len(crashes)} test crashes")
        
        # Extract features
        features = extractor.extract_features(crashes, current_time)
        
        print(f"\n📊 Extracted Features:")
        print(f"  Temporal:")
        print(f"    • Hour of day: {features.hour_of_day}")
        print(f"    • Day of week: {features.day_of_week} ({'weekend' if features.is_weekend else 'weekday'})")
        print(f"    • Peak hour: {features.is_peak_hour}")
        
        print(f"\n  Crash Counts:")
        print(f"    • Last hour: {features.crashes_last_hour}")
        print(f"    • Last day: {features.crashes_last_day}")
        print(f"    • Last week: {features.crashes_last_week}")
        
        print(f"\n  Frequency Metrics:")
        print(f"    • Crash rate/hour: {features.crash_rate_per_hour:.2f}")
        print(f"    • Crash acceleration: {features.crash_acceleration:.2f}")
        print(f"    • Time since last crash: {features.time_since_last_crash:.1f} min")
        
        print(f"\n  Pattern Analysis:")
        print(f"    • Unique crash types: {features.unique_crash_types}")
        print(f"    • Most common type: {features.most_common_crash_type}")
        print(f"    • Diversity score: {features.crash_diversity_score:.2f}")
        
        print(f"\n  Severity:")
        print(f"    • Critical ratio: {features.critical_crash_ratio:.1%}")
        print(f"    • Memory crash ratio: {features.memory_crash_ratio:.1%}")
        print(f"    • System crash ratio: {features.system_crash_ratio:.1%}")
        
        print(f"\n  Trend:")
        print(f"    • Direction: {features.trend_direction.name}")
        print(f"    • Strength: {features.trend_strength:.1%}")
        
        print(f"\n  Historical Comparison:")
        print(f"    • vs Daily Average: {features.vs_daily_average:.2f}x")
        print(f"    • vs Last Week: {features.vs_same_hour_last_week:.2f}x")
        
        # Validation
        success_criteria = [
            features.crashes_last_day > 0,
            features.unique_crash_types > 0,
            features.trend_direction != TrendDirection.STABLE  # Should detect rising trend
        ]
        
        success = all(success_criteria)
        print(f"\n✅ Feature Extraction: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Feature extraction test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crash_prediction():
    """Test crash prediction engine"""
    print("\n🔮 Testing Crash Prediction Engine")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.predictive_analytics import (
            PredictiveCrashAnalyzer, RiskLevel, TrendDirection
        )
        
        analyzer = PredictiveCrashAnalyzer()
        
        # Simulate escalating crash pattern
        current_time = datetime.now()
        
        print("Simulating crash patterns...")
        
        # Low risk scenario (past crashes, declining)
        print("\n1️⃣ Scenario: Low Risk (Old crashes, declining)")
        for hour in range(12, 0, -1):  # 12 to 1 hour ago, declining
            crash_time = current_time - timedelta(hours=hour)
            num_crashes = max(1, hour // 4)  # Declining
            
            for i in range(num_crashes):
                analyzer.add_crash({
                    'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'app_name': 'SafeApp',
                    'description': 'Minor issue resolved',
                    'title': f'Old Crash {i}'
                })
        
        prediction_low = analyzer.predict_crashes(prediction_window=60)
        print(f"   Risk Level: {prediction_low.risk_level.name}")
        print(f"   Risk Score: {prediction_low.risk_score:.1%}")
        print(f"   Confidence: {prediction_low.confidence:.1%}")
        print(f"   Predicted crashes (next hour): {prediction_low.predicted_crash_count} ({prediction_low.predicted_crash_range[0]}-{prediction_low.predicted_crash_range[1]})")
        print(f"   Trend: {prediction_low.trend.name}")
        print(f"   Urgency: {prediction_low.urgency_level}/10")
        
        # High risk scenario (recent crashes, accelerating)
        print("\n2️⃣ Scenario: High Risk (Recent crashes, accelerating)")
        analyzer2 = PredictiveCrashAnalyzer()
        
        # Add accelerating pattern with more recent crashes
        for minute in range(60, 0, -5):  # Last hour, every 5 minutes
            crash_time = current_time - timedelta(minutes=minute)
            # Accelerating: more crashes in recent minutes
            num_crashes = max(1, (60 - minute) // 10)  # 1,1,1,...,2,2,...,5,5,6
            
            for i in range(num_crashes):
                analyzer2.add_crash({
                    'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'app_name': 'ProblematicApp',
                    'description': 'Fatal OutOfMemoryError: heap exhausted',
                    'title': f'Critical Crash {i}'
                })
        
        prediction_high = analyzer2.predict_crashes(prediction_window=60)
        print(f"   Risk Level: {prediction_high.risk_level.name}")
        print(f"   Risk Score: {prediction_high.risk_score:.1%}")
        print(f"   Confidence: {prediction_high.confidence:.1%}")
        print(f"   Predicted crashes (next hour): {prediction_high.predicted_crash_count} ({prediction_high.predicted_crash_range[0]}-{prediction_high.predicted_crash_range[1]})")
        print(f"   Trend: {prediction_high.trend.name}")
        print(f"   Urgency: {prediction_high.urgency_level}/10")
        
        if prediction_high.primary_risk_factors:
            print(f"   Risk Factors:")
            for factor in prediction_high.primary_risk_factors:
                score = prediction_high.risk_factor_scores.get(factor, 0)
                print(f"     • {factor}: {score:.1%}")
        
        if prediction_high.recommended_actions:
            print(f"   Recommendations:")
            for action in prediction_high.recommended_actions[:3]:
                print(f"     • {action}")
        
        # Medium risk scenario (steady rate)
        print("\n3️⃣ Scenario: Medium Risk (Steady crash rate)")
        analyzer3 = PredictiveCrashAnalyzer()
        
        for hour in range(12, 0, -1):
            crash_time = current_time - timedelta(hours=hour)
            num_crashes = 3  # Steady rate
            
            for i in range(num_crashes):
                analyzer3.add_crash({
                    'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'app_name': 'StableApp',
                    'description': 'Database error' if i % 2 == 0 else 'Network timeout',
                    'title': f'Steady Crash {i}'
                })
        
        prediction_medium = analyzer3.predict_crashes(prediction_window=30)
        print(f"   Risk Level: {prediction_medium.risk_level.name}")
        print(f"   Risk Score: {prediction_medium.risk_score:.1%}")
        print(f"   Predicted crashes (next 30min): {prediction_medium.predicted_crash_count}")
        print(f"   Trend: {prediction_medium.trend.name}")
        
        # Validation
        success_criteria = [
            prediction_high.risk_score > prediction_low.risk_score,  # High risk > low risk
            prediction_high.urgency_level > prediction_low.urgency_level,
            prediction_high.predicted_crash_count > prediction_low.predicted_crash_count,
            prediction_high.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            len(prediction_high.recommended_actions) > 0
        ]
        
        success = all(success_criteria)
        print(f"\n✅ Prediction Engine: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Prediction test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prediction_validation():
    """Test prediction accuracy tracking"""
    print("\n📈 Testing Prediction Validation")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.predictive_analytics import (
            PredictiveCrashAnalyzer, CrashPrediction, RiskLevel
        )
        
        analyzer = PredictiveCrashAnalyzer()
        
        # Add baseline crashes
        current_time = datetime.now()
        for hour in range(6, 0, -1):
            crash_time = current_time - timedelta(hours=hour)
            for i in range(3):
                analyzer.add_crash({
                    'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'app_name': 'TestApp',
                    'description': 'Test crash',
                    'title': f'Crash {i}'
                })
        
        # Make prediction
        prediction = analyzer.predict_crashes(60)
        print(f"Made prediction: {prediction.predicted_crash_count} crashes expected")
        print(f"  Range: {prediction.predicted_crash_range[0]}-{prediction.predicted_crash_range[1]}")
        
        # Simulate outcomes
        test_cases = [
            (prediction.predicted_crash_count, "Exact match"),
            (prediction.predicted_crash_range[0] + 1, "Within range (low)"),
            (prediction.predicted_crash_range[1] - 1, "Within range (high)"),
            (0, "False positive"),
            (prediction.predicted_crash_range[1] + 10, "False negative")
        ]
        
        print(f"\nValidating predictions against outcomes:")
        for actual, description in test_cases:
            analyzer.validate_prediction(prediction, actual)
            print(f"  • {description}: actual={actual}")
        
        metrics = analyzer.get_prediction_metrics()
        print(f"\n📊 Prediction Metrics:")
        print(f"  • Total predictions: {metrics.total_predictions}")
        print(f"  • Correct predictions: {metrics.correct_predictions}")
        print(f"  • False positives: {metrics.false_positives}")
        print(f"  • False negatives: {metrics.false_negatives}")
        print(f"  • Average error: {metrics.average_error:.2f}")
        
        accuracy = metrics.correct_predictions / metrics.total_predictions if metrics.total_predictions > 0 else 0
        print(f"  • Accuracy: {accuracy:.1%}")
        
        success = metrics.total_predictions == len(test_cases)
        print(f"\n✅ Prediction Validation: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Validation test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases and robustness"""
    print("\n🔧 Testing Edge Cases")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.predictive_analytics import (
            PredictiveCrashAnalyzer, CrashFeatureExtractor
        )
        
        successes = []
        
        # Test 1: No crashes
        print("1. Empty crash history...")
        analyzer_empty = PredictiveCrashAnalyzer()
        prediction_empty = analyzer_empty.predict_crashes()
        success_1 = (prediction_empty.predicted_crash_count == 0 and 
                     prediction_empty.risk_level.value <= 2)  # VERY_LOW or LOW
        print(f"   Result: {prediction_empty.risk_level.name} - {'✅' if success_1 else '❌'}")
        successes.append(success_1)
        
        # Test 2: Single crash
        print("2. Single crash...")
        analyzer_single = PredictiveCrashAnalyzer()
        analyzer_single.add_crash({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'app_name': 'App',
            'description': 'Crash',
            'title': 'Single'
        })
        prediction_single = analyzer_single.predict_crashes()
        success_2 = prediction_single.predicted_crash_count >= 0
        print(f"   Result: Predicted {prediction_single.predicted_crash_count} - {'✅' if success_2 else '❌'}")
        successes.append(success_2)
        
        # Test 3: Malformed timestamps
        print("3. Malformed timestamps...")
        extractor = CrashFeatureExtractor()
        bad_crashes = [
            {'timestamp': 'invalid', 'description': 'test'},
            {'timestamp': '', 'description': 'test'},
            {'description': 'test'},  # No timestamp
        ]
        features_bad = extractor.extract_features(bad_crashes)
        success_3 = features_bad.crashes_last_day == 0  # Should handle gracefully
        print(f"   Result: Handled gracefully - {'✅' if success_3 else '❌'}")
        successes.append(success_3)
        
        # Test 4: Very old crashes only
        print("4. Very old crashes (no recent activity)...")
        analyzer_old = PredictiveCrashAnalyzer()
        old_time = datetime.now() - timedelta(days=30)
        for i in range(10):
            analyzer_old.add_crash({
                'timestamp': old_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'app_name': 'OldApp',
                'description': 'Old crash',
                'title': f'Old {i}'
            })
        prediction_old = analyzer_old.predict_crashes()
        success_4 = prediction_old.risk_level.value <= 3  # Should be low/medium at most
        print(f"   Result: {prediction_old.risk_level.name} - {'✅' if success_4 else '❌'}")
        successes.append(success_4)
        
        success = all(successes)
        print(f"\n✅ Edge Cases: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Edge case test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Predictive Analytics Test Suite")
    print("=" * 50)
    
    # Run tests
    test1_success = test_feature_extraction()
    test2_success = test_crash_prediction()
    test3_success = test_prediction_validation()
    test4_success = test_edge_cases()
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"📊 Final Test Results:")
    print(f"Feature Extraction: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Crash Prediction: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    print(f"Prediction Validation: {'✅ PASSED' if test3_success else '❌ FAILED'}")
    print(f"Edge Cases: {'✅ PASSED' if test4_success else '❌ FAILED'}")
    
    overall_success = all([test1_success, test2_success, test3_success, test4_success])
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '⚠️ SOME TESTS FAILED'}")
    
    if overall_success:
        print(f"\n🎯 Predictive Analytics Features Validated:")
        print("• Feature extraction from crash history")
        print("• Temporal pattern analysis and trends")
        print("• Risk scoring with multiple weighted factors")
        print("• Crash count prediction with confidence intervals")
        print("• Risk factor identification")
        print("• Actionable recommendations generation")
        print("• Prediction accuracy tracking")
        print("• Robust handling of edge cases")
    else:
        print("\nSome tests failed. Check error messages above.")
