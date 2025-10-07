#!/usr/bin/env python3
"""
HTML Exporter

Exports crash reports to HTML format with styling, charts, and interactive features
for viewing in web browsers.
"""

from pathlib import Path
from typing import Dict, Any, List
import html

from .base import BaseExporter, ExportData, ExportError


class HTMLExporter(BaseExporter):
    """Exports data to HTML format with styling."""
    
    @property
    def file_extension(self) -> str:
        return "html"
    
    @property
    def format_name(self) -> str:
        return "HTML Report"
    
    def export(self, data: ExportData, output_path: Path, **kwargs) -> None:
        """Export data to HTML file."""
        self._validate_output_path(output_path)
        
        # Get styling options
        include_css = kwargs.get('include_css', True)
        include_charts = kwargs.get('include_charts', True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                html_content = self._build_html_content(data, include_css, include_charts)
                f.write(html_content)
                
        except Exception as e:
            raise ExportError(f"Failed to write HTML file: {e}")
    
    def _build_html_content(self, data: ExportData, include_css: bool, include_charts: bool) -> str:
        """Build the complete HTML content."""
        metadata = self._create_export_metadata(data)
        
        html_parts = [
            self._html_header(metadata.get('export_timestamp', ''), include_css),
            self._html_summary_section(data),
            self._html_crashes_section(data.crashes),
        ]
        
        if data.stats:
            html_parts.append(self._html_statistics_section(data.stats))
        
        if include_charts and data.crashes:
            html_parts.append(self._html_charts_section(data))
        
        html_parts.append(self._html_footer())
        
        return '\n'.join(html_parts)
    
    def _html_header(self, export_time: str, include_css: bool) -> str:
        """Generate HTML header with CSS."""
        css = self._get_css() if include_css else ""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Android Crash Monitor Report</title>
    {css}
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>📱 Android Crash Monitor Report</h1>
            <p class="export-time">Generated: {export_time}</p>
        </header>"""
    
    def _html_summary_section(self, data: ExportData) -> str:
        """Generate summary section."""
        crash_count = len(data.crashes)
        
        if crash_count == 0:
            return """
        <section class="summary no-crashes">
            <h2>Summary</h2>
            <div class="summary-card success">
                <h3>✅ No Crashes Detected</h3>
                <p>Great news! No crashes were detected during the monitoring session.</p>
            </div>
        </section>"""
        
        # Calculate summary statistics
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
        
        return f"""
        <section class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>{crash_count}</h3>
                    <p>Total Crashes</p>
                </div>
                <div class="summary-card">
                    <h3>{severity_high}</h3>
                    <p>High Severity</p>
                </div>
                <div class="summary-card">
                    <h3>{len(apps_affected)}</h3>
                    <p>Apps Affected</p>
                </div>
                <div class="summary-card">
                    <h3>{len(devices_affected)}</h3>
                    <p>Devices Affected</p>
                </div>
            </div>
        </section>"""
    
    def _html_crashes_section(self, crashes: List[Any]) -> str:
        """Generate crashes section."""
        if not crashes:
            return ""
        
        crashes_html = []
        for i, crash in enumerate(crashes):
            crash_dict = crash.to_dict() if hasattr(crash, 'to_dict') else crash
            crashes_html.append(self._html_crash_item(crash_dict, i + 1))
        
        return f"""
        <section class="crashes">
            <h2>Crash Details</h2>
            <div class="crashes-list">
                {''.join(crashes_html)}
            </div>
        </section>"""
    
    def _html_crash_item(self, crash: Dict[str, Any], index: int) -> str:
        """Generate HTML for a single crash item."""
        crash_type = crash.get('crash_type', 'unknown')
        severity = crash.get('severity', 0)
        title = html.escape(crash.get('title', 'Unknown Crash'))
        description = html.escape(crash.get('description', '')[:200])
        timestamp = crash.get('timestamp', 'Unknown')
        app_package = crash.get('app_package', 'Unknown')
        device = crash.get('device_serial', 'Unknown')
        
        # Determine severity class
        severity_class = self._get_severity_class(severity)
        
        # Format stack trace if available
        stack_trace_html = ""
        stack_trace = crash.get('stack_trace', [])
        if stack_trace:
            stack_trace_lines = [html.escape(line) for line in stack_trace[:10]]  # Limit to 10 lines
            stack_trace_html = f"""
                <div class="stack-trace">
                    <h4>Stack Trace</h4>
                    <pre><code>{'<br>'.join(stack_trace_lines)}</code></pre>
                    {f'<p class="truncated">... and {len(stack_trace) - 10} more lines</p>' if len(stack_trace) > 10 else ''}
                </div>"""
        
        return f"""
            <div class="crash-item {severity_class}">
                <div class="crash-header">
                    <h3>#{index} {title}</h3>
                    <div class="crash-meta">
                        <span class="badge crash-type">{crash_type.replace('_', ' ').title()}</span>
                        <span class="badge severity-{severity}">Severity: {severity}/10</span>
                    </div>
                </div>
                
                <div class="crash-details">
                    <div class="detail-grid">
                        <div class="detail-item">
                            <strong>Time:</strong> {timestamp}
                        </div>
                        <div class="detail-item">
                            <strong>Application:</strong> {app_package}
                        </div>
                        <div class="detail-item">
                            <strong>Device:</strong> {device}
                        </div>
                    </div>
                    
                    <div class="crash-description">
                        <h4>Description</h4>
                        <p>{description}</p>
                    </div>
                    
                    {stack_trace_html}
                </div>
            </div>"""
    
    def _html_statistics_section(self, stats: Any) -> str:
        """Generate statistics section."""
        stats_dict = stats if isinstance(stats, dict) else stats.__dict__
        
        return f"""
        <section class="statistics">
            <h2>Session Statistics</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <h4>Duration</h4>
                    <p>{self._format_duration(stats_dict.get('uptime_seconds', 0))}</p>
                </div>
                <div class="stat-item">
                    <h4>Logs Processed</h4>
                    <p>{stats_dict.get('total_logs_processed', 0):,}</p>
                </div>
                <div class="stat-item">
                    <h4>Avg Logs/Second</h4>
                    <p>{stats_dict.get('logs_per_second', 0):.1f}</p>
                </div>
                <div class="stat-item">
                    <h4>Reconnections</h4>
                    <p>{stats_dict.get('reconnection_count', 0)}</p>
                </div>
            </div>
        </section>"""
    
    def _html_charts_section(self, data: ExportData) -> str:
        """Generate charts section (simplified, would need JavaScript for real charts)."""
        return """
        <section class="charts">
            <h2>Visual Analysis</h2>
            <p class="chart-placeholder">
                📊 Chart visualizations would be implemented here with JavaScript libraries 
                like Chart.js or D3.js for interactive crash analysis.
            </p>
        </section>"""
    
    def _html_footer(self) -> str:
        """Generate HTML footer."""
        return """
        <footer class="report-footer">
            <p>Generated by Android Crash Monitor v1.0</p>
        </footer>
    </div>
</body>
</html>"""
    
    def _get_css(self) -> str:
        """Get embedded CSS for styling."""
        return """
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .report-header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .export-time { opacity: 0.9; font-size: 1.1em; }
        
        section {
            background: white;
            margin-bottom: 30px;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        section h2 {
            color: #4a5568;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .summary-card {
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e2e8f0;
        }
        
        .summary-card h3 {
            font-size: 2em;
            color: #2d3748;
            margin-bottom: 5px;
        }
        
        .summary-card.success {
            background: #f0fff4;
            border-color: #9ae6b4;
            color: #276749;
        }
        
        .crash-item {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        
        .crash-item.high-severity { border-left: 4px solid #f56565; }
        .crash-item.medium-severity { border-left: 4px solid #ed8936; }
        .crash-item.low-severity { border-left: 4px solid #48bb78; }
        
        .crash-header {
            background: #f8fafc;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .crash-header h3 { color: #2d3748; }
        
        .crash-meta {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }
        
        .badge.crash-type {
            background: #bee3f8;
            color: #2a69ac;
        }
        
        .badge[class*="severity-"] {
            background: #fed7d7;
            color: #c53030;
        }
        
        .crash-details { padding: 15px; }
        
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .detail-item {
            padding: 8px;
            background: #f8fafc;
            border-radius: 4px;
        }
        
        .crash-description h4,
        .stack-trace h4 {
            color: #4a5568;
            margin: 15px 0 10px 0;
        }
        
        .stack-trace pre {
            background: #1a202c;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.9em;
        }
        
        .truncated {
            color: #718096;
            font-style: italic;
            margin-top: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .stat-item {
            text-align: center;
            padding: 20px;
            background: #f8fafc;
            border-radius: 8px;
        }
        
        .stat-item h4 {
            color: #4a5568;
            margin-bottom: 10px;
        }
        
        .stat-item p {
            font-size: 1.5em;
            font-weight: bold;
            color: #2d3748;
        }
        
        .chart-placeholder {
            text-align: center;
            padding: 40px;
            background: #f8fafc;
            border-radius: 8px;
            color: #718096;
            font-style: italic;
        }
        
        .report-footer {
            text-align: center;
            padding: 20px;
            color: #718096;
            border-top: 1px solid #e2e8f0;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .crash-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            .detail-grid { grid-template-columns: 1fr; }
        }
    </style>"""
    
    def _get_severity_class(self, severity: int) -> str:
        """Get CSS class for severity level."""
        if severity >= 7:
            return "high-severity"
        elif severity >= 4:
            return "medium-severity"
        else:
            return "low-severity"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"