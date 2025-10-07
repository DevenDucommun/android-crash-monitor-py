#!/usr/bin/env python3
"""
Android Crash Monitor Engine

Core monitoring functionality that:
- Monitors Android devices for crashes and errors in real-time
- Parses logcat output with intelligent pattern recognition
- Categorizes and stores detected issues
- Provides statistics and reporting
- Handles device reconnection and health monitoring
"""

import asyncio
import json
import os
import re
import signal
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, AsyncGenerator, Callable
from enum import Enum

from .adb import ADBManager, ADBError, AndroidDevice
from .config import MonitoringConfig, ConfigManager
from ..ui.console import ConsoleUI
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LogLevel(Enum):
    """Android log levels."""
    VERBOSE = "V"
    DEBUG = "D" 
    INFO = "I"
    WARNING = "W"
    ERROR = "E"
    FATAL = "F"


class CrashType(Enum):
    """Types of crashes and errors we detect."""
    ANR = "anr"  # Application Not Responding
    CRASH = "crash"  # Application crash
    NATIVE_CRASH = "native_crash"  # Native code crash
    RUNTIME_ERROR = "runtime_error"  # Runtime exceptions
    OUT_OF_MEMORY = "out_of_memory"  # OOM conditions
    PERMISSION_ERROR = "permission_error"  # Permission denied
    NETWORK_ERROR = "network_error"  # Network-related errors
    DATABASE_ERROR = "database_error"  # Database errors
    UNKNOWN = "unknown"  # Other errors


@dataclass
class LogEntry:
    """Represents a single Android log entry."""
    timestamp: str
    level: LogLevel
    tag: str
    pid: int
    tid: int
    message: str
    device_serial: str
    raw_line: str
    
    def to_dict(self) -> dict:
        return {
            **asdict(self),
            'level': self.level.value
        }


@dataclass
class CrashEvent:
    """Represents a detected crash or error event."""
    timestamp: str
    crash_type: CrashType
    app_package: Optional[str]
    app_name: Optional[str]
    severity: int  # 1-10 scale
    title: str
    description: str
    stack_trace: List[str]
    related_logs: List[LogEntry]
    device_serial: str
    device_model: Optional[str]
    
    # Metadata
    session_id: str
    detection_patterns: List[str]
    first_seen: str
    
    def to_dict(self) -> dict:
        result = asdict(self)
        result['crash_type'] = self.crash_type.value
        result['related_logs'] = [log.to_dict() for log in self.related_logs]
        return result


@dataclass
class MonitoringStats:
    """Statistics about the monitoring session."""
    session_id: str
    start_time: str
    end_time: Optional[str]
    uptime_seconds: float
    
    # Device stats
    devices_monitored: List[str]
    reconnection_count: int
    
    # Log stats
    total_logs_processed: int
    logs_per_second: float
    
    # Crash stats
    total_crashes: int
    crashes_by_type: Dict[str, int]
    crashes_by_app: Dict[str, int]
    
    # Performance
    memory_usage_mb: float
    cpu_usage_percent: float


