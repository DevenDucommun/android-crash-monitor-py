#!/usr/bin/env python3
"""
Test Root Cause Analysis System

Tests the RCA engine including dependency analysis, fault trees, and causal inference
"""

from datetime import datetime, timedelta


def test_dependency_analysis():
    """Test crash dependency detection"""
    print("🔍 Testing Dependency Analysis")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.root_cause_analyzer import (
            DependencyAnalyzer, ComponentType
        )
        
        analyzer = DependencyAnalyzer()
        
        # Create cascading crash scenario
        current_time = datetime.now()
        crashes = [
            {
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Memory Exhaustion',
                'app_name': 'HeavyApp',
                'description': 'OutOfMemoryError: Java heap space exceeded. GC overhead limit'
            },
            {
                'timestamp': (current_time + timedelta(seconds=10)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Database Timeout',
                'app_name': 'HeavyApp',
                'description': 'SQLiteException: database connection timeout waiting for memory'
            },
            {
                'timestamp': (current_time + timedelta(seconds=15)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'UI Thread Blocked',
                'app_name': 'HeavyApp',
                'description': 'ANR: Activity not responding, UI thread blocked'
            }
        ]
        
        # Analyze dependencies
        dependencies, components = analyzer.analyze_dependencies(crashes)
        
        print(f"\n📊 Analysis Results:")
        print(f"  Crashes analyzed: {len(crashes)}")
        print(f"  Dependencies found: {len(dependencies)}")
        print(f"  Components affected: {len(components)}")
        
        print(f"\n🔗 Dependencies:")
        for dep in dependencies:
            print(f"  • {dep.source_crash_id} → {dep.target_crash_id}")
            print(f"    Type: {dep.dependency_type}, Confidence: {dep.confidence:.1%}")
            print(f"    Time delta: {dep.time_delta:.1f}s")
            if dep.evidence:
                print(f"    Evidence: {dep.evidence[0]}")
        
        print(f"\n🏥 Component Health:")
        for comp_name, comp in components.items():
            print(f"  • {comp_name} ({comp.component_type.value})")
            print(f"    Health: {comp.health_score:.1%}, Failures: {comp.failure_count}")
        
        # Validation
        success_criteria = [
            len(dependencies) > 0,  # Should find at least one dependency
            len(components) > 0,    # Should identify components
            any(d.confidence > 0.5 for d in dependencies),  # At least one high-confidence dep
            any(c.health_score < 1.0 for c in components.values())  # Some components unhealthy
        ]
        
        success = all(success_criteria)
        print(f"\n✅ Dependency Analysis: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Dependency analysis test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fault_tree_analysis():
    """Test fault tree construction"""
    print("\n🌳 Testing Fault Tree Analysis")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.root_cause_analyzer import (
            FaultTreeAnalyzer, DependencyAnalyzer, FailureMode
        )
        
        # Create diverse crash scenarios
        current_time = datetime.now()
        crashes = [
            {
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Memory Leak 1',
                'description': 'OutOfMemoryError: heap memory leak detected'
            },
            {
                'timestamp': (current_time + timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Memory Leak 2',
                'description': 'OutOfMemoryError: allocation failed'
            },
            {
                'timestamp': (current_time + timedelta(seconds=20)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Database Corruption',
                'description': 'SQLiteException: database disk image is malformed'
            },
            {
                'timestamp': (current_time + timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Network Timeout',
                'description': 'SocketTimeoutException: connection timeout'
            }
        ]
        
        # Analyze dependencies first
        dep_analyzer = DependencyAnalyzer()
        dependencies, components = dep_analyzer.analyze_dependencies(crashes)
        
        # Build fault tree
        tree_analyzer = FaultTreeAnalyzer()
        fault_tree = tree_analyzer.build_fault_tree(crashes, dependencies, components)
        
        print(f"\n🌳 Fault Tree Structure:")
        print(f"  Root event: {fault_tree.event}")
        print(f"  Gate type: {fault_tree.gate_type}")
        print(f"  Probability: {fault_tree.probability:.1%}")
        print(f"  Child nodes: {len(fault_tree.children)}")
        
        print(f"\n📊 Failure Modes:")
        for child in fault_tree.children:
            print(f"  • {child.event}")
            print(f"    Gate: {child.gate_type}, P={child.probability:.2%}")
            print(f"    Basic events: {len(child.children)}")
            if child.children:
                for basic in child.children[:2]:  # Show first 2
                    print(f"      - {basic.event}")
        
        # Validation
        success_criteria = [
            fault_tree is not None,
            len(fault_tree.children) > 0,  # Should have intermediate nodes
            fault_tree.probability > 0,     # Should calculate probability
            fault_tree.event_type == "root"
        ]
        
        success = all(success_criteria)
        print(f"\n✅ Fault Tree Analysis: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Fault tree test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_causal_inference():
    """Test causal chain inference"""
    print("\n🔗 Testing Causal Inference")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.root_cause_analyzer import (
            CausalInferenceEngine, DependencyAnalyzer
        )
        
        # Create clear causal chain
        current_time = datetime.now()
        crashes = [
            {
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Root: Memory Leak',
                'app_name': 'TestApp',
                'description': 'Memory leak in image loading library causing heap growth'
            },
            {
                'timestamp': (current_time + timedelta(seconds=10)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Consequence: OOM',
                'app_name': 'TestApp',
                'description': 'OutOfMemoryError: Failed to allocate memory for bitmap'
            },
            {
                'timestamp': (current_time + timedelta(seconds=12)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Final: Activity Crash',
                'app_name': 'TestApp',
                'description': 'ActivityThread: Unable to create activity due to memory'
            }
        ]
        
        # Analyze dependencies
        dep_analyzer = DependencyAnalyzer()
        dependencies, components = dep_analyzer.analyze_dependencies(crashes)
        
        # Infer causal chains
        causal_engine = CausalInferenceEngine()
        chains = causal_engine.infer_causal_chains(crashes, dependencies, components)
        
        print(f"\n🔗 Causal Chains Found: {len(chains)}")
        
        for i, chain in enumerate(chains, 1):
            print(f"\n  Chain {i}: {chain.chain_id}")
            print(f"  Root cause: {chain.root_cause}")
            print(f"  Confidence: {chain.confidence:.1%}")
            if chain.failure_mode:
                print(f"  Failure mode: {chain.failure_mode.value}")
            print(f"  Events ({len(chain.events)}):")
            
            for event in chain.events:
                role = event.get('role', 'unknown')
                crash_id = event.get('crash_id', 'unknown')
                print(f"    {role.upper()}: {crash_id}")
                if 'dependency_type' in event:
                    print(f"      ({event['dependency_type']}, conf={event.get('confidence', 0):.1%})")
        
        # Validation
        success_criteria = [
            len(chains) > 0,  # Should find at least one chain
            any(len(c.events) > 1 for c in chains),  # At least one multi-event chain
            any(c.confidence > 0 for c in chains)    # Should have confidence scores
        ]
        
        success = all(success_criteria)
        print(f"\n✅ Causal Inference: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Causal inference test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_rca():
    """Test complete root cause analysis"""
    print("\n🎯 Testing Complete RCA")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.root_cause_analyzer import RootCauseAnalyzer
        
        # Create realistic crash scenario
        current_time = datetime.now()
        crashes = [
            {
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Config Error',
                'app_name': 'ProductionApp',
                'description': 'Missing database configuration property at startup'
            },
            {
                'timestamp': (current_time + timedelta(seconds=2)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'DB Connection Fail',
                'app_name': 'ProductionApp',
                'description': 'SQLiteException: unable to open database file'
            },
            {
                'timestamp': (current_time + timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Data Load Error',
                'app_name': 'ProductionApp',
                'description': 'NullPointerException: database connection is null'
            },
            {
                'timestamp': (current_time + timedelta(seconds=8)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'UI Crash',
                'app_name': 'ProductionApp',
                'description': 'RuntimeException: Cannot display data - data source unavailable'
            },
            # Add unrelated crash for noise
            {
                'timestamp': (current_time + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': 'Unrelated Network Issue',
                'app_name': 'OtherApp',
                'description': 'Network timeout connecting to API'
            }
        ]
        
        # Run full RCA
        analyzer = RootCauseAnalyzer()
        result = analyzer.analyze(crashes)
        
        print(f"\n📊 RCA Results:")
        print(f"  Analysis ID: {result.analysis_id}")
        print(f"  Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Overall confidence: {result.overall_confidence:.1%}")
        
        print(f"\n🎯 Primary Root Causes ({len(result.primary_root_causes)}):")
        for cause in result.primary_root_causes:
            print(f"  • {cause['cause']}")
            print(f"    Confidence: {cause['confidence']:.1%}")
            print(f"    Frequency: {cause['frequency']}")
            print(f"    Description: {cause['description'][:60]}...")
        
        print(f"\n⚠️  Contributing Factors ({len(result.contributing_factors)}):")
        for factor in result.contributing_factors[:3]:
            print(f"  • {factor['factor']} ({factor['component_type']})")
            print(f"    Health: {factor['health_score']:.1%}, Failures: {factor['failure_count']}")
        
        print(f"\n🔗 Dependencies: {len(result.crash_dependencies)}")
        for dep in result.crash_dependencies[:3]:
            print(f"  • {dep.source_crash_id} → {dep.target_crash_id} ({dep.confidence:.1%})")
        
        print(f"\n🌳 Fault Tree:")
        if result.fault_tree:
            print(f"  Root: {result.fault_tree.event} (P={result.fault_tree.probability:.2%})")
            print(f"  Failure modes: {len(result.fault_tree.children)}")
        
        print(f"\n🔗 Causal Chains: {len(result.causal_chains)}")
        for chain in result.causal_chains[:2]:
            print(f"  • {chain.chain_id}: {len(chain.events)} events, conf={chain.confidence:.1%}")
        
        print(f"\n📋 Evidence:")
        for evidence in result.evidence_summary:
            print(f"  • {evidence}")
        
        print(f"\n🔧 Remediation Steps:")
        for i, step in enumerate(result.remediation_steps, 1):
            print(f"  {i}. {step}")
        
        print(f"\n🛡️  Prevention Measures:")
        for i, measure in enumerate(result.prevention_measures, 1):
            print(f"  {i}. {measure}")
        
        # Validation
        success_criteria = [
            len(result.primary_root_causes) > 0 or len(result.contributing_factors) > 0,
            result.overall_confidence >= 0,
            len(result.remediation_steps) > 0,
            len(result.prevention_measures) > 0,
            result.fault_tree is not None
        ]
        
        success = all(success_criteria)
        print(f"\n✅ Complete RCA: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ RCA test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test RCA edge cases"""
    print("\n🔧 Testing Edge Cases")
    print("=" * 50)
    
    try:
        from src.android_crash_monitor.analysis.root_cause_analyzer import RootCauseAnalyzer
        
        successes = []
        
        # Test 1: Empty crash list
        print("1. Empty crash list...")
        analyzer = RootCauseAnalyzer()
        result_empty = analyzer.analyze([])
        success_1 = (result_empty is not None and 
                     len(result_empty.primary_root_causes) == 0)
        print(f"   Result: {'✅' if success_1 else '❌'}")
        successes.append(success_1)
        
        # Test 2: Single crash
        print("2. Single crash (no dependencies)...")
        single_crash = [{
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'title': 'Solo Crash',
            'description': 'Single isolated crash event'
        }]
        result_single = analyzer.analyze(single_crash)
        success_2 = result_single is not None
        print(f"   Result: Analyzed successfully - {'✅' if success_2 else '❌'}")
        successes.append(success_2)
        
        # Test 3: Crashes without timestamps
        print("3. Crashes with missing timestamps...")
        no_time_crashes = [
            {'title': 'Crash 1', 'description': 'Test crash 1'},
            {'title': 'Crash 2', 'description': 'Test crash 2'}
        ]
        result_notime = analyzer.analyze(no_time_crashes)
        success_3 = result_notime is not None  # Should handle gracefully
        print(f"   Result: Handled gracefully - {'✅' if success_3 else '❌'}")
        successes.append(success_3)
        
        # Test 4: Widely spaced crashes (no dependencies expected)
        print("4. Widely spaced crashes...")
        base_time = datetime.now()
        spaced_crashes = [
            {
                'timestamp': (base_time - timedelta(hours=i)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'title': f'Crash {i}',
                'description': f'Crash number {i}'
            }
            for i in range(5)
        ]
        result_spaced = analyzer.analyze(spaced_crashes)
        # Should find few or no dependencies
        success_4 = (result_spaced is not None and 
                     len(result_spaced.crash_dependencies) < len(spaced_crashes))
        print(f"   Result: {len(result_spaced.crash_dependencies)} deps (expected few) - {'✅' if success_4 else '❌'}")
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
    print("🚀 Root Cause Analysis Test Suite")
    print("=" * 50)
    
    # Run tests
    test1_success = test_dependency_analysis()
    test2_success = test_fault_tree_analysis()
    test3_success = test_causal_inference()
    test4_success = test_full_rca()
    test5_success = test_edge_cases()
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"📊 Final Test Results:")
    print(f"Dependency Analysis: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Fault Tree Analysis: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    print(f"Causal Inference: {'✅ PASSED' if test3_success else '❌ FAILED'}")
    print(f"Complete RCA: {'✅ PASSED' if test4_success else '❌ FAILED'}")
    print(f"Edge Cases: {'✅ PASSED' if test5_success else '❌ FAILED'}")
    
    overall_success = all([test1_success, test2_success, test3_success, test4_success, test5_success])
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '⚠️ SOME TESTS FAILED'}")
    
    if overall_success:
        print(f"\n🎯 RCA Features Validated:")
        print("• Crash dependency tracking and cascading failure detection")
        print("• Component health assessment")
        print("• Fault tree construction with probability analysis")
        print("• Causal chain inference with confidence scoring")
        print("• Root cause identification from complex crash patterns")
        print("• Evidence compilation and analysis confidence")
        print("• Actionable remediation and prevention recommendations")
        print("• Robust handling of edge cases")
    else:
        print("\nSome tests failed. Check error messages above.")
