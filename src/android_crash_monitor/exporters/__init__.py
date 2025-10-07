#!/usr/bin/env python3
"""
Export System for Android Crash Monitor

Provides various export formats for crash reports, session data, and logs.
Supports JSON, CSV, HTML, and text/markdown formats with rich formatting.
"""

from .base import BaseExporter, ExportError, ExportData, MultiFormatExporter
from .json_exporter import JSONExporter, CompactJSONExporter, DetailedJSONExporter
from .csv_exporter import CSVExporter, ExcelCSVExporter, DetailedCSVExporter, LogsCSVExporter
from .html_exporter import HTMLExporter
from .text_exporter import TextExporter, MarkdownExporter

# Export format registry
EXPORTERS = {
    'json': JSONExporter,
    'csv': CSVExporter, 
    'html': HTMLExporter,
    'txt': TextExporter,
    'text': TextExporter,
    'md': MarkdownExporter,
    'markdown': MarkdownExporter,
    # Specialized variants
    'compact-json': CompactJSONExporter,
    'detailed-json': DetailedJSONExporter,
    'excel-csv': ExcelCSVExporter,
    'detailed-csv': DetailedCSVExporter,
    'logs-csv': LogsCSVExporter,
}

def get_exporter(format_name: str) -> BaseExporter:
    """Get an exporter instance for the specified format."""
    format_name = format_name.lower()
    if format_name not in EXPORTERS:
        available = ', '.join(sorted(EXPORTERS.keys()))
        raise ExportError(f"Unsupported export format: {format_name}. Available formats: {available}")
    
    return EXPORTERS[format_name]()

def get_available_formats() -> list[str]:
    """Get list of available export formats."""
    return sorted(EXPORTERS.keys())

def export_crashes(crashes, output_path, format_name='json', **kwargs):
    """Convenience function to export crash data."""
    exporter = get_exporter(format_name)
    data = ExportData()
    data.add_crashes(crashes)
    exporter.export(data, output_path, **kwargs)

__all__ = [
    # Base classes
    'BaseExporter', 'ExportError', 'ExportData', 'MultiFormatExporter',
    # Specific exporters
    'JSONExporter', 'CompactJSONExporter', 'DetailedJSONExporter',
    'CSVExporter', 'ExcelCSVExporter', 'DetailedCSVExporter', 'LogsCSVExporter',
    'HTMLExporter',
    'TextExporter', 'MarkdownExporter',
    # Utility functions
    'get_exporter', 'get_available_formats', 'export_crashes'
]