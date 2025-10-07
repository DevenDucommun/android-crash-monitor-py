#!/usr/bin/env python3
"""
CSV Exporter

Exports crash reports and monitoring data to CSV format for analysis in
spreadsheet applications like Excel, Google Sheets, etc.
"""

import csv
from pathlib import Path
from typing import Dict, Any, List

from .base import BaseExporter, ExportData, ExportError


class CSVExporter(BaseExporter):
    """Exports crash data to CSV format."""
    
    # Default columns for crash export
    DEFAULT_CRASH_COLUMNS = [
        'timestamp',
        'crash_type', 
        'severity',
        'title',
        'app_package',
        'app_name',
        'device_serial',
        'device_model',
        'description',
        'session_id'
    ]
    
    # All available columns
    ALL_CRASH_COLUMNS = DEFAULT_CRASH_COLUMNS + [
        'stack_trace_lines',
        'related_logs_count',
        'detection_patterns',
        'first_seen'
    ]
    
    @property
    def file_extension(self) -> str:
        return "csv"
    
    @property
    def format_name(self) -> str:
        return "CSV"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data to CSV file."""
        self._validate_output_path(output_path)
        
        # Get export options
        columns = kwargs.get('columns', self.DEFAULT_CRASH_COLUMNS)
        include_header = kwargs.get('include_header', True)
        delimiter = kwargs.get('delimiter', ',')
        include_stats = kwargs.get('include_stats', False)
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                # Export crashes to CSV
                if data.crashes:
                    self._write_crashes_csv(f, data.crashes, columns, include_header, delimiter)
                
                # Optionally add statistics as additional rows
                if include_stats and data.stats:
                    if data.crashes:
                        f.write('\n\n')  # Add some space
                    self._write_stats_csv(f, data.stats, delimiter)
                    
        except Exception as e:
            raise ExportError(f"Failed to write CSV file: {e}")
    
    def _write_crashes_csv(self, file_handle, crashes, columns, include_header, delimiter):
        """Write crash data to CSV."""
        writer = csv.writer(file_handle, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        if include_header:
            header = [col.replace('_', ' ').title() for col in columns]
            writer.writerow(header)
        
        # Write crash data
        for crash in crashes:
            row = []
            crash_dict = crash.to_dict() if hasattr(crash, 'to_dict') else crash
            
            for column in columns:
                value = self._get_column_value(crash_dict, column)
                row.append(value)
            
            writer.writerow(row)
    
    def _write_stats_csv(self, file_handle, stats, delimiter):
        """Write statistics as CSV sections."""
        writer = csv.writer(file_handle, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
        
        stats_dict = stats if isinstance(stats, dict) else stats.__dict__
        
        # Session summary
        writer.writerow(['SESSION STATISTICS'])
        writer.writerow(['Metric', 'Value'])
        
        basic_stats = [
            ('Session ID', stats_dict.get('session_id', 'N/A')),
            ('Start Time', stats_dict.get('start_time', 'N/A')),
            ('End Time', stats_dict.get('end_time', 'N/A')),
            ('Duration (seconds)', stats_dict.get('uptime_seconds', 0)),
            ('Total Logs Processed', stats_dict.get('total_logs_processed', 0)),
            ('Total Crashes', stats_dict.get('total_crashes', 0)),
            ('Logs per Second', stats_dict.get('logs_per_second', 0)),
            ('Reconnection Count', stats_dict.get('reconnection_count', 0))
        ]
        
        for metric, value in basic_stats:
            writer.writerow([metric, value])
        
        # Crash types breakdown
        crashes_by_type = stats_dict.get('crashes_by_type', {})
        if crashes_by_type:
            writer.writerow([])  # Empty row
            writer.writerow(['CRASHES BY TYPE'])
            writer.writerow(['Crash Type', 'Count'])
            
            for crash_type, count in crashes_by_type.items():
                writer.writerow([crash_type.replace('_', ' ').title(), count])
        
        # Apps breakdown
        crashes_by_app = stats_dict.get('crashes_by_app', {})
        if crashes_by_app:
            writer.writerow([])  # Empty row
            writer.writerow(['CRASHES BY APPLICATION'])
            writer.writerow(['Application', 'Count'])
            
            # Sort by count descending, limit to top 10
            sorted_apps = sorted(crashes_by_app.items(), key=lambda x: x[1], reverse=True)
            for app, count in sorted_apps[:10]:
                writer.writerow([app, count])
    
    def _get_column_value(self, crash_dict: Dict[str, Any], column: str) -> str:
        """Get the value for a specific column from crash data."""
        if column == 'stack_trace_lines':
            stack_trace = crash_dict.get('stack_trace', [])
            return str(len(stack_trace)) if stack_trace else '0'
        
        elif column == 'related_logs_count':
            related_logs = crash_dict.get('related_logs', [])
            return str(len(related_logs)) if related_logs else '0'
        
        elif column == 'detection_patterns':
            patterns = crash_dict.get('detection_patterns', [])
            return '; '.join(patterns) if patterns else ''
        
        elif column == 'description':
            # Truncate long descriptions and remove newlines
            desc = crash_dict.get('description', '')
            if len(desc) > 200:
                desc = desc[:200] + '...'
            return desc.replace('\n', ' ').replace('\r', ' ')
        
        else:
            # Standard column
            value = crash_dict.get(column, '')
            
            # Convert complex values to strings
            if isinstance(value, list):
                return '; '.join(str(v) for v in value)
            elif isinstance(value, dict):
                return str(value)
            else:
                return str(value) if value is not None else ''


class ExcelCSVExporter(CSVExporter):
    """CSV exporter optimized for Microsoft Excel."""
    
    @property
    def format_name(self) -> str:
        return "Excel CSV"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data optimized for Excel."""
        # Use semicolon delimiter for Excel compatibility in some locales
        kwargs.setdefault('delimiter', ';')
        super().export(data, output_path, **kwargs)


class DetailedCSVExporter(CSVExporter):
    """CSV exporter with all available columns."""
    
    @property
    def format_name(self) -> str:
        return "Detailed CSV"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export with all available columns."""
        kwargs.setdefault('columns', self.ALL_CRASH_COLUMNS)
        kwargs.setdefault('include_stats', True)
        super().export(data, output_path, **kwargs)


class LogsCSVExporter(BaseExporter):
    """Specialized CSV exporter for log entries."""
    
    LOG_COLUMNS = [
        'timestamp',
        'level',
        'tag', 
        'pid',
        'tid',
        'message',
        'device_serial'
    ]
    
    @property
    def file_extension(self) -> str:
        return "csv"
    
    @property
    def format_name(self) -> str:
        return "Logs CSV"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export log entries to CSV."""
        self._validate_output_path(output_path)
        
        if not data.logs:
            raise ExportError("No log entries to export")
        
        columns = kwargs.get('columns', self.LOG_COLUMNS)
        include_header = kwargs.get('include_header', True)
        delimiter = kwargs.get('delimiter', ',')
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
                
                # Write header
                if include_header:
                    header = [col.replace('_', ' ').title() for col in columns]
                    writer.writerow(header)
                
                # Write log entries
                for log in data.logs:
                    row = []
                    log_dict = log.to_dict() if hasattr(log, 'to_dict') else log
                    
                    for column in columns:
                        value = log_dict.get(column, '')
                        
                        # Clean up message field
                        if column == 'message':
                            value = str(value).replace('\n', ' ').replace('\r', ' ')
                        
                        row.append(str(value) if value is not None else '')
                    
                    writer.writerow(row)
                    
        except Exception as e:
            raise ExportError(f"Failed to write logs CSV file: {e}")