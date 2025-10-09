#!/usr/bin/env python3
"""
Report Generator - Format crash analysis results into user-friendly reports

Generates comprehensive, actionable reports based on crash analysis results.
"""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from .crash_analyzer import CrashAnalyzer, SystemHealthStatus


class ReportGenerator:
    """Generate formatted crash analysis reports."""
    
    def __init__(self, console: Console = None):
        """Initialize report generator."""
        self.console = console or Console()
        
    def generate_console_report(self, analysis_report: Dict[str, Any]) -> None:
        """Generate a rich console report."""
        self.console.print()
        self._print_header(analysis_report)
        self._print_system_health(analysis_report)
        self._print_critical_patterns(analysis_report)
        self._print_timeline_analysis(analysis_report)
        self._print_component_analysis(analysis_report)
        self._print_recommendations(analysis_report)
        self.console.print()
        
    def _print_header(self, analysis_report: Dict[str, Any]) -> None:
        """Print report header."""
        summary = analysis_report.get('summary', {})
        total_crashes = summary.get('total_crashes', 0)
        timestamp = summary.get('analysis_timestamp', '')
        
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = timestamp
        else:
            formatted_time = 'Unknown'
            
        header_text = f"""🔍 CRASH ANALYSIS REPORT
Total Crashes Analyzed: {total_crashes:,}
Analysis Time: {formatted_time}"""
        
        panel = Panel(header_text, 
                     title="Android Crash Monitor", 
                     box=box.DOUBLE,
                     style="bold blue")
        self.console.print(panel)
        
    def _print_system_health(self, analysis_report: Dict[str, Any]) -> None:
        """Print system health assessment."""
        health = analysis_report.get('summary', {}).get('system_health', {})
        status = health.get('status', 'UNKNOWN')
        confidence = health.get('confidence', 0.0)
        summary = health.get('summary', 'No summary available')
        
        # Status emoji and color
        status_config = {
            'STABLE': {'emoji': '✅', 'color': 'green'},
            'DEGRADED': {'emoji': '⚠️', 'color': 'yellow'},
            'UNSTABLE': {'emoji': '🚨', 'color': 'red'},
            'CRITICAL': {'emoji': '💥', 'color': 'bright_red'}
        }
        
        config = status_config.get(status, {'emoji': '❓', 'color': 'white'})
        
        health_text = f"""{config['emoji']} System Status: {status}
📊 Confidence: {confidence:.1%}
📝 Summary: {summary}"""
        
        panel = Panel(health_text, 
                     title="System Health Assessment", 
                     style=config['color'])
        self.console.print(panel)
        
    def _print_critical_patterns(self, analysis_report: Dict[str, Any]) -> None:
        """Print critical patterns found."""
        patterns = analysis_report.get('critical_patterns', {})
        
        if not patterns:
            self.console.print("[green]✅ No critical patterns detected[/green]")
            return
            
        self.console.print(f"[red]🚨 {len(patterns)} CRITICAL PATTERN(S) DETECTED[/red]")
        
        # Create table for patterns
        table = Table(title="Critical Patterns", box=box.ROUNDED)
        table.add_column("Pattern", style="cyan", no_wrap=True)
        table.add_column("Risk", justify="center")
        table.add_column("Count", justify="right")
        table.add_column("Description", style="dim")
        table.add_column("Recommendation", style="green")
        
        for pattern_name, pattern_data in patterns.items():
            risk_color = {
                'CRITICAL': 'bright_red',
                'HIGH': 'red',
                'MEDIUM': 'yellow',
                'LOW': 'green'
            }.get(pattern_data.get('risk_level', 'LOW'), 'white')
            
            table.add_row(
                pattern_name.replace('_', ' ').title(),
                f"[{risk_color}]{pattern_data.get('risk_level', 'UNKNOWN')}[/{risk_color}]",
                str(pattern_data.get('count', 0)),
                pattern_data.get('description', ''),
                pattern_data.get('recommendation', '')
            )
            
        self.console.print(table)
        
    def _print_timeline_analysis(self, analysis_report: Dict[str, Any]) -> None:
        """Print timeline analysis."""
        timeline = analysis_report.get('timeline_analysis', {})
        
        if not timeline:
            return
            
        peak_period = timeline.get('peak_period')
        if peak_period:
            peak_text = f"""📅 Peak Crash Period: {peak_period.get('time', 'Unknown')}
📊 Crash Count: {peak_period.get('crash_count', 0)}
📋 Top Crash Types: {', '.join([f"{k}({v})" for k, v in peak_period.get('crash_types', {}).items()][:3])}"""
            
            panel = Panel(peak_text, 
                         title="Timeline Analysis", 
                         style="yellow")
            self.console.print(panel)
            
    def _print_component_analysis(self, analysis_report: Dict[str, Any]) -> None:
        """Print system component analysis."""
        components = analysis_report.get('component_analysis', {})
        most_affected = components.get('most_affected_apps', {})
        
        if not most_affected:
            return
            
        # Create table for most affected components
        table = Table(title="Most Affected Components", box=box.SIMPLE)
        table.add_column("Component", style="cyan")
        table.add_column("Crashes", justify="right", style="red")
        table.add_column("Type", style="dim")
        
        system_components = components.get('system_component_crashes', {})
        
        for app, count in list(most_affected.items())[:8]:  # Top 8
            component_type = "System" if app in system_components else "App"
            table.add_row(app, str(count), component_type)
            
        self.console.print(table)
        
    def _print_recommendations(self, analysis_report: Dict[str, Any]) -> None:
        """Print actionable recommendations."""
        risk_assessment = analysis_report.get('risk_assessment', {})
        patterns = analysis_report.get('critical_patterns', {})
        
        recommendations = []
        
        # Priority recommendations based on risk assessment
        if risk_assessment.get('immediate_action_needed', False):
            recommendations.append("🚨 IMMEDIATE ACTION REQUIRED")
            
        if risk_assessment.get('cascade_failure_risk', False):
            recommendations.append("⚡ Cascade failure risk - clear system caches immediately")
            
        if risk_assessment.get('reboot_risk', False):
            recommendations.append("🔄 Device reboot risk - monitor system stability")
            
        # Pattern-specific recommendations
        for pattern_name, pattern_data in patterns.items():
            recommendation = pattern_data.get('recommendation', '')
            if recommendation and recommendation not in recommendations:
                recommendations.append(f"🛠️ {recommendation}")
                
        if recommendations:
            rec_text = "\n".join([f"• {rec}" for rec in recommendations[:5]])  # Top 5
            
            panel = Panel(rec_text, 
                         title="Priority Recommendations", 
                         style="bright_yellow",
                         box=box.DOUBLE)
            self.console.print(panel)
            
    def generate_json_report(self, analysis_report: Dict[str, Any], 
                           output_path: Path) -> None:
        """Generate JSON report file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(analysis_report, f, indent=2, default=str)
        except Exception as e:
            self.console.print(f"[red]Failed to save JSON report: {e}[/red]")
            
    def generate_markdown_report(self, analysis_report: Dict[str, Any], 
                                output_path: Path) -> None:
        """Generate Markdown report file."""
        try:
            with open(output_path, 'w') as f:
                self._write_markdown_report(f, analysis_report)
        except Exception as e:
            self.console.print(f"[red]Failed to save Markdown report: {e}[/red]")
            
    def _write_markdown_report(self, file, analysis_report: Dict[str, Any]) -> None:
        """Write Markdown formatted report."""
        summary = analysis_report.get('summary', {})
        health = summary.get('system_health', {})
        
        file.write(f"""# Crash Analysis Report
        
