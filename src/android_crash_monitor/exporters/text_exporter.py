#!/usr/bin/env python3
"""
Text/Markdown Exporter

Exports crash reports and monitoring data to plain text or Markdown format
for simple viewing and documentation.
"""

from pathlib import Path
from typing import Dict, Any, List

from .base import BaseExporter, ExportData, ExportError


class TextExporter(BaseExporter):
    """Exports data to plain text format."""
    
    @property
    def file_extension(self) -> str:
        return "txt"
    
    @property
    def format_name(self) -> str:
        return "Plain Text"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data to text file."""
        self._validate_output_path(output_path)
        
        # Get formatting options
        use_markdown = kwargs.get('use_markdown', False)
        include_metadata = kwargs.get('include_metadata', True)
        include_stats = kwargs.get('include_stats', True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                content = self._build_text_content(
                    data, use_markdown, include_metadata, include_stats
                )
                f.write(content)
                
        except Exception as e:
            raise ExportError(f"Failed to write text file: {e}")
    
    def _build_text_content(self, data: ExportData, use_markdown: bool, 
                           include_metadata: bool, include_stats: bool) -> str:
        """Build the complete text content."""
        sections = []
        
        # Header
        sections.append(self._text_header(use_markdown))
        
        # Metadata
        if include_metadata:
            metadata = self._create_export_metadata(data)
            sections.append(self._text_metadata_section(metadata, use_markdown))
        
        # Summary
        sections.append(self._text_summary_section(data, use_markdown))
        
        # Crashes
        if data.crashes:
            sections.append(self._text_crashes_section(data.crashes, use_markdown))
        
        # Statistics
        if include_stats and data.stats:
            sections.append(self._text_statistics_section(data.stats, use_markdown))
        
        return '\n\n'.join(sections)
    
    def _text_header(self, use_markdown: bool) -> str:
        """Generate text header."""
        if use_markdown:
            return "# 📱 Android Crash Monitor Report\n"
        else:
            return "=" * 60 + "\n  ANDROID CRASH MONITOR REPORT\n" + "=" * 60
    
    def _text_metadata_section(self, metadata: Dict[str, Any], use_markdown: bool) -> str:
        """Generate metadata section."""
        if use_markdown:
            lines = ["## Export Information"]
        else:
            lines = ["-" * 40, "EXPORT INFORMATION", "-" * 40]
        
        lines.extend([
            f"Generated: {metadata.get('export_timestamp', 'Unknown')}",
            f"Format: {metadata.get('export_format', 'Unknown')}",
            f"Crashes: {metadata.get('crash_count', 0)}",
            f"Logs: {metadata.get('log_count', 0)}"
        ])
        
        return '\n'.join(lines)
    
    def _text_summary_section(self, data: ExportData, use_markdown: bool) -> str:
        """Generate summary section."""
        if use_markdown:
            lines = ["## Summary"]
        else:
            lines = ["-" * 40, "SUMMARY", "-" * 40]
        
        crash_count = len(data.crashes)
        
        if crash_count == 0:
            lines.extend([
                "✅ No crashes detected during monitoring session.",
                "This indicates stable application performance."
            ])
            return '\n'.join(lines)
        
        # Calculate summary stats
        crash_types = {}
        severity_high = 0
        apps_affected = set()
        devices_affected = set()
        
        for crash in data.crashes:
            crash_types[crash.crash_type.value] = crash_types.get(crash.crash_type.value, 0) + 1
            if crash.severity >= 7:
                severity_high += 1
            if crash.app_package:
                apps_affected.add(crash.app_package)
            devices_affected.add(crash.device_serial)
        
        lines.extend([
            f"Total Crashes: {crash_count}",
            f"High Severity Crashes: {severity_high}",
            f"Applications Affected: {len(apps_affected)}",
            f"Devices Affected: {len(devices_affected)}"
        ])
        
        # Top crash types
        if crash_types:
            lines.append("")
            if use_markdown:
                lines.append("### Crash Types")
            else:
                lines.append("Crash Types:")
            
            sorted_types = sorted(crash_types.items(), key=lambda x: x[1], reverse=True)
            for crash_type, count in sorted_types:
                type_name = crash_type.replace('_', ' ').title()
                lines.append(f"  {type_name}: {count}")
        
        return '\n'.join(lines)
    
    def _text_crashes_section(self, crashes: List[Any], use_markdown: bool) -> str:
        """Generate crashes section."""
        if use_markdown:
            lines = ["## Crash Details"]
        else:
            lines = ["-" * 40, "CRASH DETAILS", "-" * 40]
        
        for i, crash in enumerate(crashes, 1):
            crash_dict = crash.to_dict() if hasattr(crash, 'to_dict') else crash
            lines.append(self._text_crash_item(crash_dict, i, use_markdown))
        
        return '\n'.join(lines)
    
    def _text_crash_item(self, crash: Dict[str, Any], index: int, use_markdown: bool) -> str:
        """Generate text for a single crash item."""
        crash_type = crash.get('crash_type', 'unknown')
        severity = crash.get('severity', 0)
        title = crash.get('title', 'Unknown Crash')
        description = crash.get('description', '')
        timestamp = crash.get('timestamp', 'Unknown')
        app_package = crash.get('app_package', 'Unknown')
        device = crash.get('device_serial', 'Unknown')
        
        if use_markdown:
            lines = [f"### {index}. {title}"]
        else:
            lines = [f"\nCrash #{index}: {title}", "-" * 50]
        
        lines.extend([
            f"Time: {timestamp}",
            f"Type: {crash_type.replace('_', ' ').title()}",
            f"Severity: {severity}/10 {self._severity_indicator(severity)}",
            f"Application: {app_package}",
            f"Device: {device}",
            ""
        ])
        
        # Description
        if use_markdown:
            lines.append("**Description:**")
        else:
            lines.append("Description:")
        
        # Wrap description text
        desc_lines = self._wrap_text(description, 80)
        lines.extend(desc_lines)
        
        # Stack trace
        stack_trace = crash.get('stack_trace', [])
        if stack_trace:
            lines.append("")
            if use_markdown:
                lines.append("**Stack Trace:**")
                lines.append("```")
            else:
                lines.append("Stack Trace:")
            
            # Limit stack trace lines
            for line in stack_trace[:15]:  # First 15 lines
                lines.append(line)
            
            if len(stack_trace) > 15:
                lines.append(f"... ({len(stack_trace) - 15} more lines)")
            
            if use_markdown:
                lines.append("```")
        
        return '\n'.join(lines)
    
    def _text_statistics_section(self, stats: Any, use_markdown: bool) -> str:
        """Generate statistics section."""
        if use_markdown:
            lines = ["## Session Statistics"]
        else:
            lines = ["-" * 40, "SESSION STATISTICS", "-" * 40]
        
        stats_dict = stats if isinstance(stats, dict) else stats.__dict__
        
        # Basic stats
        duration = self._format_duration(stats_dict.get('uptime_seconds', 0))
        
        lines.extend([
            f"Session ID: {stats_dict.get('session_id', 'N/A')}",
            f"Start Time: {stats_dict.get('start_time', 'N/A')}",
            f"End Time: {stats_dict.get('end_time', 'N/A')}",
            f"Duration: {duration}",
            f"Total Logs Processed: {stats_dict.get('total_logs_processed', 0):,}",
            f"Average Logs/Second: {stats_dict.get('logs_per_second', 0):.1f}",
            f"Total Crashes: {stats_dict.get('total_crashes', 0)}",
            f"Device Reconnections: {stats_dict.get('reconnection_count', 0)}"
        ])
        
        # Crashes by type
        crashes_by_type = stats_dict.get('crashes_by_type', {})
        if crashes_by_type:
            lines.append("")
            if use_markdown:
                lines.append("### Crashes by Type")
            else:
                lines.append("Crashes by Type:")
            
            for crash_type, count in crashes_by_type.items():
                type_name = crash_type.replace('_', ' ').title()
                lines.append(f"  {type_name}: {count}")
        
        # Crashes by app
        crashes_by_app = stats_dict.get('crashes_by_app', {})
        if crashes_by_app:
            lines.append("")
            if use_markdown:
                lines.append("### Top Crashing Applications")
            else:
                lines.append("Top Crashing Applications:")
            
            # Sort and limit to top 5
            sorted_apps = sorted(crashes_by_app.items(), key=lambda x: x[1], reverse=True)
            for app, count in sorted_apps[:5]:
                lines.append(f"  {app}: {count}")
        
        return '\n'.join(lines)
    
    def _severity_indicator(self, severity: int) -> str:
        """Get severity indicator emoji/text."""
        if severity >= 9:
            return "🔴 Critical"
        elif severity >= 7:
            return "🟠 High"
        elif severity >= 5:
            return "🟡 Medium"
        elif severity >= 3:
            return "🔵 Low"
        else:
            return "⚪ Very Low"
    
    def _wrap_text(self, text: str, width: int = 80) -> List[str]:
        """Wrap text to specified width."""
        if not text:
            return [""]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines or [""]
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human readable format."""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"


class MarkdownExporter(TextExporter):
    """Specialized exporter for Markdown format."""
    
    @property
    def file_extension(self) -> str:
        return "md"
    
    @property
    def format_name(self) -> str:
        return "Markdown"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data to Markdown file."""
        kwargs['use_markdown'] = True
        super().export(data, output_path, **kwargs)