class CrashPatterns:
    """Defines patterns for detecting different types of crashes and errors."""
    
    # ANR patterns
    ANR_PATTERNS = [
        r"ANR in (.+?) \((.+?)\)",
        r"ActivityManager.*: ANR",
        r"Application Not Responding",
        r"Input dispatching timed out"
    ]
    
    # Application crash patterns  
    CRASH_PATTERNS = [
        r"FATAL EXCEPTION",
        r"Process: (.+?), PID: (\d+)",
        r"AndroidRuntime.*: FATAL EXCEPTION",
        r"System.exit called, status: (-?\d+)"
    ]
    
    # Native crash patterns
    NATIVE_CRASH_PATTERNS = [
        r"DEBUG.*: \*\*\* FATAL EXCEPTION IN PROCESS",
        r"DEBUG.*: Build fingerprint:",
        r"DEBUG.*: Abort message:",
        r"libc.*: Fatal signal \d+",
        r"tombstoned.*: crash_dump"
    ]
    
    # Runtime error patterns
    RUNTIME_ERROR_PATTERNS = [
        r"java\.lang\.\w*Exception",
        r"java\.lang\..*Error",
        r"RuntimeException",
        r"IllegalArgumentException",
        r"NullPointerException",
        r"ClassNotFoundException"
    ]
    
    # Out of memory patterns
    OOM_PATTERNS = [
        r"OutOfMemoryError",
        r"Failed to allocate.*bytes",
        r"Low on memory",
        r"GC_.*freed.*native heap"
    ]
    
    # Permission error patterns
    PERMISSION_PATTERNS = [
        r"Permission denied",
        r"SecurityException",
        r"requires.*permission",
        r"Access denied"
    ]
    
    # Network error patterns
    NETWORK_ERROR_PATTERNS = [
        r"UnknownHostException",
        r"ConnectTimeoutException",
        r"SocketTimeoutException",
        r"No network security config specified",
        r"Unable to resolve host"
    ]
    
    # Database error patterns
    DATABASE_ERROR_PATTERNS = [
        r"SQLiteException",
        r"SQLException",
        r"Database.*corrupt",
        r"SQLiteCantOpenDatabaseException"
    ]
    
    @classmethod
    def get_all_patterns(cls) -> Dict[CrashType, List[str]]:
        """Get all crash patterns organized by type."""
        return {
            CrashType.ANR: cls.ANR_PATTERNS,
            CrashType.CRASH: cls.CRASH_PATTERNS,
            CrashType.NATIVE_CRASH: cls.NATIVE_CRASH_PATTERNS,
            CrashType.RUNTIME_ERROR: cls.RUNTIME_ERROR_PATTERNS,
            CrashType.OUT_OF_MEMORY: cls.OOM_PATTERNS,
            CrashType.PERMISSION_ERROR: cls.PERMISSION_PATTERNS,
            CrashType.NETWORK_ERROR: cls.NETWORK_ERROR_PATTERNS,
            CrashType.DATABASE_ERROR: cls.DATABASE_ERROR_PATTERNS
        }


class LogParser:
    """Parses Android logcat output into structured data."""
    
    # Logcat format: timestamp PID-TID/package priority/tag: message
    LOGCAT_PATTERN = re.compile(
        r'^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+'  # timestamp
        r'(\d+)\s+(\d+)\s+'  # PID TID
        r'([VDIWEF])\s+'     # priority
        r'([^:]+):\s*'       # tag
        r'(.*)$'             # message
    )
    
    def parse_log_line(self, line: str, device_serial: str) -> Optional[LogEntry]:
        """Parse a single logcat line into a LogEntry."""
        line = line.strip()
        if not line:
            return None
            
        match = self.LOGCAT_PATTERN.match(line)
        if not match:
            # Handle malformed lines gracefully
            return LogEntry(
                timestamp=datetime.now().strftime("%m-%d %H:%M:%S.%f")[:-3],
                level=LogLevel.INFO,
                tag="UNKNOWN",
                pid=0,
                tid=0,
                message=line,
                device_serial=device_serial,
                raw_line=line
            )
        
        timestamp, pid, tid, level, tag, message = match.groups()
        
        try:
            log_level = LogLevel(level)
        except ValueError:
            log_level = LogLevel.INFO
        
        return LogEntry(
            timestamp=timestamp,
            level=log_level,
            tag=tag.strip(),
            pid=int(pid),
            tid=int(tid),
            message=message.strip(),
            device_serial=device_serial,
            raw_line=line
        )


