#!/usr/bin/env python3
"""
Device Detector UI Module

Handles Android device detection and displays setup instructions.
"""

from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from ...core.adb import ADBManager
from ...core.config import Config
from ...ui.console import ACMConsole


class DeviceDetectorUI:
    """Handles Android device detection and UI presentation."""
    
    def __init__(self, config: Config, console: ACMConsole, adb_manager: ADBManager, auto_mode: bool = False):
        self.config = config
        self.console = console
        self.adb_manager = adb_manager
        self.auto_mode = auto_mode
    
    def detect_and_display(self, adb_installed: bool) -> bool:
        """
        Detect connected Android devices and display them.
        Returns True if at least one device was found.
        """
        if not adb_installed:
            self.console.warning("Skipping device detection (ADB not installed)")
            return False
            
        self.console.step("Device Detection")
        
        with self.console.status("Scanning for Android devices..."):
            devices = self.adb_manager.list_devices()
            
        if devices:
            self.console.success(f"Found {len(devices)} Android device(s)")
            
            # Show device table
            device_table = Table(title="Connected Devices")
            device_table.add_column("Device ID", style="cyan")
            device_table.add_column("Model", style="white")
            device_table.add_column("Status", style="green")
            
            for device in devices:
                device_table.add_row(device.id, device.model or "Unknown", device.status)
                
            self.console.print(device_table)
            return True
            
        else:
            self.console.warning("No Android devices found")
            self.show_device_setup_instructions()
            return False
    
    def show_device_setup_instructions(self) -> None:
        """Show instructions for setting up Android device connection."""
        instructions = """
📱 Android Device Setup

To connect your Android device:

1. Enable Developer Options:
   - Go to Settings > About Phone
   - Tap 'Build Number' 7 times
   - You'll see "You are now a developer!"

2. Enable USB Debugging:
   - Go to Settings > Developer Options
   - Turn on 'USB Debugging'

3. Connect via USB:
   - Connect your device with a USB cable
   - Allow USB debugging when prompted

4. Verify connection:
   - Run: adb devices
   - Your device should appear in the list
"""
        
        self.console.print(Panel(instructions.strip(),
                               title="[bold blue]Device Setup[/bold blue]",
                               border_style="blue"))
        
        if not self.auto_mode:
            if Confirm.ask("Continue without device?", default=False):
                return