**Generated:** {summary.get('analysis_timestamp', 'Unknown')}  
**Total Crashes:** {summary.get('total_crashes', 0):,}  
**System Status:** {health.get('status', 'UNKNOWN')}  

## System Health Assessment

- **Status:** {health.get('status', 'UNKNOWN')}
- **Confidence:** {health.get('confidence', 0.0):.1%}
- **Summary:** {health.get('summary', 'No summary available')}

""")
        
        # Critical Patterns
        patterns = analysis_report.get('critical_patterns', {})
        if patterns:
            file.write("## Critical Patterns Detected\n\n")
            for pattern_name, pattern_data in patterns.items():
                file.write(f"""### {pattern_name.replace('_', ' ').title()}
                
- **Risk Level:** {pattern_data.get('risk_level', 'UNKNOWN')}
- **Count:** {pattern_data.get('count', 0)}
- **Severity:** {pattern_data.get('severity', 0)}/10
- **Description:** {pattern_data.get('description', '')}
- **Recommendation:** {pattern_data.get('recommendation', '')}

""")
        
        # Timeline Analysis
        timeline = analysis_report.get('timeline_analysis', {})
        peak = timeline.get('peak_period')
        if peak:
            file.write(f"""## Timeline Analysis

**Peak Crash Period:** {peak.get('time', 'Unknown')}  
**Crash Count:** {peak.get('crash_count', 0)}  
**Top Crash Types:** {', '.join([f"{k}({v})" for k, v in peak.get('crash_types', {}).items()][:3])}

""")
        
        # Component Analysis  
        components = analysis_report.get('component_analysis', {})
        most_affected = components.get('most_affected_apps', {})
        if most_affected:
            file.write("## Most Affected Components\n\n")
            file.write("| Component | Crashes | Type |\n")
            file.write("|-----------|---------|------|\n")
            
            system_components = components.get('system_component_crashes', {})
            for app, count in list(most_affected.items())[:10]:
                component_type = "System" if app in system_components else "App"
                file.write(f"| {app} | {count} | {component_type} |\n")
                
        # Risk Assessment
        risk = analysis_report.get('risk_assessment', {})
        file.write(f"""
## Risk Assessment

- **Cascade Failure Risk:** {"Yes" if risk.get('cascade_failure_risk') else "No"}
- **Reboot Risk:** {"Yes" if risk.get('reboot_risk') else "No"}  
- **Immediate Action Needed:** {"Yes" if risk.get('immediate_action_needed') else "No"}

""")
        
    def generate_summary_report(self, analysis_report: Dict[str, Any]) -> str:
        """Generate a brief summary report."""
        summary = analysis_report.get('summary', {})
        health = summary.get('system_health', {})
        patterns = analysis_report.get('critical_patterns', {})
        
        total_crashes = summary.get('total_crashes', 0)
        status = health.get('status', 'UNKNOWN')
        critical_count = len([p for p in patterns.values() 
                            if p.get('risk_level') == 'CRITICAL'])
        
        if critical_count > 0:
            return f"⚠️ CRITICAL: {critical_count} critical patterns in {total_crashes} crashes. Status: {status}. Immediate action required."
        elif status in ['UNSTABLE', 'DEGRADED']:
            return f"⚠️ {status}: {total_crashes} crashes detected. System stability compromised."
        else:
            return f"✅ STABLE: {total_crashes} crashes analyzed. System operating normally."