class CrashDetector:
    """Detects crashes and errors from parsed log entries."""
    
    def __init__(self):
        self.patterns = CrashPatterns.get_all_patterns()
        self.compiled_patterns = {}
        self._compile_patterns()
        
        # Track ongoing crash sequences
        self.active_crashes: Dict[str, CrashEvent] = {}
        self.log_buffer: List[LogEntry] = []
        self.buffer_size = 1000
        
    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        for crash_type, patterns in self.patterns.items():
            self.compiled_patterns[crash_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def detect_crashes(self, log_entry: LogEntry) -> List[CrashEvent]:
        """Detect crashes from a log entry."""
        # Add to buffer for context
        self.log_buffer.append(log_entry)
        if len(self.log_buffer) > self.buffer_size:
            self.log_buffer.pop(0)
        
        crashes = []
        
        # Check each pattern type
        for crash_type, compiled_patterns in self.compiled_patterns.items():
            for pattern in compiled_patterns:
                if pattern.search(log_entry.message):
                    crash = self._create_crash_event(
                        log_entry, crash_type, pattern.pattern
                    )
                    crashes.append(crash)
                    break  # Don't duplicate crashes of the same type
        
        return crashes
    
    def _create_crash_event(self, log_entry: LogEntry, crash_type: CrashType, 
                           pattern: str) -> CrashEvent:
        """Create a crash event from a detected log entry."""
        session_id = f"{int(time.time())}_{log_entry.device_serial}"
        
        # Extract app information
        app_package = self._extract_app_package(log_entry)
        app_name = self._extract_app_name(log_entry)
        
        # Determine severity based on crash type and log level
        severity = self._calculate_severity(crash_type, log_entry.level)
        
        # Generate title and description
        title = self._generate_crash_title(crash_type, log_entry)
        description = self._generate_crash_description(crash_type, log_entry)
        
        # Collect related logs (context around the crash)
        related_logs = self._get_related_logs(log_entry)
        
        # Extract stack trace if available
        stack_trace = self._extract_stack_trace(related_logs)
        
        return CrashEvent(
            timestamp=log_entry.timestamp,
            crash_type=crash_type,
            app_package=app_package,
            app_name=app_name,
            severity=severity,
            title=title,
            description=description,
            stack_trace=stack_trace,
            related_logs=related_logs,
            device_serial=log_entry.device_serial,
            device_model=None,  # Will be filled by monitor
            session_id=session_id,
            detection_patterns=[pattern],
            first_seen=log_entry.timestamp
        )
    
    def _extract_app_package(self, log_entry: LogEntry) -> Optional[str]:
        """Extract app package name from log entry."""
        # Try to extract from common patterns
        patterns = [
            r"Process: ([a-zA-Z0-9._]+)",
            r"Package: ([a-zA-Z0-9._]+)",
            r"([a-zA-Z0-9._]+)\s+\(pid \d+\)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_entry.message)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_app_name(self, log_entry: LogEntry) -> Optional[str]:
        """Extract app name from log entry."""
        # This would typically require additional system calls
        # For now, return the tag or package name
        app_package = self._extract_app_package(log_entry)
        if app_package:
            return app_package.split('.')[-1]  # Use last part of package name
        return log_entry.tag
    
    def _calculate_severity(self, crash_type: CrashType, log_level: LogLevel) -> int:
        """Calculate crash severity (1-10 scale)."""
        base_severity = {
            CrashType.CRASH: 9,
            CrashType.ANR: 8,
            CrashType.NATIVE_CRASH: 9,
            CrashType.OUT_OF_MEMORY: 7,
            CrashType.RUNTIME_ERROR: 6,
            CrashType.PERMISSION_ERROR: 4,
            CrashType.NETWORK_ERROR: 3,
            CrashType.DATABASE_ERROR: 5,
            CrashType.UNKNOWN: 2
        }.get(crash_type, 2)
        
        # Adjust based on log level
        level_modifier = {
            LogLevel.FATAL: 2,
            LogLevel.ERROR: 1,
            LogLevel.WARNING: 0,
            LogLevel.INFO: -1,
            LogLevel.DEBUG: -2,
            LogLevel.VERBOSE: -2
        }.get(log_level, 0)
        
        return max(1, min(10, base_severity + level_modifier))
    
    def _generate_crash_title(self, crash_type: CrashType, log_entry: LogEntry) -> str:
        """Generate a human-readable title for the crash."""
        titles = {
            CrashType.ANR: "Application Not Responding",
            CrashType.CRASH: "Application Crash", 
            CrashType.NATIVE_CRASH: "Native Code Crash",
            CrashType.RUNTIME_ERROR: "Runtime Exception",
            CrashType.OUT_OF_MEMORY: "Out of Memory Error",
            CrashType.PERMISSION_ERROR: "Permission Denied",
            CrashType.NETWORK_ERROR: "Network Connection Error",
            CrashType.DATABASE_ERROR: "Database Error",
            CrashType.UNKNOWN: "Unknown Error"
        }
        
        base_title = titles.get(crash_type, "Error")
        app_package = self._extract_app_package(log_entry)
        
        if app_package:
            return f"{base_title} in {app_package}"
        else:
            return f"{base_title} ({log_entry.tag})"
    
    def _generate_crash_description(self, crash_type: CrashType, log_entry: LogEntry) -> str:
        """Generate a detailed description of the crash."""
        return log_entry.message[:500]  # Truncate long messages
    
    def _get_related_logs(self, crash_log: LogEntry, context_lines: int = 10) -> List[LogEntry]:
        """Get related log entries around a crash for context."""
        # Find the crash log in buffer
        crash_index = -1
        for i, log in enumerate(reversed(self.log_buffer)):
            if (log.timestamp == crash_log.timestamp and 
                log.message == crash_log.message):
                crash_index = len(self.log_buffer) - 1 - i
                break
        
        if crash_index == -1:
            return [crash_log]
        
        # Get context around the crash
        start_index = max(0, crash_index - context_lines)
        end_index = min(len(self.log_buffer), crash_index + context_lines + 1)
        
        return self.log_buffer[start_index:end_index]
    
    def _extract_stack_trace(self, related_logs: List[LogEntry]) -> List[str]:
        """Extract stack trace from related logs."""
        stack_trace = []
        in_stack_trace = False
        
        for log in related_logs:
            # Look for stack trace indicators
            if any(indicator in log.message for indicator in 
                   ["at ", "Caused by:", "Exception", "Error"]):
                in_stack_trace = True
                stack_trace.append(log.message)
            elif in_stack_trace and log.message.strip().startswith("at "):
                stack_trace.append(log.message)
            elif in_stack_trace and not log.message.strip():
                # Empty line might end stack trace
                continue
            elif in_stack_trace:
                # Non-stack trace line, stop collecting
                break
        
        return stack_trace


class AndroidCrashMonitor:
    """Main monitoring engine for Android crash detection."""
    
    def __init__(self, config: MonitoringConfig, console: ConsoleUI):
        self.config = config
        self.console = console
        self.adb_manager = ADBManager()
        self.log_parser = LogParser()
        self.crash_detector = CrashDetector()
        
        # Monitoring state
        self.is_running = False
        self.session_id = f"session_{int(time.time())}"
        self.start_time = None
        self.monitored_devices: List[AndroidDevice] = []
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
        
        # Statistics
        self.stats = MonitoringStats(
            session_id=self.session_id,
            start_time="",
            end_time=None,
            uptime_seconds=0.0,
            devices_monitored=[],
            reconnection_count=0,
            total_logs_processed=0,
            logs_per_second=0.0,
            total_crashes=0,
            crashes_by_type={},
            crashes_by_app={},
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0
        )
        
        # Output configuration
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Event handlers
        self.crash_handlers: List[Callable[[CrashEvent], None]] = []
        
        # Graceful shutdown
        self.shutdown_event = asyncio.Event()
        
    def add_crash_handler(self, handler: Callable[[CrashEvent], None]):
        """Add a crash event handler."""
        self.crash_handlers.append(handler)
    
    async def start_monitoring(self, device_serials: Optional[List[str]] = None) -> None:
        """Start monitoring specified devices or all available devices."""
        if self.is_running:
            raise RuntimeError("Monitor is already running")
        
        self.start_time = datetime.now()
        self.stats.start_time = self.start_time.isoformat()
        
        try:
            # Discover devices to monitor
            await self._discover_devices(device_serials)
            
            if not self.monitored_devices:
                self.console.error("No devices available for monitoring")
                return
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            self.is_running = True
            
            # Start monitoring tasks
            tasks = []
            for device in self.monitored_devices:
                task = asyncio.create_task(self._monitor_device(device))
                tasks.append(task)
            
            # Start statistics update task
            stats_task = asyncio.create_task(self._update_stats_periodically())
            tasks.append(stats_task)
            
            # Wait for shutdown or task completion
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.console.error(f"Monitoring failed: {e}")
            logger.exception("Monitoring failed")
        finally:
            await self._cleanup()
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring gracefully."""
        if not self.is_running:
            return
        
        self.console.info("Stopping monitoring...")
        self.is_running = False
        self.shutdown_event.set()
        
        # Stop all logcat processes
        for device_serial, process in self.active_processes.items():
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            except Exception as e:
                logger.warning(f"Error stopping process for {device_serial}: {e}")
    
    async def _discover_devices(self, device_serials: Optional[List[str]] = None) -> None:
        """Discover devices to monitor."""
        all_devices = await self.adb_manager.list_devices()
        
        if device_serials:
            # Filter to requested devices
            self.monitored_devices = [
                d for d in all_devices 
                if d.serial in device_serials and d.is_online
            ]
        else:
            # Monitor all online devices
            self.monitored_devices = [d for d in all_devices if d.is_online]
        
        self.stats.devices_monitored = [d.serial for d in self.monitored_devices]
        
        # Display discovered devices  
        if self.monitored_devices:
            device_names = [d.display_name for d in self.monitored_devices]
            self.console.success(f"Monitoring: {', '.join(device_names)}")
            self.console.info("🔄 Waiting for live logs... (Press Ctrl+C to stop)")
        else:
            available_devices = [d for d in all_devices if d.is_online]
            if available_devices:
                self.console.warning("No devices match the specified criteria")
            else:
                self.console.error("No online devices found")
    
    async def _monitor_device(self, device: AndroidDevice) -> None:
        """Monitor a single device for crashes."""
        device_name = device.display_name
        
        retry_count = 0
        max_retries = 5
        
        while self.is_running and retry_count < max_retries:
            try:
                # Start logcat process - empty filters means capture all logs
                filters = self.config.default_filters if self.config.default_filters else None
                process = await self.adb_manager.start_logcat(
                    device_serial=device.serial,
                    filters=filters
                )
                
                self.active_processes[device.serial] = process
                retry_count = 0  # Reset retry count on success
                
                # Process log lines
                async for log_line in self._read_logcat_stream(process):
                    if not self.is_running:
                        break
                    
                    # Parse log line
                    log_entry = self.log_parser.parse_log_line(log_line, device.serial)
                    if not log_entry:
                        continue
                    
                    # Update statistics
                    self.stats.total_logs_processed += 1
                    
                    # Detect crashes
                    crashes = self.crash_detector.detect_crashes(log_entry)
                    for crash in crashes:
                        crash.device_model = device.model
                        await self._handle_crash(crash)
                
            except Exception as e:
                retry_count += 1
                self.stats.reconnection_count += 1
                
                # Log detailed error information for debugging
                logger.error(f"Device monitoring error for {device_name}: {type(e).__name__}: {e}")
                
                if retry_count >= max_retries:
                    self.console.error(f"Max retries reached for {device_name}: {e}")
                    break
                
                self.console.warning(
                    f"Connection lost to {device_name}. Retrying {retry_count}/{max_retries}... (Error: {type(e).__name__})"
                )
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            
            finally:
                # Clean up process
                if device.serial in self.active_processes:
                    process = self.active_processes[device.serial]
                    try:
                        process.terminate()
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except Exception:
                        try:
                            process.kill()
                            await process.wait()
                        except Exception:
                            pass
                    del self.active_processes[device.serial]
        
        # Device monitoring stopped
    
    async def _read_logcat_stream(self, process: asyncio.subprocess.Process) -> AsyncGenerator[str, None]:
        """Read lines from logcat process stream."""
        while True:
            try:
                line = await asyncio.wait_for(
                    process.stdout.readline(), 
                    timeout=1.0
                )
                
                if not line:  # EOF
                    break
                
                # Line is already bytes, decode it
                decoded_line = line.decode('utf-8', errors='replace').strip() if isinstance(line, bytes) else line.strip()
                yield decoded_line
                
            except asyncio.TimeoutError:
                # Check if process is still running
                if process.returncode is not None:
                    logger.warning(f"Logcat process died with return code: {process.returncode}")
                    break
                continue
            except Exception as e:
                logger.error(f"Error reading logcat stream: {type(e).__name__}: {e}")
                logger.error(f"Process return code: {process.returncode}")
                break
    
    async def _handle_crash(self, crash: CrashEvent) -> None:
        """Handle a detected crash event."""
        # Update statistics
        self.stats.total_crashes += 1
        
        crash_type_str = crash.crash_type.value
        self.stats.crashes_by_type[crash_type_str] = (
            self.stats.crashes_by_type.get(crash_type_str, 0) + 1
        )
        
        if crash.app_package:
            self.stats.crashes_by_app[crash.app_package] = (
                self.stats.crashes_by_app.get(crash.app_package, 0) + 1
            )
        
        # Display crash to user
        self._display_crash(crash)
        
        # Save crash to file
        await self._save_crash(crash)
        
        # Call registered handlers
        for handler in self.crash_handlers:
            try:
                handler(crash)
            except Exception as e:
                logger.warning(f"Crash handler failed: {e}")
    
    def _display_crash(self, crash: CrashEvent) -> None:
        """Display crash information to the user."""
        severity_colors = {
            (9, 10): "red",
            (7, 8): "yellow", 
            (5, 6): "blue",
            (1, 4): "dim"
        }
        
        color = "white"
        for (min_sev, max_sev), sev_color in severity_colors.items():
            if min_sev <= crash.severity <= max_sev:
                color = sev_color
                break
        
        # More concise crash display
        app_info = f" in {crash.app_package}" if crash.app_package else f" ({crash.app_name})" if crash.app_name else ""
        stack_info = f" +{len(crash.stack_trace)} stack lines" if crash.stack_trace else ""
        
        self.console.print(
            f"[{color}]🚨 {crash.crash_type.value.upper()}[/{color}] "
            f"[bold]{crash.title.split(' (')[0]}[/bold]{app_info} "
            f"(severity: {crash.severity}/10{stack_info})"
        )
    
    async def _save_crash(self, crash: CrashEvent) -> None:
        """Save crash data to file."""
        try:
            # Create filename with timestamp including milliseconds to prevent collisions
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            milliseconds = now.microsecond // 1000
            filename = f"crash_{timestamp}_{milliseconds:03d}_{crash.crash_type.value}_{crash.device_serial}.json"
            filepath = self.output_dir / filename
            
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save crash data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(crash.to_dict(), f, indent=2, default=str)
            
            # Log successful save for debugging
            logger.debug(f"Crash saved: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save crash to {filepath}: {type(e).__name__}: {e}")
            logger.error(f"Output directory exists: {self.output_dir.exists()}")
            logger.error(f"Output directory writable: {os.access(self.output_dir, os.W_OK)}")
    
    async def _update_stats_periodically(self) -> None:
        """Update monitoring statistics periodically."""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                if self.start_time:
                    self.stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
                    
                    if self.stats.uptime_seconds > 0:
                        self.stats.logs_per_second = (
                            self.stats.total_logs_processed / self.stats.uptime_seconds
                        )
                
                # Could add memory/CPU monitoring here with psutil
                
            except Exception as e:
                logger.warning(f"Stats update failed: {e}")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop_monitoring())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        self.is_running = False
        
        # Stop all processes
        for device_serial, process in list(self.active_processes.items()):
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except Exception:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
        
        self.active_processes.clear()
        
        # Finalize statistics
        if self.start_time:
            self.stats.end_time = datetime.now().isoformat()
            self.stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Save session statistics
        await self._save_session_stats()
        
        self.console.success("Monitoring stopped")
        self._display_final_stats()
    
    async def _save_session_stats(self) -> None:
        """Save session statistics to file."""
        try:
            stats_filename = f"session_stats_{self.session_id}.json"
            stats_filepath = self.output_dir / stats_filename
            
            with open(stats_filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.stats), f, indent=2, default=str)
            
            logger.info(f"Session stats saved to {stats_filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save session stats: {e}")
    
    def _display_final_stats(self) -> None:
        """Display final monitoring statistics."""
        self.console.header("Monitoring Session Summary")
        
        uptime_str = str(timedelta(seconds=int(self.stats.uptime_seconds)))
        
        self.console.info(f"Session ID: {self.stats.session_id}")
        self.console.info(f"Duration: {uptime_str}")
        self.console.info(f"Devices monitored: {len(self.stats.devices_monitored)}")
        self.console.info(f"Total logs processed: {self.stats.total_logs_processed:,}")
        self.console.info(f"Average logs/second: {self.stats.logs_per_second:.1f}")
        self.console.info(f"Reconnections: {self.stats.reconnection_count}")
        
        if self.stats.total_crashes > 0:
            self.console.warning(f"Total crashes detected: {self.stats.total_crashes}")
            
            if self.stats.crashes_by_type:
                self.console.info("Crashes by type:")
                for crash_type, count in self.stats.crashes_by_type.items():
                    self.console.info(f"  {crash_type}: {count}")
            
            if self.stats.crashes_by_app:
                self.console.info("Top crashing apps:")
                sorted_apps = sorted(
                    self.stats.crashes_by_app.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                for app, count in sorted_apps[:5]:  # Top 5
                    self.console.info(f"  {app}: {count}")
        else:
            self.console.success("No crashes detected during monitoring")


# Convenience function for CLI integration
async def start_monitoring(config: MonitoringConfig, console: ConsoleUI, 
                          device_serials: Optional[List[str]] = None) -> AndroidCrashMonitor:
    """Start monitoring with the given configuration."""
    monitor = AndroidCrashMonitor(config, console)
    await monitor.start_monitoring(device_serials)
    return monitor