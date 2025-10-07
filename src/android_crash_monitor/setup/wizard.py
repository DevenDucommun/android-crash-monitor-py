#!/usr/bin/env python3
"""
Android Crash Monitor - Setup Wizard

Modern, intelligent setup wizard that replaces the complex bash script
with a user-friendly Python implementation featuring:
- Automatic system detection
- Smart package manager integration  
- Direct ADB downloads
- Graceful error handling
- Rich terminal interface
"""

import platform
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import requests

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.table import Table

from ..core.config import Config
from ..core.system import SystemDetector
from ..core.adb import ADBManager
from ..ui.console import ACMConsole


class SetupWizard:
    """Intelligent setup wizard for Android Crash Monitor.
    
    This wizard provides a modern replacement for the bash setup script,
    with enhanced error handling, progress indicators, and user experience.
    """
    
    def __init__(self, config: Config, console: ACMConsole, auto_mode: bool = False):
        self.config = config
        self.console = console  
        self.auto_mode = auto_mode
        self.system = SystemDetector()
        self.adb_manager = ADBManager(console)
        
        # Setup state tracking
        self.state = {
            'system_detected': False,
            'adb_installed': False,
            'device_connected': False,
            'config_saved': False
        }
        
    def run(self) -> None:
        """Run the complete setup wizard workflow."""
        try:
            self._show_welcome()
            self._detect_system()
            self._handle_adb_installation()
            self._detect_devices()
            self._configure_monitoring()
            self._save_configuration()
            self._show_completion()
            
        except KeyboardInterrupt:
            self.console.warning(\"\\nSetup interrupted by user\")
            if Confirm.ask(\"Save partial configuration?\"):
                self._save_configuration()
            raise
        except Exception as e:
            self.console.error(f\"Setup failed: {e}\")
            raise
            
    def _show_welcome(self) -> None:
        \"\"\"Display welcome screen and introduction.\"\"\"
        self.console.clear()
        
        welcome_text = \"\"\"
🚀 Android Crash Monitor Setup

This wizard will help you set up Android crash monitoring with:
• Automatic system detection and configuration
• Intelligent ADB installation with multiple methods  
• Device connection testing and validation
• Monitoring preferences and customization

The setup is designed to be fast, reliable, and user-friendly.
\"\"\"
        
        self.console.print(Panel(welcome_text.strip(), 
                                title=\"[bold blue]Welcome[/bold blue]\",
                                border_style=\"blue\"))
        
        if not self.auto_mode:
            if not Confirm.ask(\"\\n[bold]Ready to begin setup?[/bold]\", default=True):
                raise KeyboardInterrupt(\"User cancelled setup\")
                
    def _detect_system(self) -> None:
        \"\"\"Detect system information and capabilities.\"\"\"
        self.console.step(\"Detecting System Configuration\")
        
        with self.console.status(\"Analyzing system...\"):
            system_info = self.system.detect_all()
            
        # Display system information
        system_table = Table(title=\"System Information\")
        system_table.add_column(\"Component\", style=\"cyan\")
        system_table.add_column(\"Details\", style=\"white\")
        
        system_table.add_row(\"Operating System\", f\"{system_info.os_name} ({system_info.architecture})\")
        system_table.add_row(\"Python Version\", system_info.python_version)
        
        if system_info.package_managers:
            managers = \", \".join(system_info.package_managers)
            system_table.add_row(\"Package Managers\", managers)
        else:
            system_table.add_row(\"Package Managers\", \"[yellow]None detected[/yellow]\")
            
        system_table.add_row(\"Download Tools\", 
                           \"Available\" if system_info.has_download_tools else \"[red]Missing[/red]\")
        
        self.console.print(system_table)
        self.console.success(\"System detection completed\")
        
        # Store system info in config
        self.config.system = system_info
        self.state['system_detected'] = True
        
    def _handle_adb_installation(self) -> None:
        \"\"\"Handle ADB detection and installation.\"\"\"
        self.console.step(\"ADB Installation\")
        
        # First, try to detect existing ADB
        with self.console.status(\"Scanning for existing ADB installation...\"):
            adb_info = self.adb_manager.detect_existing()
            
        if adb_info.installed:
            self.console.success(f\"ADB already installed: {adb_info.version}\")
            self.console.info(f\"Location: {adb_info.path}\")
            
            if not self.auto_mode:
                skip_install = Confirm.ask(\"Skip ADB installation?\", default=True)
                if skip_install:
                    self.config.adb_path = str(adb_info.path)
                    self.state['adb_installed'] = True
                    return
                    
        # Show installation options
        if not adb_info.installed or not self.auto_mode:
            self._show_adb_installation_options()
            
    def _show_adb_installation_options(self) -> None:
        \"\"\"Show available ADB installation methods.\"\"\"
        system_info = self.config.system
        options = []
        
        # Add direct download option if available
        if system_info.has_download_tools:
            options.append((\"auto\", \"⚡ Download and install ADB automatically (recommended)\"))
            
        # Add package manager options
        for pm in system_info.package_managers:
            if pm == \"homebrew\":
                options.append((\"brew\", \"🍺 Install ADB using Homebrew\"))
            elif pm == \"apt\":
                options.append((\"apt\", \"📦 Install ADB using APT (Ubuntu/Debian)\"))
            elif pm == \"dnf\":
                options.append((\"dnf\", \"📦 Install ADB using DNF (Fedora)\")) 
            elif pm == \"pacman\":
                options.append((\"pacman\", \"📦 Install ADB using Pacman (Arch)\"))
            # Add other package managers as needed
                
        # Always add manual option
        options.append((\"manual\", \"📖 Show manual installation instructions\"))
        options.append((\"skip\", \"⏭️  Skip ADB installation (not recommended)\"))
        
        # Display options
        self.console.print(\"\\n[bold]Available installation methods:[/bold]\")
        for i, (key, description) in enumerate(options, 1):
            self.console.print(f\"  {i}. {description}\")
            
        # Get user choice
        if self.auto_mode:
            choice = 1  # Automatic installation
        else:
            while True:
                try:
                    choice = int(Prompt.ask(f\"\\nChoose installation method\", 
                                          choices=[str(i) for i in range(1, len(options) + 1)]))
                    break
                except ValueError:
                    self.console.error(\"Please enter a valid number\")
                    
        # Execute chosen installation method
        selected_key, _ = options[choice - 1]
        self._execute_adb_installation(selected_key)
        
    def _execute_adb_installation(self, method: str) -> None:
        \"\"\"Execute the chosen ADB installation method.\"\"\"
        try:
            if method == \"auto\":
                self._install_adb_automatic()
            elif method == \"brew\":
                self._install_adb_homebrew()
            elif method == \"apt\":
                self._install_adb_apt()
            elif method == \"dnf\":
                self._install_adb_dnf()
            elif method == \"pacman\":
                self._install_adb_pacman()
            elif method == \"manual\":
                self._show_manual_installation()
                return
            elif method == \"skip\":
                self.console.warning(\"Skipping ADB installation - some features will be unavailable\")
                return
                
            # Verify installation
            self._verify_adb_installation()
            
        except Exception as e:
            self.console.error(f\"Installation failed: {e}\")
            if not self.auto_mode:
                if Confirm.ask(\"Try a different installation method?\"):
                    self._show_adb_installation_options()
                    return
            raise
            
    def _install_adb_automatic(self) -> None:
        \"\"\"Install ADB by direct download from Android SDK.\"\"\"
        self.console.info(\"Downloading ADB from official Android SDK...\")
        
        # Determine download URL based on platform
        system_info = self.config.system
        base_url = \"https://dl.google.com/android/repository\"
        
        if system_info.os_name.lower() == \"darwin\":
            filename = \"platform-tools_r36.0.0-darwin.zip\"
        elif system_info.os_name.lower() == \"linux\":
            filename = \"platform-tools_r36.0.0-linux.zip\"
        elif system_info.os_name.lower() == \"windows\":
            filename = \"platform-tools_r36.0.0-windows.zip\"
        else:
            raise ValueError(f\"Unsupported platform: {system_info.os_name}\")
            
        download_url = f\"{base_url}/{filename}\"
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / filename
            
            # Download with progress bar
            self._download_file(download_url, zip_path)
            
            # Extract
            self.console.info(\"Extracting platform tools...\")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
                
            # Install to system location
            platform_tools_dir = temp_path / \"platform-tools\"
            self._install_adb_to_system(platform_tools_dir)
            
    def _download_file(self, url: str, destination: Path) -> None:
        \"\"\"Download file with progress bar.\"\"\"
        with Progress(
            SpinnerColumn(),
            TextColumn(\"[progress.description]{task.description}\"),
            BarColumn(),
            DownloadColumn(),
            console=self.console.console,
        ) as progress:
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            task = progress.add_task(\"Downloading...\", total=total_size)
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
                        
    def _install_adb_to_system(self, platform_tools_dir: Path) -> None:
        \"\"\"Install ADB binary to system location.\"\"\"
        adb_binary = platform_tools_dir / (\"adb.exe\" if platform.system() == \"Windows\" else \"adb\")
        
        if not adb_binary.exists():
            raise FileNotFoundError(\"ADB binary not found in downloaded package\")
            
        # Determine installation directory
        if platform.system() == \"Darwin\":  # macOS
            install_dir = Path(\"/usr/local/bin\")
        elif platform.system() == \"Windows\":
            install_dir = Path.home() / \".local\" / \"bin\"
            install_dir.mkdir(parents=True, exist_ok=True)
        else:  # Linux
            install_dir = Path.home() / \".local\" / \"bin\"
            install_dir.mkdir(parents=True, exist_ok=True)
            
        target_path = install_dir / adb_binary.name
        
        try:
            # Try to copy directly
            shutil.copy2(adb_binary, target_path)
            target_path.chmod(0o755)
            
        except PermissionError:
            # Need sudo for system directories
            if install_dir == Path(\"/usr/local/bin\"):
                self.console.info(\"Administrator privileges required for installation...\")
                cmd = [\"sudo\", \"cp\", str(adb_binary), str(target_path)]
                subprocess.run(cmd, check=True)
                subprocess.run([\"sudo\", \"chmod\", \"755\", str(target_path)], check=True)
            else:
                raise
                
        self.config.adb_path = str(target_path)
        self.console.success(f\"ADB installed to {target_path}\")
        
    def _install_adb_homebrew(self) -> None:
        \"\"\"Install ADB using Homebrew.\"\"\"
        self.console.info(\"Installing ADB via Homebrew...\")
        result = subprocess.run([\"brew\", \"install\", \"android-platform-tools\"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f\"Homebrew installation failed: {result.stderr}\")
        self.console.success(\"ADB installed via Homebrew\")
        
    def _install_adb_apt(self) -> None:
        \"\"\"Install ADB using APT.\"\"\"
        self.console.info(\"Installing ADB via APT...\")
        subprocess.run([\"sudo\", \"apt\", \"update\"], check=True)
        subprocess.run([\"sudo\", \"apt\", \"install\", \"-y\", \"android-tools-adb\"], check=True)
        self.console.success(\"ADB installed via APT\")
        
    def _install_adb_dnf(self) -> None:
        \"\"\"Install ADB using DNF.\"\"\"
        self.console.info(\"Installing ADB via DNF...\")
        subprocess.run([\"sudo\", \"dnf\", \"install\", \"-y\", \"android-tools\"], check=True)
        self.console.success(\"ADB installed via DNF\")
        
    def _install_adb_pacman(self) -> None:
        \"\"\"Install ADB using Pacman.\"\"\"
        self.console.info(\"Installing ADB via Pacman...\")
        subprocess.run([\"sudo\", \"pacman\", \"-S\", \"android-tools\"], check=True)
        self.console.success(\"ADB installed via Pacman\")
        
    def _show_manual_installation(self) -> None:
        \"\"\"Show manual installation instructions.\"\"\"
        system_info = self.config.system
        
        instructions_text = f\"\"\"
📖 Manual ADB Installation Instructions

1. Download Android SDK Platform Tools from:
   https://developer.android.com/studio/releases/platform-tools

2. Extract the downloaded ZIP file to a directory of your choice

3. Add the platform-tools directory to your PATH:
\"\"\"
        
        if system_info.os_name.lower() == \"darwin\":
            instructions_text += \"\"\"
   macOS:
   echo 'export PATH=\"$PATH:/path/to/platform-tools\"' >> ~/.zshrc
   source ~/.zshrc
\"\"\"
        elif system_info.os_name.lower() == \"linux\":
            instructions_text += \"\"\"
   Linux:
   echo 'export PATH=\"$PATH:/path/to/platform-tools\"' >> ~/.bashrc
   source ~/.bashrc
\"\"\"
        elif system_info.os_name.lower() == \"windows\":
            instructions_text += \"\"\"
   Windows:
   - Right-click 'This PC' or 'Computer' > Properties
   - Click 'Advanced system settings'
   - Click 'Environment Variables'
   - Edit the 'Path' variable and add the path to platform-tools directory
\"\"\"
            
        instructions_text += \"\\n4. Restart your terminal and verify: adb version\"
        
        self.console.print(Panel(instructions_text.strip(),
                               title=\"[bold blue]Manual Installation[/bold blue]\",
                               border_style=\"blue\"))
        
        self.console.warning(\"After manual installation, restart this setup wizard.\")
        
    def _verify_adb_installation(self) -> None:
        \"\"\"Verify that ADB is properly installed and accessible.\"\"\"
        with self.console.status(\"Verifying ADB installation...\"):
            adb_info = self.adb_manager.detect_existing()
            
        if adb_info.installed:
            self.console.success(f\"ADB installation verified: {adb_info.version}\")
            self.config.adb_path = str(adb_info.path)
            self.state['adb_installed'] = True
        else:
            raise RuntimeError(\"ADB installation verification failed\")
            
    def _detect_devices(self) -> None:
        \"\"\"Detect connected Android devices.\"\"\"
        if not self.state['adb_installed']:
            self.console.warning(\"Skipping device detection (ADB not installed)\")
            return
            
        self.console.step(\"Device Detection\")
        
        with self.console.status(\"Scanning for Android devices...\"):
            devices = self.adb_manager.list_devices()
            
        if devices:
            self.console.success(f\"Found {len(devices)} Android device(s)\")
            
            # Show device table
            device_table = Table(title=\"Connected Devices\")
            device_table.add_column(\"Device ID\", style=\"cyan\")
            device_table.add_column(\"Model\", style=\"white\")
            device_table.add_column(\"Status\", style=\"green\")
            
            for device in devices:
                device_table.add_row(device.id, device.model or \"Unknown\", device.status)
                
            self.console.print(device_table)
            self.state['device_connected'] = True
            
        else:
            self.console.warning(\"No Android devices found\")
            self._show_device_setup_instructions()
            
    def _show_device_setup_instructions(self) -> None:
        \"\"\"Show instructions for setting up Android device connection.\"\"\"
        instructions = \"\"\"
📱 Android Device Setup

To connect your Android device:

1. Enable Developer Options:
   - Go to Settings > About Phone
   - Tap 'Build Number' 7 times
   - You'll see \"You are now a developer!\"

2. Enable USB Debugging:
   - Go to Settings > Developer Options
   - Turn on 'USB Debugging'

3. Connect via USB:
   - Connect your device with a USB cable
   - Allow USB debugging when prompted

4. Verify connection:
   - Run: adb devices
   - Your device should appear in the list
\"\"\"
        
        self.console.print(Panel(instructions.strip(),
                               title=\"[bold blue]Device Setup[/bold blue]\",
                               border_style=\"blue\"))
        
        if not self.auto_mode:
            if Confirm.ask(\"Continue without device?\", default=False):
                return
                
    def _configure_monitoring(self) -> None:
        \"\"\"Configure monitoring preferences.\"\"\"
        self.console.step(\"Monitoring Configuration\")
        
        # Set reasonable defaults
        self.config.monitoring.auto_start = True
        self.config.monitoring.log_level = \"INFO\"
        self.config.monitoring.max_log_size = \"100MB\"
        self.config.monitoring.retention_days = 30
        
        if not self.auto_mode:
            # Ask for customization
            customize = Confirm.ask(\"Customize monitoring settings?\", default=False)
            if customize:
                self._customize_monitoring_settings()
                
    def _customize_monitoring_settings(self) -> None:
        \"\"\"Allow user to customize monitoring settings.\"\"\"
        # Implementation for custom settings would go here
        self.console.info(\"Monitoring customization coming soon!\")
        
    def _save_configuration(self) -> None:
        \"\"\"Save the configuration to disk.\"\"\"
        self.console.step(\"Saving Configuration\")
        
        try:
            with self.console.status(\"Writing configuration...\"):
                self.config.setup_complete = True
                self.config.save()
                
            self.console.success(\"Configuration saved successfully\")
            self.state['config_saved'] = True
            
        except Exception as e:
            self.console.error(f\"Failed to save configuration: {e}\")
            raise
            
    def _show_completion(self) -> None:
        \"\"\"Show setup completion summary.\"\"\"
        self.console.clear()
        
        # Create status summary
        status_table = Table(title=\"Setup Summary\")
        status_table.add_column(\"Component\", style=\"cyan\")
        status_table.add_column(\"Status\", style=\"white\")
        
        status_table.add_row(\"System Detection\", 
                           \"✅ Complete\" if self.state['system_detected'] else \"❌ Failed\")
        status_table.add_row(\"ADB Installation\", 
                           \"✅ Complete\" if self.state['adb_installed'] else \"❌ Failed\")
        status_table.add_row(\"Device Connection\", 
                           \"✅ Connected\" if self.state['device_connected'] else \"⚠️  No devices\")
        status_table.add_row(\"Configuration\", 
                           \"✅ Saved\" if self.state['config_saved'] else \"❌ Failed\")
        
        self.console.print(status_table)
        
        # Show next steps
        next_steps = \"\"\"
🎉 Setup Complete!

Your Android Crash Monitor is ready to use:

• Start monitoring: acm monitor
• List devices: acm devices  
• View logs: acm logs
• Get help: acm --help

The setup has configured everything automatically for the best experience.
\"\"\"
        
        self.console.print(Panel(next_steps.strip(),
                               title=\"[bold green]Success![/bold green]\",
                               border_style=\"green\"))