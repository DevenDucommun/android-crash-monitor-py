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
from .analysis.crash_analyzer import CrashAnalyzer
from .analysis.report_generator import ReportGenerator

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
    
    Quick Start (Recommended):
      acm start              # 🚀 One-command setup and monitoring
    
    Analysis & Monitoring:
      acm analyze            # 🔍 Analyze crash patterns and system health
      acm monitor            # Start monitoring (requires setup first)
      acm logs --last 1h     # Show logs from last hour
    
    Other Commands:
      acm setup              # Run interactive setup wizard
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
            console.print("[yellow]💡 Tip: Use '[bold green]acm start[/bold green]' for one-command setup and monitoring![/yellow]")
            console.print()
            console.print(ctx.get_help())
        else:
            # Show status and help
            console.print("[green]✅ Android Crash Monitor is configured and ready![/green]")
            console.print("[yellow]💡 Use '[bold green]acm start[/bold green]' to begin monitoring immediately[/yellow]")
            console.print()
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
@click.option('--setup', is_flag=True,
              help='Run setup first if needed')
@click.option('--duration', '-t',
              help='Monitoring duration (e.g., 30m, 2h, 1d)')
@click.pass_context
def start(ctx, setup: bool, duration: Optional[str]):
    """🚀 Start Android crash monitoring - simple one-command setup.
    
    This is the easiest way to start monitoring your Android device.
    It automatically handles setup if needed and begins monitoring.
    
    Perfect for:
    - First time users
    - Quick debugging sessions
    - When you just want to start monitoring immediately
    
    Examples:
      acm start                      # Auto-setup and start monitoring
      acm start --setup              # Force setup then start
      acm start -t 1h                # Monitor for 1 hour then stop
    """
    config = ctx.obj.get('config')
    ui = ctx.obj['console']
    config_manager = ctx.obj['config_manager']
    
    # Welcome message
    ui.success("🚀 Android Crash Monitor - Quick Start")
    ui.info("One-command solution for Android crash monitoring\n")
    
    # Check if setup is needed or forced
    needs_setup = setup or not config
    
    if needs_setup:
        ui.info("⚙️  Running setup first...")
        try:
            import asyncio
            success = asyncio.run(run_setup())
            if not success:
                ui.error("Setup failed. Cannot start monitoring.")
                sys.exit(1)
                
            # Reload config after setup
            config = config_manager.get_active_config()
            ctx.obj['config'] = config
            ui.success("✅ Setup completed!\n")
            
        except KeyboardInterrupt:
            ui.warning("Setup cancelled. Cannot start monitoring.")
            sys.exit(130)
        except Exception as e:
            ui.error(f"Setup failed: {e}")
            sys.exit(1)
    
    # Start monitoring immediately
    ui.info("🎯 Starting enhanced crash monitoring...")
    
    if duration:
        ui.info(f"⏱️  Duration: {duration}")
    
    ui.info("📱 Monitoring all connected devices")
    ui.info("🔍 Enhanced System.err detection enabled")
    ui.info("⚠️  Press Ctrl+C to stop monitoring\n")
    
    # Invoke the monitor command with optimized settings
    try:
        from .core.monitor import AndroidCrashMonitor
        import asyncio
        
        # Create and start the monitoring engine
        monitor = AndroidCrashMonitor(config, ui)
        
        # Start monitoring (run in async context)
        asyncio.run(monitor.start_monitoring(None))  # None = monitor all devices
        
    except KeyboardInterrupt:
        ui.info("\n✅ Monitoring stopped by user")
        ui.info("📊 Check the output directory for crash reports")
    except Exception as e:
        ui.error(f"Monitoring failed: {e}")
        logger.exception("Start command failed")
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
        
        # Apply configuration overrides
        if output:
            config.output_dir = output
        
        if filter:
            config.default_filters = list(filter)
        
        # Show streamlined monitoring info
        target = device if device else "all devices"
        ui.info(f"Monitoring {target} - {config.log_level} level")
        ui.info(f"Output: {config.output_dir}")
        
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
              type=click.Choice(['json', 'csv', 'html', 'txt', 'md', 'compact-json', 'detailed-json', 'excel-csv']),
              help='Export crash data to specified format')
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
    
    from pathlib import Path
    from .exporters import get_exporter, get_available_formats, ExportData
    from .exporters.base import find_crash_files, load_crashes_from_files
    
    try:
        # If export is requested, handle export
        if export:
            ui.info(f"Exporting logs in {export} format...")
            
            # Find crash files in the config output directory
            config_output_dir = Path(config.output_dir) if config else Path.home() / "android_logs"
            ui.info(f"Searching for crash files in: {config_output_dir}")
            
            crash_files = find_crash_files(config_output_dir)
            
            if not crash_files:
                ui.warning("No crash files found to export")
                ui.info("Run 'acm monitor' first to generate crash data")
                return
            
            ui.success(f"Found {len(crash_files)} crash file(s)")
            
            # Load crash data
            ui.info("Loading crash data...")
            crashes = load_crashes_from_files(crash_files)
            
            # Create export data container
            export_data = ExportData()
            export_data.add_crashes(crashes)
            export_data.add_metadata("source", "Android Crash Monitor CLI")
            export_data.add_metadata("crash_files_count", len(crash_files))
            
            # Determine output file
            if output:
                output_path = Path(output)
            else:
                # Generate default filename
                exporter = get_exporter(export)
                filename = exporter.generate_filename("crash_export")
                output_path = Path.cwd() / filename
            
            # Export data
            exporter = get_exporter(export)
            exporter.export(export_data, output_path)
            
            ui.success(f"Export completed: {output_path}")
            ui.info(f"Format: {exporter.format_name}")
            ui.info(f"File size: {output_path.stat().st_size:,} bytes")
            
        else:
            # Show log viewer info (placeholder for now)
            ui.info("Log Viewer Features:")
            ui.info("• Use --export [format] to export crash data")
            ui.info("• Use --filter [type] to filter by crash type")
            ui.info("• Use --search [text] to search in crash descriptions")
            ui.info("• Use --last [period] for time-based filtering")
            
            available_formats = get_available_formats()
            ui.info(f"• Available export formats: {', '.join(available_formats)}")
            
            # Show summary of available data
            if config:
                config_output_dir = Path(config.output_dir)
                if config_output_dir.exists():
                    crash_files = find_crash_files(config_output_dir)
                    if crash_files:
                        ui.success(f"Found {len(crash_files)} crash file(s) in {config_output_dir}")
                        ui.info("Use --export json to export them to a report")
                    else:
                        ui.warning("No crash files found")
                        ui.info("Run 'acm monitor' to start collecting crash data")
                else:
                    ui.warning("Output directory not found")
                    ui.info("Run 'acm setup' to configure the output directory")
    
    except Exception as e:
        ui.error(f"Export failed: {e}")
        logger.exception("Export command failed")
        sys.exit(1)


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
            ui.success(f"Configuration profiles: {', '.join(profiles)}")
        else:
            ui.warning("No configuration found. Run 'acm setup' first.")
        return
    
    if edit:
        ui.info("Configuration editing functionality coming soon!")
        return
    
    # Show current config status
    if config:
        ui.success("Configuration ready for monitoring")
        ui.info(f"Log level: {config.log_level}")
        ui.info(f"Output directory: {config.output_dir}")
        ui.info(f"Log rotation: {'Enabled' if config.auto_rotate_logs else 'Disabled'}")
        if config.auto_rotate_logs:
            size_mb = config.max_log_size // (1024 * 1024)
            ui.info(f"Max log size: {size_mb}MB")
    else:
        ui.warning("No configuration found. Run 'acm setup' first.")


