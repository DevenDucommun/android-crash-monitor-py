#!/usr/bin/env python3
"""
Android Crash Monitor - Main CLI Entry Point

A modern, user-friendly Android crash monitoring tool with rich terminal interface.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.traceback import install

from .core.config import Config, ConfigManager
from .setup.wizard import SetupWizard
from .core.monitor import CrashMonitor
from .core.devices import DeviceManager
from .ui.console import ACMConsole
from .utils.logger import setup_logging

# Install rich traceback handler for better error display
install(show_locals=True)

# Global console instance
console = Console()


@click.group(invoke_without_command=True)
@click.option('--config', '-c', 
              type=click.Path(exists=True, path_type=Path),
              help='Path to configuration file')
@click.option('--profile', '-p', 
              default='default',
              help='Configuration profile to use')
@click.option('--verbose', '-v', 
              count=True,
              help='Increase verbosity (use -v, -vv, -vvv)')
@click.option('--quiet', '-q', 
              is_flag=True,
              help='Suppress all output except errors')
@click.pass_context
def cli(ctx, config: Optional[Path], profile: str, verbose: int, quiet: bool):
    """Android Crash Monitor - Modern crash monitoring for Android devices.
    
    ACM provides intelligent setup, real-time monitoring, and rich log analysis
    for Android application development and debugging.
    
    Examples:
      acm setup              # Run interactive setup wizard
      acm monitor            # Start monitoring default device
      acm logs --last 1h     # Show logs from last hour
      acm devices            # List connected Android devices
    """
    # Setup logging based on verbosity
    log_level = 'ERROR' if quiet else ['INFO', 'DEBUG', 'TRACE'][min(verbose, 2)]
    setup_logging(log_level)
    
    # Initialize configuration
    config_manager = ConfigManager(config_file=config)
    try:
        app_config = config_manager.load_profile(profile)
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        console.print("[yellow]Run 'acm setup' to configure the application[/yellow]")
        sys.exit(1)
    
    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['config'] = app_config
    ctx.obj['console'] = ACMConsole(quiet=quiet)
    
    # If no subcommand provided, show help or run default action
    if ctx.invoked_subcommand is None:
        if not app_config.setup_complete:
            console.print("[yellow]First time setup required. Running setup wizard...[/yellow]")
            ctx.invoke(setup)
        else:
            # Show status or help
            console.print(ctx.get_help())


@cli.command()
@click.option('--auto', is_flag=True, 
              help='Run automatic setup with minimal prompts')
@click.option('--force', is_flag=True,
              help='Force setup even if already configured')
@click.pass_context
def setup(ctx, auto: bool, force: bool):
    """Run the interactive setup wizard.
    
    The setup wizard will:
    - Detect your system configuration
    - Install ADB if needed
    - Configure Android device connections  
    - Set up monitoring preferences
    - Test the complete workflow
    
    Use --auto for minimal prompts, --force to reconfigure.
    """
    config = ctx.obj['config']
    ui = ctx.obj['console']
    
    if config.setup_complete and not force:
        ui.info("Setup already completed. Use --force to reconfigure.")
        return
    
    wizard = SetupWizard(config, ui, auto_mode=auto)
    try:
        wizard.run()
        ui.success("Setup completed successfully!")
    except KeyboardInterrupt:
        ui.warning("Setup cancelled by user")
        sys.exit(130)
    except Exception as e:
        ui.error(f"Setup failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--device', '-d',
              help='Specific device ID to monitor')
@click.option('--output', '-o',
              type=click.Path(path_type=Path),
              help='Output directory for logs')
@click.option('--filter', '-f',
              multiple=True,
              help='Log filters (can be used multiple times)')
@click.option('--duration', '-t',
              help='Monitoring duration (e.g., 30m, 2h, 1d)')
@click.option('--auto-export',
              is_flag=True,
              help='Automatically export logs when monitoring stops')
@click.pass_context
def monitor(ctx, device: Optional[str], output: Optional[Path], 
           filter: tuple, duration: Optional[str], auto_export: bool):
    """Start monitoring Android device for crashes and errors.
    
    This command begins real-time monitoring of your Android device,
    collecting and categorizing logs for later analysis.
    
    Examples:
      acm monitor                    # Monitor default device
      acm monitor -d pixel-5         # Monitor specific device
      acm monitor -f crash -f error  # Filter for crashes and errors only
      acm monitor -t 1h              # Monitor for 1 hour then stop
    """
    config = ctx.obj['config']
    ui = ctx.obj['console']
    
    if not config.setup_complete:
        ui.error("Setup not completed. Run 'acm setup' first.")
        sys.exit(1)
    
    monitor_instance = CrashMonitor(config, ui)
    
    try:
        monitor_instance.start(
            device_id=device,
            output_dir=output,
            filters=list(filter),
            duration=duration,
            auto_export=auto_export
        )
    except KeyboardInterrupt:
        ui.info("Monitoring stopped by user")
    except Exception as e:
        ui.error(f"Monitoring failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--detailed', is_flag=True,
              help='Show detailed device information')
@click.option('--refresh', is_flag=True,
              help='Refresh device list')
@click.pass_context
def devices(ctx, detailed: bool, refresh: bool):
    """List connected Android devices.
    
    Shows all Android devices connected via USB or network,
    with their current status and capabilities.
    """
    config = ctx.obj['config']
    ui = ctx.obj['console']
    
    device_manager = DeviceManager(config, ui)
    
    try:
        device_list = device_manager.list_devices(refresh=refresh)
        ui.display_devices(device_list, detailed=detailed)
    except Exception as e:
        ui.error(f"Failed to list devices: {e}")
        sys.exit(1)


@cli.command()
@click.option('--filter', '-f',
              help='Filter logs (crash, error, warning, info, debug)')
@click.option('--last',
              help='Show logs from last period (e.g., 1h, 30m, 2d)')
@click.option('--device', '-d',
              help='Filter by device ID')
@click.option('--search', '-s',
              help='Search logs for text')
@click.option('--export', '-e',
              type=click.Choice(['json', 'csv', 'html', 'txt']),
              help='Export logs to format')
@click.option('--output', '-o',
              type=click.Path(path_type=Path),
              help='Output file for export')
@click.pass_context
def logs(ctx, filter: Optional[str], last: Optional[str], 
         device: Optional[str], search: Optional[str],
         export: Optional[str], output: Optional[Path]):
    """View and manage collected logs.
    
    Browse, search, and export logs collected from Android devices.
    Supports filtering by time, device, log level, and text search.
    
    Examples:
      acm logs                           # Show recent logs
      acm logs --filter crash --last 1h # Show crashes from last hour
      acm logs --search "NullPointer"    # Search for specific errors
      acm logs --export json -o report.json # Export to JSON file
    """
    config = ctx.obj['config']
    ui = ctx.obj['console']
    
    # Implementation would go here
    ui.info("Log viewer functionality coming soon!")


@cli.command()
@click.option('--profile', '-p',
              help='Configuration profile name')
@click.option('--list', 'list_profiles', is_flag=True,
              help='List all configuration profiles')
@click.option('--edit', is_flag=True,
              help='Open configuration in editor')
@click.pass_context
def config(ctx, profile: Optional[str], list_profiles: bool, edit: bool):
    """Manage configuration and profiles.
    
    Configure monitoring settings, device preferences, and create
    multiple profiles for different use cases.
    """
    config = ctx.obj['config']
    ui = ctx.obj['console']
    
    # Implementation would go here
    ui.info("Configuration management functionality coming soon!")


def main():
    """Main entry point for the CLI application."""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            console.print_exception()
        sys.exit(1)


if __name__ == '__main__':
    main()