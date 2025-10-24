#!/usr/bin/env python3
"""
System Detector UI Module

Handles system detection with rich UI presentation.
"""

from rich.table import Table

from ...core.config import Config
from ...core.system import SystemDetector
from ...ui.console import ACMConsole


class SystemDetectorUI:
    """Handles system detection and UI presentation."""
    
    def __init__(self, config: Config, console: ACMConsole):
        self.config = config
        self.console = console
        self.detector = SystemDetector()
    
    def detect_and_display(self) -> bool:
        """
        Detect system information and display it.
        Returns True if detection was successful.
        """
        self.console.step("Detecting System Configuration")
        
        with self.console.status("Analyzing system..."):
            system_info = self.detector.detect_all()
            
        # Display system information
        system_table = Table(title="System Information")
        system_table.add_column("Component", style="cyan")
        system_table.add_column("Details", style="white")
        
        system_table.add_row("Operating System", f"{system_info.os_name} ({system_info.architecture})")
        system_table.add_row("Python Version", system_info.python_version)
        
        if system_info.package_managers:
            managers = ", ".join(system_info.package_managers)
            system_table.add_row("Package Managers", managers)
        else:
            system_table.add_row("Package Managers", "[yellow]None detected[/yellow]")
            
        system_table.add_row("Download Tools", 
                           "Available" if system_info.has_download_tools else "[red]Missing[/red]")
        
        self.console.print(system_table)
        self.console.success("System detection completed")
        
        # Store system info in config
        self.config.system = system_info
        return True
