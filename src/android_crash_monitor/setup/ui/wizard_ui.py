#!/usr/bin/env python3
"""
Wizard UI Module

Handles all UI presentation for the setup wizard including:
- Welcome screen
- Completion summary
- Configuration screens
"""

from typing import Dict

from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from ...core.config import Config
from ...ui.console import ACMConsole


class WizardUI:
    """Handles all UI presentation for the setup wizard."""
    
    def __init__(self, console: ACMConsole, auto_mode: bool = False):
        self.console = console
        self.auto_mode = auto_mode
    
    def show_welcome(self) -> bool:
        """
        Display welcome screen and introduction.
        Returns True if user wants to continue, False if cancelled.
        """
        self.console.clear()
        
        welcome_text = """
🚀 Android Crash Monitor Setup

This wizard will help you set up Android crash monitoring with:
• Automatic system detection and configuration
• Intelligent ADB installation with multiple methods  
• Device connection testing and validation
• Monitoring preferences and customization

The setup is designed to be fast, reliable, and user-friendly.
"""
        
        self.console.print(Panel(welcome_text.strip(), 
                                title="[bold blue]Welcome[/bold blue]",
                                border_style="blue"))
        
        if not self.auto_mode:
            if not Confirm.ask("\n[bold]Ready to begin setup?[/bold]", default=True):
                return False
                
        return True
    
    def show_completion(self, state: Dict[str, bool]) -> None:
        """Show setup completion summary."""
        self.console.clear()
        
        # Create status summary
        status_table = Table(title="Setup Summary")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="white")
        
        status_table.add_row("System Detection", 
                           "✅ Complete" if state.get('system_detected') else "❌ Failed")
        status_table.add_row("ADB Installation", 
                           "✅ Complete" if state.get('adb_installed') else "❌ Failed")
        status_table.add_row("Device Connection", 
                           "✅ Connected" if state.get('device_connected') else "⚠️  No devices")
        status_table.add_row("Configuration", 
                           "✅ Saved" if state.get('config_saved') else "❌ Failed")
        
        self.console.print(status_table)
        
        # Show next steps
        next_steps = """
🎉 Setup Complete!

Your Android Crash Monitor is ready to use:

• Start monitoring: acm monitor
• List devices: acm devices  
• View logs: acm logs
• Get help: acm --help

The setup has configured everything automatically for the best experience.
"""
        
        self.console.print(Panel(next_steps.strip(),
                               title="[bold green]Success![/bold green]",
                               border_style="green"))
    
    def configure_monitoring(self, config: Config) -> None:
        """Configure monitoring preferences."""
        self.console.step("Monitoring Configuration")
        
        # Set reasonable defaults
        config.monitoring.auto_start = True
        config.monitoring.log_level = "INFO"
        config.monitoring.max_log_size = "100MB"
        config.monitoring.retention_days = 30
        
        if not self.auto_mode:
            # Ask for customization
            customize = Confirm.ask("Customize monitoring settings?", default=False)
            if customize:
                self._customize_monitoring_settings()
    
    def _customize_monitoring_settings(self) -> None:
        """Allow user to customize monitoring settings."""
        # Implementation for custom settings would go here
        self.console.info("Monitoring customization coming soon!")
    
    def save_configuration(self, config: Config) -> bool:
        """
        Save the configuration to disk.
        Returns True if saved successfully.
        """
        self.console.step("Saving Configuration")
        
        try:
            with self.console.status("Writing configuration..."):
                config.setup_complete = True
                config.save()
                
            self.console.success("Configuration saved successfully")
            return True
            
        except Exception as e:
            self.console.error(f"Failed to save configuration: {e}")
            return False
