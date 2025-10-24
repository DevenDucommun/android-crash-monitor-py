"""
Pytest configuration and shared fixtures for Android Crash Monitor tests
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_crash():
    """Single sample crash for testing"""
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
        'app_name': 'TestApp',
        'title': 'Test Crash',
        'description': 'OutOfMemoryError: Java heap space exceeded',
        'related_logs': [
            {'message': 'Low memory warning', 'level': 'WARN'},
            {'message': 'GC overhead limit exceeded', 'level': 'ERROR'}
        ]
    }


@pytest.fixture
def sample_crashes():
    """Multiple related crashes for testing"""
    current_time = datetime.now()
    crashes = []
    
    # Memory exhaustion cascade
    for i in range(3):
        crash_time = current_time + timedelta(seconds=i * 10)
        crashes.append({
            'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'app_name': 'TestApp',
            'title': f'Memory Crash {i+1}',
            'description': f'OutOfMemoryError: allocation failed attempt {i+1}',
            'related_logs': [{'message': f'Memory pressure {i+1}', 'level': 'ERROR'}]
        })
    
    return crashes


@pytest.fixture
def cascading_crashes():
    """Cascading failure scenario for testing"""
    current_time = datetime.now()
    return [
        {
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'app_name': 'AppA',
            'title': 'Root: Config Error',
            'description': 'Missing database configuration property',
            'related_logs': []
        },
        {
            'timestamp': (current_time + timedelta(seconds=2)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'app_name': 'AppA',
            'title': 'DB Connection Fail',
            'description': 'SQLiteException: unable to open database',
            'related_logs': []
        },
        {
            'timestamp': (current_time + timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'app_name': 'AppA',
            'title': 'Data Load Error',
            'description': 'NullPointerException: database connection is null',
            'related_logs': []
        }
    ]


@pytest.fixture
def diverse_crashes():
    """Diverse crash types for testing"""
    current_time = datetime.now()
    crash_types = [
        ('Memory', 'OutOfMemoryError: heap exhausted'),
        ('Database', 'SQLiteException: database corrupted'),
        ('Network', 'SocketTimeoutException: connection timeout'),
        ('UI', 'ANR: Activity not responding'),
        ('System', 'Native crash in libandroid.so')
    ]
    
    crashes = []
    for i, (crash_type, description) in enumerate(crash_types):
        crash_time = current_time + timedelta(minutes=i)
        crashes.append({
            'timestamp': crash_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'app_name': f'App{i}',
            'title': f'{crash_type} Crash',
            'description': description,
            'related_logs': []
        })
    
    return crashes


# ============================================================================
# Analyzer Fixtures
# ============================================================================

@pytest.fixture
def pattern_detector():
    """Enhanced pattern detector instance"""
    from android_crash_monitor.analysis.enhanced_pattern_detector import StatisticalPatternDetector
    return StatisticalPatternDetector()


@pytest.fixture
def realtime_analyzer():
    """Real-time pattern analyzer instance"""
    from android_crash_monitor.analysis.realtime_analyzer import RealtimePatternAnalyzer
    return RealtimePatternAnalyzer(buffer_size=100, analysis_window_minutes=15)


@pytest.fixture
def predictive_analyzer():
    """Predictive crash analyzer instance"""
    from android_crash_monitor.analysis.predictive_analytics import PredictiveCrashAnalyzer
    return PredictiveCrashAnalyzer()


@pytest.fixture
def rca_analyzer():
    """Root cause analyzer instance"""
    from android_crash_monitor.analysis.root_cause_analyzer import RootCauseAnalyzer
    return RootCauseAnalyzer()


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_log_dir(temp_dir):
    """Temporary log directory"""
    log_dir = temp_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_adb_device():
    """Mock ADB device connection"""
    class MockADBDevice:
        def __init__(self):
            self.connected = True
            self.serial = "emulator-5554"
        
        def shell(self, command):
            return f"Mock output for: {command}"
        
        def is_connected(self):
            return self.connected
    
    return MockADBDevice()


# ============================================================================
# Performance Test Utilities
# ============================================================================

@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return Timer()


# ============================================================================
# Test Helpers
# ============================================================================

def assert_crash_pattern(pattern, expected_type=None, min_confidence=0.0):
    """Helper to assert pattern properties"""
    assert pattern is not None, "Pattern should not be None"
    assert pattern.confidence_score >= min_confidence, f"Confidence {pattern.confidence_score} below threshold {min_confidence}"
    if expected_type:
        assert expected_type.lower() in pattern.name.lower(), f"Expected pattern type {expected_type} not in {pattern.name}"


def assert_prediction(prediction, expected_risk_level=None):
    """Helper to assert prediction properties"""
    assert prediction is not None, "Prediction should not be None"
    assert 0 <= prediction.risk_score <= 1, "Risk score should be between 0 and 1"
    assert 0 <= prediction.confidence <= 1, "Confidence should be between 0 and 1"
    if expected_risk_level:
        assert prediction.risk_level == expected_risk_level


def assert_rca_result(result, min_causes=0, min_evidence=0):
    """Helper to assert RCA result properties"""
    assert result is not None, "RCA result should not be None"
    assert len(result.primary_root_causes) >= min_causes, f"Expected at least {min_causes} root causes"
    assert len(result.evidence_summary) >= min_evidence, f"Expected at least {min_evidence} evidence items"
    assert result.fault_tree is not None, "Fault tree should be generated"


# Export helpers for use in tests
pytest.assert_crash_pattern = assert_crash_pattern
pytest.assert_prediction = assert_prediction
pytest.assert_rca_result = assert_rca_result


# ============================================================================
# Session-level fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_data_path():
    """Path to test data directory"""
    return Path(__file__).parent / "fixtures"
