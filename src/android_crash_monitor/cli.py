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

from .core.config import ConfigManager, MonitoringConfig
from .setup.setup import run_setup
from .core.adb import ADBManager
from .ui.console import ConsoleUI
from .utils.logger import get_logger, setup_logging

logger = get_logger(__name__)

# Install rich traceback handler for better error display
install(show_locals=True)

# Global console instance
console = Console()
ui = ConsoleUI()


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
    config_manager = ConfigManager()
    
    # Check if setup is needed
    setup_needed = False
    try:
        app_config = config_manager.get_active_config()
    except Exception:
        setup_needed = True
        app_config = None
    
    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['config'] = app_config
    ctx.obj['config_manager'] = config_manager
    ctx.obj['console'] = ui
    ctx.obj['quiet'] = quiet
    
    # If no subcommand provided, show help or run default action
    if ctx.invoked_subcommand is None:
        if setup_needed:
            console.print("[yellow]First time setup required. Running setup wizard...[/yellow]")
            ctx.invoke(setup)
        else:
            # Show status or help
            console.print(ctx.get_help())


@cli.command()
@click.option('--force', is_flag=True,
              help='Force setup even if already configured')
@click.pass_context
def setup(ctx, force: bool):
    """Run the interactive setup wizard.
    
    The setup wizard will:
    - Detect your system configuration
    - Install ADB if needed
    - Configure Android device connections  
    - Set up monitoring preferences
    - Test the complete workflow
    
    Use --force to reconfigure existing setup.
    """
    import asyncio
    
    config = ctx.obj.get('config')
    config_manager = ctx.obj['config_manager']
    
    # Check if setup already exists
    if config and not force:
        console.print("[yellow]Setup already completed. Use --force to reconfigure.[/yellow]")
        return
    
    try:
        success = asyncio.run(run_setup())
        if success:
            console.print("\n[green]✅ Setup completed successfully![/green]")
            ctx.exit(0)
        else:
            console.print("\n[red]❌ Setup failed or was cancelled.[/red]")
            ctx.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Setup cancelled by user[/yellow]")
        ctx.exit(130)
    except Exception as e:
        console.print(f"\n[red]❌ Setup error: {e}[/red]")
        logger.exception("Setup command failed")
        ctx.exit(1)


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
    
    if not config:
        ui.error("Setup not completed. Run 'acm setup' first.")
        sys.exit(1)
    
    from .core.monitor import AndroidCrashMonitor
    import asyncio
    
    try:
        # Create and start the monitoring engine
        monitor = AndroidCrashMonitor(config, ui)
        
        # Parse device filter
        device_serials = [device] if device else None
        
        # Show monitoring info
        if device:
            ui.info(f"Starting monitoring for device: {device}")
        else:
            ui.info("Starting monitoring for all connected devices")
        
        if output:
            ui.info(f"Output directory: {output}")
            # Update config with custom output directory
            config.output_dir = output
        
        if filter:
            ui.info(f"Filters: {', '.join(filter)}")
            config.default_filters = list(filter)
        
        if duration:
            ui.info(f"Duration: {duration}")
            # TODO: Parse duration and set timeout
        
        # Start monitoring (run in async context)
        asyncio.run(monitor.start_monitoring(device_serials))
        
    except KeyboardInterrupt:
        ui.info("\nMonitoring stopped by user")
    except Exception as e:
        ui.error(f"Monitoring failed: {e}")
        logger.exception("Monitor command failed")
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
    import asyncio
    
    config = ctx.obj['config']
    ui = ctx.obj['console']
    
    if not config:
        ui.error("Setup not completed. Run 'acm setup' first.")
        sys.exit(1)
    
    try:
        adb_manager = ADBManager()
        device_list = asyncio.run(adb_manager.list_devices())
        ui.display_devices(device_list)
        if detailed:
            ui.info("Detailed device information not yet implemented.")
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
    
    # TODO: Implement log viewer functionality
    ui.info("Log viewer functionality coming soon!")
    ui.warning("This will be implemented in the next phase.")


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
    
    config_mgr = ctx.obj['config_manager']
    
    if list_profiles:
        profiles = config_mgr.list_profiles()
        if profiles:
            ui.success(f"Available profiles: {', '.join(profiles)}")
            ui.info(f"Active profile: {config_mgr.active_profile}")
        else:
            ui.warning("No profiles found. Run 'acm setup' to create one.")
        return
    
    if edit:
        ui.info("Configuration editing functionality coming soon!")
        return
    
    # Show current config
    if config:
        ui.info(f"Active profile: {config_mgr.active_profile}")
        ui.info(f"Config directory: {config_mgr.config_dir}")
        # TODO: Display current configuration details
    else:
        ui.warning("No configuration found. Run 'acm setup' first.")


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