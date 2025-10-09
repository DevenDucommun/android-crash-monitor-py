#!/usr/bin/env python3
"""
Enhanced Crash Patterns for System.err Monitoring
==================================================

This module extends the base crash detection patterns with specific
patterns identified from the System.err crash analysis, focusing on:

- HLS streaming manifest errors
- Video codec failures  
- Broadcast receiver management issues
- Hardware acceleration problems
- Media pipeline errors
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


class EnhancedCrashType(Enum):
    """Enhanced crash types for System.err specific errors."""
    HLS_STREAMING_ERROR = "hls_streaming_error"
    VIDEO_CODEC_ERROR = "video_codec_error" 
    RECEIVER_REGISTRATION_ERROR = "receiver_registration_error"
    MEDIA_PIPELINE_ERROR = "media_pipeline_error"
    HARDWARE_ACCELERATION_ERROR = "hardware_acceleration_error"
    MANIFEST_VALIDATION_ERROR = "manifest_validation_error"


@dataclass
class PatternMatch:
    """Result of pattern matching with metadata."""
    crash_type: EnhancedCrashType
    pattern: str
    confidence: float  # 0.0 - 1.0
    severity_override: Optional[int] = None
    additional_context: Optional[Dict[str, str]] = None


class SystemErrPatterns:
    """System.err specific crash patterns based on analysis."""
    
    # HLS Streaming Error Patterns
    HLS_STREAMING_PATTERNS = [
        # Primary pattern from analysis
        r"Invalid HLS manifest: does not start with #EXTM3U",
        
        # Related HLS streaming issues
        r"HLS.*manifest.*invalid",
        r"HLS.*parsing.*failed",
        r"#EXTM3U.*not found",
        r"M3U8.*format.*error",
        r"HLS.*stream.*unavailable",
        r"Invalid.*playlist.*format",
        r"Manifest.*download.*failed",
        r"HLS.*segment.*error"
    ]
    
    # Video Codec Error Patterns
    VIDEO_CODEC_PATTERNS = [
        # From crash analysis - VP9 codec issues
        r"ExynosC2Vp9DecComponent.*error",
        r"ExynosC2Vp9DecComponent.*failed",
        r"ExynosC2Vp9DecComponent.*release",
        
        # General codec errors
        r"CCodecBuffers.*error",
        r"MediaCodec.*failed",
        r"VideoDecoder.*error",
        r"Codec.*initialization.*failed",
        r"Hardware.*decoder.*error",
        r"Video.*encoding.*failed",
        r"Codec2.*error",
        r"C2.*Buffer.*error"
    ]
    
    # Receiver Registration Error Patterns  
    RECEIVER_REGISTRATION_PATTERNS = [
        # Primary pattern from analysis
        r"Receiver not registered: r8\.[a-zA-Z0-9$@]+",
        
        # Related receiver issues
        r"Receiver.*not.*registered",
        r"BroadcastReceiver.*unregistered",
        r"IllegalArgumentException.*Receiver",
        r"Cannot.*unregister.*receiver",
        r"Receiver.*already.*unregistered",
        r"registerReceiver.*failed",
        r"unregisterReceiver.*failed"
    ]
    
    # Media Pipeline Error Patterns
    MEDIA_PIPELINE_PATTERNS = [
        # From related crash logs
        r"Media.*playback.*stopped",
        r"SurfaceUtils.*disconnecting.*surface",
        r"deallocate.*not.*successful",
        r"AHwb.*destruction.*notifying.*failure",
        
        # General media pipeline issues
        r"MediaPlayer.*error",
        r"AudioTrack.*error",
        r"MediaSession.*error",
        r"ExoPlayer.*error",
        r"Surface.*error",
        r"MediaExtractor.*error"
    ]
    
    # Hardware Acceleration Error Patterns
    HARDWARE_ACCELERATION_PATTERNS = [
        # Hardware buffer and graphic issues
        r"C2IgbaBuffer.*error",
        r"Codec2-GraphicBufferAllocator.*deallocate.*not.*successful",
        r"Hardware.*acceleration.*failed",
        r"GPU.*memory.*allocation.*failed",
        r"OpenGL.*error",
        r"Vulkan.*error",
        r"Graphics.*buffer.*error"
    ]
    
    # Manifest Validation Patterns (more general)
    MANIFEST_VALIDATION_PATTERNS = [
        r"Manifest.*validation.*failed",
        r"Invalid.*media.*manifest",
        r"Playlist.*parsing.*error",
        r"Media.*format.*unsupported",
        r"Unsupported.*media.*type"
    ]


class CascadeDetector:
    """Detects cascade failure patterns in crash sequences."""
    
    def __init__(self, window_seconds: int = 5, threshold_count: int = 3):
        self.window_seconds = window_seconds
        self.threshold_count = threshold_count
        self.recent_crashes: List[Tuple[float, str]] = []  # (timestamp, crash_type)
    
    def add_crash(self, timestamp: float, crash_type: str) -> bool:
        """Add a crash and check if it triggers cascade detection."""
        # Add to recent crashes
        self.recent_crashes.append((timestamp, crash_type))
        
        # Clean old entries outside the window
        cutoff_time = timestamp - self.window_seconds
        self.recent_crashes = [
            (ts, ct) for ts, ct in self.recent_crashes 
            if ts >= cutoff_time
        ]
        
        # Check if we have a cascade
        return len(self.recent_crashes) >= self.threshold_count
    
    def get_cascade_info(self) -> Dict[str, any]:
        """Get information about the current cascade."""
        if len(self.recent_crashes) < self.threshold_count:
            return {}
        
        crash_types = [ct for _, ct in self.recent_crashes]
        unique_types = set(crash_types)
        
        return {
            "total_crashes": len(self.recent_crashes),
            "unique_types": len(unique_types),
            "crash_types": list(unique_types),
            "time_window": self.window_seconds,
            "dominant_type": max(crash_types, key=crash_types.count) if crash_types else None
        }


class EnhancedCrashPatterns:
    """Enhanced crash pattern detection with System.err specific patterns."""
    
    def __init__(self):
        self.compiled_patterns = self._compile_patterns()
        self.cascade_detector = CascadeDetector()
    
    def _compile_patterns(self) -> Dict[EnhancedCrashType, List[re.Pattern]]:
        """Compile all enhanced patterns for performance."""
        patterns = {
            EnhancedCrashType.HLS_STREAMING_ERROR: SystemErrPatterns.HLS_STREAMING_PATTERNS,
            EnhancedCrashType.VIDEO_CODEC_ERROR: SystemErrPatterns.VIDEO_CODEC_PATTERNS,
            EnhancedCrashType.RECEIVER_REGISTRATION_ERROR: SystemErrPatterns.RECEIVER_REGISTRATION_PATTERNS,
            EnhancedCrashType.MEDIA_PIPELINE_ERROR: SystemErrPatterns.MEDIA_PIPELINE_PATTERNS,
            EnhancedCrashType.HARDWARE_ACCELERATION_ERROR: SystemErrPatterns.HARDWARE_ACCELERATION_PATTERNS,
            EnhancedCrashType.MANIFEST_VALIDATION_ERROR: SystemErrPatterns.MANIFEST_VALIDATION_PATTERNS,
        }
        
        compiled = {}
        for crash_type, pattern_list in patterns.items():
            compiled[crash_type] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in pattern_list
            ]
        
        return compiled
    
    def detect_enhanced_crashes(self, message: str, tag: str = "", 
                              timestamp: float = 0.0) -> List[PatternMatch]:
        """Detect enhanced crash patterns in a log message."""
        matches = []
        
        # Check each enhanced pattern type
        for crash_type, compiled_patterns in self.compiled_patterns.items():
            for pattern in compiled_patterns:
                if pattern.search(message):
                    confidence = self._calculate_confidence(
                        crash_type, message, tag
                    )
                    severity = self._get_severity_override(crash_type, message)
                    context = self._extract_context(crash_type, message, tag)
                    
                    match = PatternMatch(
                        crash_type=crash_type,
                        pattern=pattern.pattern,
                        confidence=confidence,
                        severity_override=severity,
                        additional_context=context
                    )
                    matches.append(match)
                    break  # Don't duplicate same type
        
        # Check for cascade patterns if we have matches
        if matches and timestamp > 0:
            for match in matches:
                is_cascade = self.cascade_detector.add_crash(
                    timestamp, match.crash_type.value
                )
                if is_cascade:
                    cascade_info = self.cascade_detector.get_cascade_info()
                    if match.additional_context is None:
                        match.additional_context = {}
                    match.additional_context["cascade_detected"] = cascade_info
                    # Increase severity for cascade failures
                    if match.severity_override:
                        match.severity_override = min(10, match.severity_override + 2)
                    else:
                        match.severity_override = 8
        
        return matches
    
    def _calculate_confidence(self, crash_type: EnhancedCrashType, 
                            message: str, tag: str) -> float:
        """Calculate confidence level for pattern match."""
        base_confidence = 0.8
        
        # Increase confidence for specific conditions
        if crash_type == EnhancedCrashType.HLS_STREAMING_ERROR:
            if "System.err" in tag:
                base_confidence += 0.1
            if "#EXTM3U" in message:
                base_confidence += 0.1
        
        elif crash_type == EnhancedCrashType.RECEIVER_REGISTRATION_ERROR:
            if "System.err" in tag and "r8." in message:
                base_confidence += 0.15
        
        elif crash_type == EnhancedCrashType.VIDEO_CODEC_ERROR:
            if any(codec in message.lower() for codec in ["vp9", "h264", "hevc"]):
                base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _get_severity_override(self, crash_type: EnhancedCrashType, 
                             message: str) -> Optional[int]:
        """Get severity override for specific crash types."""
        severity_map = {
            # High severity for streaming failures as they affect user experience
            EnhancedCrashType.HLS_STREAMING_ERROR: 7,
            
            # Medium-high for codec errors as they can cascade
            EnhancedCrashType.VIDEO_CODEC_ERROR: 6,
            
            # Medium for receiver issues - usually app-specific
            EnhancedCrashType.RECEIVER_REGISTRATION_ERROR: 5,
            
            # Medium for media pipeline issues
            EnhancedCrashType.MEDIA_PIPELINE_ERROR: 5,
            
            # High for hardware acceleration as it affects performance
            EnhancedCrashType.HARDWARE_ACCELERATION_ERROR: 7,
            
            # Medium for manifest validation
            EnhancedCrashType.MANIFEST_VALIDATION_ERROR: 6,
        }
        
        return severity_map.get(crash_type)
    
    def _extract_context(self, crash_type: EnhancedCrashType, 
                        message: str, tag: str) -> Dict[str, str]:
        """Extract additional context from crash messages."""
        context = {
            "crash_category": "system_err_enhanced",
            "detection_tag": tag
        }
        
        # Extract specific context based on crash type
        if crash_type == EnhancedCrashType.HLS_STREAMING_ERROR:
            context["error_category"] = "media_streaming"
            context["streaming_protocol"] = "HLS"
            if "aloha" in message.lower():
                context["likely_app"] = "com.aloha.browser"
        
        elif crash_type == EnhancedCrashType.RECEIVER_REGISTRATION_ERROR:
            # Extract receiver class if available
            receiver_match = re.search(r"r8\.([a-zA-Z0-9$@]+)", message)
            if receiver_match:
                context["receiver_class"] = receiver_match.group(1)
        
        elif crash_type == EnhancedCrashType.VIDEO_CODEC_ERROR:
            # Extract codec type
            codec_patterns = {
                "VP9": "vp9",
                "H264": "h264",
                "HEVC": "hevc",
                "AV1": "av1"
            }
            for codec_name, pattern in codec_patterns.items():
                if pattern in message.lower():
                    context["codec_type"] = codec_name
                    break
        
        return context
    
    def get_pattern_stats(self) -> Dict[str, int]:
        """Get statistics about pattern matching."""
        return {
            "cascade_window_seconds": self.cascade_detector.window_seconds,
            "cascade_threshold": self.cascade_detector.threshold_count,
            "recent_crashes_count": len(self.cascade_detector.recent_crashes),
            "total_pattern_types": len(self.compiled_patterns)
        }