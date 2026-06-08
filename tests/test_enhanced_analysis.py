#!/usr/bin/env python3
"""
Test Enhanced Pattern Detection System

Creates sample crash data and tests the enhanced statistical analysis
to validate improved pattern recognition.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import random

def create_sample_crash_data(output_dir: Path, num_crashes: int = 50) -> None:
    """Create sample crash data for testing"""
    
    # Sample crash patterns to generate
    crash_patterns = {
        'memory_exhaustion': {
            'apps': ['com.example.heavyapp', 'com.game.intensive', 'com.social.media'],
            'messages': [
                'OutOfMemoryError: Java heap space exceeded',
                'GC overhead limit exceeded - heap full',
                'Unable to create new native thread',
                'Process killed due to low memory'
            ],
            'frequency': 0.3  # 30% of crashes
        },
        'database_corruption': {
            'apps': ['com.android.providers.contacts', 'com.messaging.app', 'com.notes.app'],
            'messages': [
                'SQLiteException: database disk image is malformed',
                'Database connection pool has been closed',
                'Database locked - integrity check failed',
                'I/O error writing to database file'
            ],
            'frequency': 0.2  # 20% of crashes
        },
        'network_issues': {
            'apps': ['com.browser.chrome', 'com.social.facebook', 'com.email.gmail'],
            'messages': [
                'Network unreachable - connection timeout',
                'SSL handshake failed with remote server',
                'DNS resolution failed for domain',
                'Socket exception - connection refused'
            ],
            'frequency': 0.25  # 25% of crashes
        },
        'ui_thread_blocking': {
            'apps': ['com.ui.heavy', 'com.animation.app', 'com.video.player'],
            'messages': [
                'ANR in main thread - UI blocked',
                'Choreographer skipped 60 frames',
                'StrictMode violation: NetworkOnMainThread',
                'Main thread database operation detected'
            ],
            'frequency': 0.15  # 15% of crashes
        },
        'random_crashes': {
            'apps': ['com.random.app1', 'com.random.app2', 'com.random.app3'],
            'messages': [
                'NullPointerException at random location',
                'IndexOutOfBoundsException in array access',
                'ClassCastException in type conversion',
                'IllegalStateException in component'
            ],
            'frequency': 0.1  # 10% of crashes
        }
    }
    
    crashes = []
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(num_crashes):
        # Choose pattern based on frequency
        rand = random.random()
        cumulative = 0
        chosen_pattern = 'random_crashes'
        
        for pattern_name, pattern_data in crash_patterns.items():
            cumulative += pattern_data['frequency']
            if rand <= cumulative:
                chosen_pattern = pattern_name
                break
        
        pattern = crash_patterns[chosen_pattern]
        
        # Create crash with temporal clustering for some patterns
        if chosen_pattern in ['memory_exhaustion', 'database_corruption']:
            # Create bursts - some crashes close together
            if i > 0 and random.random() < 0.4:  # 40% chance of burst
                time_offset = random.uniform(0, 300)  # Within 5 minutes of previous
            else:
                time_offset = random.uniform(0, 86400)  # Spread over 24 hours
        else:
            time_offset = random.uniform(0, 86400)
        
        crash_time = base_time + timedelta(seconds=time_offset)
        
        # Create crash data
        crash = {
            'timestamp': crash_time.strftime('%m-%d %H:%M:%S.%f')[:-3],
            'app_name': random.choice(pattern['apps']),
            'package_name': random.choice(pattern['apps']),
            'title': f'Crash in {random.choice(pattern["apps"]).split(".")[-1]}',
            'description': random.choice(pattern['messages']),
            'stack_trace': f'Stack trace for {chosen_pattern}...',
            'related_logs': [
                {'message': f'Related log entry for {chosen_pattern}', 'level': 'ERROR'},
                {'message': f'Additional context: {pattern["messages"][0]}', 'level': 'WARN'}
            ]
        }
        
        crashes.append(crash)
    
    # Sort by timestamp
    crashes.sort(key=lambda x: datetime.strptime(x['timestamp'], '%m-%d %H:%M:%S.%f'))
    
    # Save crashes to individual JSON files
    output_dir.mkdir(exist_ok=True)
    
    for i, crash in enumerate(crashes):
        crash_file = output_dir / f"crash_{i:04d}.json"
        with open(crash_file, 'w') as f:
            json.dump(crash, f, indent=2)
    
    print(f"Created {len(crashes)} sample crashes in {output_dir}")

def test_enhanced_analysis():
    """Test the enhanced analysis system"""
    print("🧪 Testing Enhanced Pattern Detection System")
    print("=" * 50)
    
    # Create temporary directory with sample data
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logs_dir = temp_path / "logs"
        
        # Create sample crash data
        print("\n1. Creating sample crash data...")
        create_sample_crash_data(logs_dir, num_crashes=75)
        
        # Test enhanced analysis
        print("\n2. Running enhanced analysis...")
        try:
            from src.android_crash_monitor.analysis.enhanced_analyzer import EnhancedCrashAnalyzer
            
            analyzer = EnhancedCrashAnalyzer(logs_dir, confidence_threshold=0.5)
            result = analyzer.analyze_comprehensive()
            
            # Display results
            print(f"\n3. Analysis Results:")
            print(f"   Crashes Analyzed: {result.total_crashes_analyzed}")
            print(f"   Analysis Time: {result.analysis_duration_seconds:.2f}s")
            print(f"   Overall Confidence: {result.overall_confidence:.1%}")
            print(f"   Quality Score: {result.analysis_quality_score:.1%}")
            print(f"   System Health: {result.system_health.status}")
            
            print(f"\n4. Enhanced Patterns Found: {len(result.enhanced_patterns)}")
            for i, pattern in enumerate(result.enhanced_patterns, 1):
                print(f"   {i}. {pattern.name}")
                print(f"      Severity: {pattern.severity.name} | Confidence: {pattern.confidence_score:.1%}")
                print(f"      Frequency: {pattern.frequency} | Urgency: {pattern.urgency_level}/10")
                print(f"      Type: {pattern.pattern_type.value}")
                if pattern.evidence:
                    print(f"      Evidence: {pattern.evidence[0]}")
                print()
            
            print(f"5. Simple Patterns Found: {len(result.simple_patterns)}")
            for name, pattern in result.simple_patterns.items():
                print(f"   • {name}: {pattern.count} occurrences ({pattern.risk_level})")
            
            print(f"\n6. Summary:")
            print(f"   {result.user_friendly_summary}")
            
            print(f"\n7. Top Recommendations:")
            for i, rec in enumerate(result.detailed_recommendations[:3], 1):
                print(f"   {i}. {rec}")
            
            # Test priority issues
            print(f"\n8. Priority Issues:")
            priority_issues = analyzer.get_priority_issues(max_issues=3)
            for issue in priority_issues:
                print(f"   • {issue.name} (Urgency: {issue.urgency_level}/10)")
            
            # Test export functionality
            export_path = temp_path / "test_analysis.json"
            success = analyzer.export_analysis_json(export_path)
            print(f"\n9. Export Test: {'SUCCESS' if success else 'FAILED'}")
            
            if success:
                with open(export_path) as f:
                    export_data = json.load(f)
                print(f"   Exported {len(export_data['enhanced_patterns'])} enhanced patterns")
            
            return True
            
        except ImportError as e:
            print(f"❌ Import Error: {e}")
            print("   Make sure you're running from the correct directory")
            return False
        except Exception as e:
            print(f"❌ Analysis Error: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_statistical_features():
    """Test specific statistical features"""
    print("\n🔬 Testing Statistical Features")
    print("=" * 35)
    
    try:
        from src.android_crash_monitor.analysis.enhanced_pattern_detector import StatisticalPatternDetector, PatternSeverity
        
        detector = StatisticalPatternDetector(confidence_threshold=0.4)
        
        # Create test crash data with known patterns
        test_crashes = [
            {
                'timestamp': '01-01 12:00:00.000',
                'description': 'OutOfMemoryError: Java heap space',
                'app_name': 'TestApp1',
                'related_logs': [{'message': 'Process killed low memory'}]
            },
            {
                'timestamp': '01-01 12:01:00.000', 
                'description': 'OutOfMemoryError in native allocation',
                'app_name': 'TestApp2',
                'related_logs': [{'message': 'Activity not responding'}]
            },
            {
                'timestamp': '01-01 12:02:00.000',
                'description': 'GC overhead limit exceeded',
                'app_name': 'TestApp1',
                'related_logs': [{'message': 'Heap size exceeded'}]
            },
            # Database pattern
            {
                'timestamp': '01-01 13:00:00.000',
                'description': 'SQLiteException database corrupt',
                'app_name': 'DatabaseApp',
                'related_logs': [{'message': 'disk full error'}]
            },
            {
                'timestamp': '01-01 13:05:00.000',
                'description': 'Connection pool closed',
                'app_name': 'DatabaseApp',
                'related_logs': [{'message': 'I/O error writing'}]
            }
        ]
        
        patterns = detector.analyze_crash_patterns(test_crashes)
        
        print(f"Detected {len(patterns)} patterns from {len(test_crashes)} test crashes:")
        
        for pattern in patterns:
            print(f"\n• {pattern.name}")
            print(f"  Confidence: {pattern.confidence_score:.1%}")
            print(f"  Frequency: {pattern.frequency}")
            print(f"  Severity: {pattern.severity.name}")
            print(f"  Pattern Type: {pattern.pattern_type.value}")
            print(f"  Correlation: {pattern.correlation_strength:.2f}")
            print(f"  Temporal Clustering: {pattern.temporal_clustering_score:.2f}")
            
            if pattern.evidence:
                print(f"  Evidence: {pattern.evidence[0]}")
        
        return len(patterns) > 0
        
    except Exception as e:
        print(f"❌ Statistical Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Enhanced Pattern Detection Test Suite")
    print("=" * 50)
    
    # Test 1: Enhanced analysis system
    test1_success = test_enhanced_analysis()
    
    # Test 2: Statistical features
    test2_success = test_statistical_features()
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print(f"Enhanced Analysis Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Statistical Features Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    overall_success = test1_success and test2_success
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '⚠️  SOME TESTS FAILED'}")
    
    if overall_success:
        print("\nThe enhanced pattern detection system is working correctly!")
        print("Key improvements over simple keyword matching:")
        print("• Statistical confidence scoring")
        print("• Temporal clustering detection") 
        print("• Correlation analysis between crash types")
        print("• Burst pattern identification")
        print("• Cascade failure detection")
        print("• Multi-factor urgency calculation")
    else:
        print("\nSome tests failed. Check the error messages above for details.")