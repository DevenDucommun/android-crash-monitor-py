#!/usr/bin/env python3
"""
JSON Exporter

Exports crash reports and monitoring data to JSON format with proper structure
and formatting for both human readability and machine processing.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base import BaseExporter, ExportData, ExportError


class JSONExporter(BaseExporter):
    """Exports data to JSON format."""
    
    @property
    def file_extension(self) -> str:
        return "json"
    
    @property
    def format_name(self) -> str:
        return "JSON"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data to JSON file."""
        self._validate_output_path(output_path)
        
        # Get formatting options
        pretty_print = kwargs.get('pretty_print', True)
        include_metadata = kwargs.get('include_metadata', True)
        include_raw_logs = kwargs.get('include_raw_logs', False)
        
        # Build the JSON structure
        json_data = self._build_json_structure(data, include_metadata, include_raw_logs)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    json.dump(json_data, f, ensure_ascii=False, default=str)
                    
        except Exception as e:
            raise ExportError(f"Failed to write JSON file: {e}")
    
    def _build_json_structure(self, data: ExportData, include_metadata: bool = True, 
                            include_raw_logs: bool = False) -> Dict[str, Any]:
        """Build the complete JSON structure."""
        json_data = {}
        
        # Add metadata
        if include_metadata:
            json_data["metadata"] = self._create_export_metadata(data)
        
        # Add crash summary
        json_data["summary"] = self._create_crash_summary(data)
        
        # Add crashes
        if data.crashes:
            json_data["crashes"] = self._prepare_crash_data(data.crashes)
        
        # Add statistics
        if data.stats:
            json_data["statistics"] = self._prepare_stats_data(data.stats)
        
        # Add logs (optional, can make files very large)
        if include_raw_logs and data.logs:
            json_data["logs"] = self._prepare_logs_data(data.logs)
        
        return json_data
    
    def _create_crash_summary(self, data: ExportData) -> Dict[str, Any]:
        """Create a summary of crashes for quick overview."""
        if not data.crashes:
            return {
                "total_crashes": 0,
                "crash_types": {},
                "severity_distribution": {},
                "apps_affected": {},
                "devices_affected": {},
                "time_range": None
            }
        
        # Count crashes by type
        crash_types = {}
        severity_dist = {}
        apps_affected = {}
        devices_affected = {}
        
        timestamps = []
        
        for crash in data.crashes:
            # Count by crash type
            crash_type = crash.crash_type.value
            crash_types[crash_type] = crash_types.get(crash_type, 0) + 1
            
            # Count by severity
            severity = crash.severity
            sev_range = self._get_severity_range(severity)
            severity_dist[sev_range] = severity_dist.get(sev_range, 0) + 1
            
            # Count by app
            if crash.app_package:
                apps_affected[crash.app_package] = apps_affected.get(crash.app_package, 0) + 1
            
            # Count by device
            device_key = f"{crash.device_serial}"
            if crash.device_model:
                device_key += f" ({crash.device_model})"
            devices_affected[device_key] = devices_affected.get(device_key, 0) + 1
            
            # Collect timestamps
            timestamps.append(crash.timestamp)
        
        # Determine time range
        time_range = None
        if timestamps:
            timestamps.sort()
            time_range = {
                "start": timestamps[0],
                "end": timestamps[-1],
                "duration_minutes": self._calculate_duration(timestamps[0], timestamps[-1])
            }
        
        return {
            "total_crashes": len(data.crashes),
            "crash_types": dict(sorted(crash_types.items(), key=lambda x: x[1], reverse=True)),
            "severity_distribution": severity_dist,
            "apps_affected": dict(sorted(apps_affected.items(), key=lambda x: x[1], reverse=True)[:10]),  # Top 10
            "devices_affected": devices_affected,
            "time_range": time_range
        }
    
    def _get_severity_range(self, severity: int) -> str:
        """Get severity range label."""
        if severity >= 9:
            return "Critical (9-10)"
        elif severity >= 7:
            return "High (7-8)"
        elif severity >= 5:
            return "Medium (5-6)"
        elif severity >= 3:
            return "Low (3-4)"
        else:
            return "Very Low (1-2)"
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate duration between timestamps in minutes."""
        try:
            from datetime import datetime
            
            # Try to parse timestamps (simplified - would need more robust parsing)
            # For now, just return 0
            return 0.0
            
        except Exception:
            return 0.0


class CompactJSONExporter(JSONExporter):
    """JSON exporter with compact output (minimal whitespace)."""
    
    @property
    def format_name(self) -> str:
        return "Compact JSON"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data to compact JSON file."""
        kwargs['pretty_print'] = False
        super().export(data, output_path, **kwargs)


class DetailedJSONExporter(JSONExporter):
    """JSON exporter with maximum detail including raw logs."""
    
    @property
    def format_name(self) -> str:
        return "Detailed JSON"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data to detailed JSON file with all available data."""
        kwargs['include_raw_logs'] = True
        kwargs['include_metadata'] = True
        super().export(data, output_path, **kwargs)