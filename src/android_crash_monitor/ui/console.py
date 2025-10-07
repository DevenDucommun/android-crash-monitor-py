#!/usr/bin/env python3
"""
Rich Console UI Module

Provides a beautiful, user-friendly terminal interface using the Rich library.
Includes progress bars, tables, panels, and colored output for enhanced UX.
"""

from contextlib import contextmanager
from typing import List, Optional, Any, TYPE_CHECKING
import sys

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align

if TYPE_CHECKING:
    from ..core.adb import AndroidDevice


class ConsoleUI:
    """Modern console interface with Rich formatting."""
    
    def __init__(self, quiet: bool = False, no_color: bool = False):
        self.console = Console(
            quiet=quiet,
            force_terminal=not no_color,
            highlight=False
        )
        self.quiet = quiet
        self._step_counter = 0
        
    def print(self, *args, **kwargs) -> None:
        """Print with Rich formatting."""
        self.console.print(*args, **kwargs)
        
    def clear(self) -> None:
        """Clear the console."""
        if not self.quiet:
            self.console.clear()
    
    def step(self, message: str) -> None:
        """Print a step header."""
        self._step_counter += 1
        header = f"Step {self._step_counter}: {message}"
        self.print(f"\n[bold blue]{'=' * 60}[/bold blue]")
        self.print(f"[bold blue]{header}[/bold blue]")
        self.print(f"[bold blue]{'=' * 60}[/bold blue]\n")
    
    def success(self, message: str) -> None:
        """Print a success message."""
        self.print(f"[bold green]✅ {message}[/bold green]")
        
    def error(self, message: str) -> None:
        """Print an error message."""
        self.print(f"[bold red]❌ {message}[/bold red]")
        
    def warning(self, message: str) -> None:
        """Print a warning message."""
        self.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
        
    def info(self, message: str) -> None:
        """Print an info message."""
        self.print(f"[blue]ℹ️  {message}[/blue]")
    
    def action(self, message: str) -> None:
        """Print an action message."""
        self.print(f"[cyan]🔧 {message}[/cyan]")
    
    @contextmanager
    def status(self, message: str):
        """Show a status spinner."""
        if self.quiet:
            yield
        else:
            with self.console.status(f"[bold blue]{message}[/bold blue]", spinner="dots"):
                yield
    
    def create_panel(self, content: str, title: str = "", 
                    border_style: str = "blue") -> Panel:
        """Create a Rich panel."""
        return Panel(
            content,
            title=f"[bold {border_style}]{title}[/bold {border_style}]" if title else "",
            border_style=border_style
        )
    
    def display_system_info(self, system_info: dict) -> None:
        """Display system information in a nice table."""
        table = Table(title="System Information")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Details", style="white")
        
        # Map system info to display
        display_map = {
            'os_name': 'Operating System',
            'architecture': 'Architecture',
            'python_version': 'Python Version',
            'shell': 'Shell',
            'terminal': 'Terminal',
            'java_version': 'Java Version',
            'android_home': 'Android SDK',
            'is_admin': 'Administrator'
        }
        
        for key, display_name in display_map.items():
            value = system_info.get(key)
            if value is not None:
                if key == 'is_admin':
                    value = "Yes" if value else "No"
                elif key == 'package_managers':
                    value = ", ".join(value) if value else "None detected"
                    
                table.add_row(display_name, str(value))
        
        # Handle package managers separately
        if 'package_managers' in system_info:
            managers = system_info['package_managers']
            if managers:
                table.add_row("Package Managers", ", ".join(managers))
            else:
                table.add_row("Package Managers", "[yellow]None detected[/yellow]")
        
        # Handle download tools
        if 'has_download_tools' in system_info:
            has_tools = system_info['has_download_tools']
            status = "[green]Available[/green]" if has_tools else "[red]Missing[/red]"
            table.add_row("Download Tools", status)
        
        self.print(table)
    
    def header(self, message: str) -> None:
        """Print a section header."""
        self.print(f"\n[bold blue]{'=' * 60}[/bold blue]")
        self.print(f"[bold blue]{message}[/bold blue]")
        self.print(f"[bold blue]{'=' * 60}[/bold blue]\n")
    
    @contextmanager
    def spinner(self, message: str):
        """Show a spinner with message."""
        if self.quiet:
            yield
        else:
            with self.console.status(f"[bold blue]{message}[/bold blue]", spinner="dots"):
                yield
    
    def display_devices(self, devices: List['AndroidDevice'], detailed: bool = False) -> None:
        """Display Android devices in a table."""
        if not devices:
            self.warning("No Android devices found")
            return
        
        table = Table(title=f"Connected Android Devices ({len(devices)})")
        table.add_column("Device ID", style="cyan", no_wrap=True)
        table.add_column("Status", style="white")
        table.add_column("Model", style="green")
        
        if detailed:
            table.add_column("Product", style="yellow")
            table.add_column("Transport", style="magenta")
        
        for device in devices:
            status = self._format_device_status(device.status)
            model = device.model or "[dim]Unknown[/dim]"
            
            row = [device.serial, status, model]
            
            if detailed:
                product = device.product or "[dim]N/A[/dim]"
                transport = device.transport_id or "[dim]N/A[/dim]"
                row.extend([product, transport])
            
            table.add_row(*row)
        
        self.print(table)
    
    def display_setup_summary(self, summary: dict) -> None:
        """Display setup completion summary."""
        table = Table(title="Setup Summary")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        
        for component, status in summary.items():
            status_icon = self._format_status_icon(status)
            table.add_row(component, status_icon)
        
        self.print(table)
    
    def display_progress_table(self, items: List[dict]) -> None:
        """Display a table with progress indicators."""
        table = Table()
        table.add_column("Task", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        for item in items:
            status = item.get('status', 'unknown')
            status_text = self._format_status_icon(status)
            
            table.add_row(
                item.get('task', ''),
                status_text,
                item.get('details', '')
            )
        
        self.print(table)
    
    def create_installation_options_table(self, options: List[tuple]) -> Table:
        """Create a table for installation options."""
        table = Table(title="Installation Options")
        table.add_column("#", style="bold cyan", width=3)
        table.add_column("Method", style="white")
        table.add_column("Description", style="dim")
        
        for i, (method, description) in enumerate(options, 1):
            # Split emoji and text for better formatting
            if description.startswith(('⚡', '📦', '📖', '⏭️', '🍺')):
                emoji = description[0]
                text = description[2:].strip()
                formatted_desc = f"{emoji} {text}"
            else:
                formatted_desc = description
            
            table.add_row(str(i), method, formatted_desc)
        
        return table
    
    def show_quick_help(self, commands: dict) -> None:
        """Show a quick help panel."""
        help_text = "\n".join([
            f"[bold cyan]{cmd}[/bold cyan] - {desc}" 
            for cmd, desc in commands.items()
        ])
        
        panel = Panel(
            help_text,
            title="[bold green]Quick Commands[/bold green]",
            border_style="green"
        )
        
        self.print(panel)
    
    def create_progress_context(self, description: str = "Working..."):
        """Create a progress context for long operations."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )
    
    def _format_device_status(self, status: str) -> str:
        """Format device status with colors."""
        status_map = {
            'device': '[green]Online[/green]',
            'offline': '[red]Offline[/red]',
            'unauthorized': '[yellow]Unauthorized[/yellow]',
            'bootloader': '[blue]Bootloader[/blue]',
            'recovery': '[magenta]Recovery[/magenta]',
            'sideload': '[cyan]Sideload[/cyan]'
        }
        return status_map.get(status, f'[dim]{status}[/dim]')
    
    def _format_status_icon(self, status: str) -> str:
        """Format status with appropriate icons and colors."""
        if isinstance(status, bool):
            return "[green]✅ Complete[/green]" if status else "[red]❌ Failed[/red]"
        
        status_lower = str(status).lower()
        
        if status_lower in ('complete', 'success', 'ok', 'installed', 'connected'):
            return "[green]✅ Complete[/green]"
        elif status_lower in ('failed', 'error', 'missing', 'not found'):
            return "[red]❌ Failed[/red]"
        elif status_lower in ('warning', 'partial', 'limited', 'no devices'):
            return "[yellow]⚠️  Warning[/yellow]"
        elif status_lower in ('pending', 'in progress', 'running'):
            return "[blue]🔄 In Progress[/blue]"
        else:
            return f"[dim]{status}[/dim]"
    
    def ask_confirmation(self, message: str, default: bool = True) -> bool:
        """Ask for user confirmation (this would integrate with Rich prompts)."""
        # Note: This is a placeholder - actual implementation would use rich.prompt
        try:
            from rich.prompt import Confirm
            return Confirm.ask(message, default=default)
        except ImportError:
            # Fallback if Rich prompt not available
            response = input(f"{message} ({'Y/n' if default else 'y/N'}): ").strip().lower()
            if not response:
                return default
            return response.startswith('y')
    
    def ask_choice(self, message: str, choices: List[str]) -> str:
        """Ask user to choose from a list of options."""
        try:
            from rich.prompt import Prompt
            return Prompt.ask(message, choices=choices)
        except ImportError:
            # Fallback implementation
            while True:
                response = input(f"{message} ({'/'.join(choices)}): ").strip()
                if response in choices:
                    return response
                self.error(f"Invalid choice. Please choose from: {', '.join(choices)}")


# Module-level convenience functions
def get_console(quiet: bool = False) -> ConsoleUI:
    """Get a console instance."""
    return ConsoleUI(quiet=quiet)


def print_success(message: str) -> None:
    """Print a success message."""
    console = get_console()
    console.success(message)


def print_error(message: str) -> None:
    """Print an error message."""
    console = get_console()
    console.error(message)


def print_warning(message: str) -> None:
    """Print a warning message."""
    console = get_console()
    console.warning(message)