@cli.command()
@click.option('--output', '-o', 
              type=click.Path(path_type=Path),
              help='Output directory for analysis reports')
@click.option('--format', '-f',
              type=click.Choice(['console', 'json', 'markdown', 'all']),
              default='console',
              help='Report format')
@click.option('--summary', is_flag=True,
              help='Generate brief summary only')
@click.pass_context
def analyze(ctx, output: Optional[Path], format: str, summary: bool):
    """🔍 Analyze crash logs for patterns and system health.
    
    Comprehensive crash analysis based on real-world diagnostic experience.
    Identifies critical patterns like database corruption, cascade failures,
    hardware issues, and system instability indicators.
    
    Examples:
      acm analyze                    # Interactive console analysis
      acm analyze --summary          # Brief summary only
      acm analyze -f json -o report.json  # JSON report file
      acm analyze -f all -o /path/   # All formats to directory
    """
    config = ctx.obj.get('config')
    ui = ctx.obj['console']
    
    if not config:
        ui.error("Setup not completed. Run 'acm setup' first.")
        sys.exit(1)
        
    # Determine log directory
    log_directory = Path(config.output_dir)
    if not log_directory.exists():
        ui.error(f"Log directory not found: {log_directory}")
        ui.info("Run 'acm monitor' first to generate crash data")
        sys.exit(1)
        
    try:
        # Initialize analyzer
        ui.info("🔍 Loading crash data for analysis...")
        analyzer = CrashAnalyzer(log_directory)
        crash_count = analyzer.load_crashes()
        
        if crash_count == 0:
            ui.warning("No crash files found to analyze")
            ui.info("Run 'acm monitor' first to generate crash data")
            return
            
        # Generate analysis
        ui.info(f"📊 Analyzing {crash_count:,} crashes...")
        report = analyzer.generate_analysis_report()
        
        # Generate reports based on format
        generator = ReportGenerator(console)
        
        if summary:
            # Just show summary
            summary_text = generator.generate_summary_report(report)
            ui.success(summary_text)
            return
            
        if format in ['console', 'all']:
            generator.generate_console_report(report)
            
        if output and format in ['json', 'all']:
            json_path = output / 'crash_analysis.json' if output.is_dir() else output.with_suffix('.json')
            generator.generate_json_report(report, json_path)
            ui.success(f"JSON report saved: {json_path}")
            
        if output and format in ['markdown', 'all']:
            md_path = output / 'crash_analysis.md' if output.is_dir() else output.with_suffix('.md')
            generator.generate_markdown_report(report, md_path)
            ui.success(f"Markdown report saved: {md_path}")
            
        # Show quick summary
        health = report.get('summary', {}).get('system_health', {})
        status = health.get('status', 'UNKNOWN')
        patterns = len(report.get('critical_patterns', {}))
        
        if status == 'CRITICAL':
            ui.error(f"⚠️ CRITICAL system status with {patterns} critical patterns detected!")
        elif status == 'UNSTABLE':
            ui.warning(f"⚠️ UNSTABLE system with {patterns} patterns - monitor closely")
        elif patterns > 0:
            ui.warning(f"Found {patterns} patterns to investigate")
        else:
            ui.success("✅ System appears stable")
            
    except Exception as e:
        ui.error(f"Analysis failed: {e}")
        logger.exception("Analyze command failed")
        sys.exit(1)


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