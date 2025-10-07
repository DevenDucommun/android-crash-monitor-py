#!/usr/bin/env python3
"""
Base Export Classes

Provides the base interface and common functionality for all export formats.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import json

from ..core.monitor import CrashEvent, MonitoringStats, LogEntry


class ExportError(Exception):
    """Exception raised during export operations."""
    pass


class ExportData:
    """Container for data to be exported."""
    
    def __init__(self):
        self.crashes: List[CrashEvent] = []
        self.stats: Optional[MonitoringStats] = None
        self.logs: List[LogEntry] = []
        self.metadata: Dict[str, Any] = {}
        
    def add_crash(self, crash: CrashEvent):
        """Add a crash event to export."""
        self.crashes.append(crash)
    
    def add_crashes(self, crashes: List[CrashEvent]):
        """Add multiple crash events to export."""
        self.crashes.extend(crashes)
    
    def set_stats(self, stats: MonitoringStats):
        """Set monitoring statistics."""
        self.stats = stats
    
    def add_logs(self, logs: List[LogEntry]):
        """Add log entries to export."""
        self.logs.extend(logs)
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to export."""
        self.metadata[key] = value


class BaseExporter(ABC):
    """Base class for all exporters."""
    
    def __init__(self):
        self.export_timestamp = datetime.now()
    
    @abstractmethod
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data to the specified path."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Get the file extension for this export format."""
        pass
    
    @property  
    @abstractmethod
    def format_name(self) -> str:
        """Get the human-readable format name."""
        pass
    
    def generate_filename(self, base_name: str = "crash_report") -> str:
        """Generate a filename with timestamp and extension."""
        timestamp = self.export_timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{self.file_extension}"
    
    def _prepare_crash_data(self, crashes: List[CrashEvent]) -> List[Dict[str, Any]]:
        """Convert crash events to exportable format."""
        return [crash.to_dict() for crash in crashes]
    
    def _prepare_stats_data(self, stats: MonitoringStats) -> Dict[str, Any]:
        """Convert monitoring stats to exportable format."""
        if not stats:
            return {}
        
        from dataclasses import asdict
        return asdict(stats)
    
    def _prepare_logs_data(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Convert log entries to exportable format."""
        return [log.to_dict() for log in logs]
    
    def _validate_output_path(self, output_path: Path) -> None:
        """Validate and create output directory if needed."""
        if output_path.is_dir():
            raise ExportError(f"Output path is a directory: {output_path}")
        
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists and is writable
        if output_path.exists():
            if not output_path.is_file():
                raise ExportError(f"Output path exists but is not a file: {output_path}")
            
            try:
                # Test if we can write to the file
                with open(output_path, 'a') as f:
                    pass
            except PermissionError:
                raise ExportError(f"Permission denied: cannot write to {output_path}")
    
    def _create_export_metadata(self, data: ExportData) -> Dict[str, Any]:
        """Create metadata for the export."""
        metadata = {
            "export_timestamp": self.export_timestamp.isoformat(),
            "export_format": self.format_name,
            "exporter_version": "1.0.0",
            "crash_count": len(data.crashes),
            "log_count": len(data.logs),
            "has_statistics": data.stats is not None
        }
        
        # Add custom metadata
        metadata.update(data.metadata)
        
        return metadata


class MultiFormatExporter:
    """Utility class for exporting to multiple formats simultaneously."""
    
    def __init__(self):
        self.exporters: Dict[str, BaseExporter] = {}
    
    def add_format(self, format_name: str, exporter: BaseExporter):
        """Add an exporter for a specific format."""
        self.exporters[format_name] = exporter
    
    def export_all(self, data: ExportData, base_path: Path, 
                   base_name: str = "crash_report") -> Dict[str, Path]:
        """Export data to all registered formats."""
        results = {}
        
        for format_name, exporter in self.exporters.items():
            try:
                filename = exporter.generate_filename(base_name)
                output_path = base_path / filename
                
                exporter.export(data, output_path)
                results[format_name] = output_path
                
            except Exception as e:
                raise ExportError(f"Failed to export {format_name}: {e}")
        
        return results


def load_crashes_from_files(crash_files: List[Path]) -> List[CrashEvent]:
    """Load crash events from JSON files."""
    crashes = []
    
    for crash_file in crash_files:
        try:
            with open(crash_file, 'r', encoding='utf-8') as f:
                crash_data = json.load(f)
            
            # Convert back to CrashEvent
            # This is a simplified version - full implementation would need
            # proper deserialization of all nested objects
            crashes.append(crash_data)
            
        except Exception as e:
            raise ExportError(f"Failed to load crash from {crash_file}: {e}")
    
    return crashes


def find_crash_files(directory: Path, pattern: str = "crash_*.json") -> List[Path]:
    """Find crash files in a directory."""
    if not directory.exists():
        return []
    
    return list(directory.glob(pattern))


def load_session_stats(stats_file: Path) -> Optional[MonitoringStats]:
    """Load session statistics from a file."""
    if not stats_file.exists():
        return None
    
    try:
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats_data = json.load(f)
        
        # Convert back to MonitoringStats
        # This would need proper deserialization in full implementation
        return stats_data
        
    except Exception as e:
        raise ExportError(f"Failed to load session stats from {stats_file}: {e}")