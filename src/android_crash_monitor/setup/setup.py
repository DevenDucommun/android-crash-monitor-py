"""
Setup wizard for Android Crash Monitor.

This module provides an interactive setup experience that:
- Detects system capabilities and existing tools
- Guides ADB installation if needed
- Discovers and configures Android devices
- Creates monitoring profiles and configurations
- Validates the complete setup
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from ..core.adb import ADBManager, ADBNotFoundError
from ..core.config import ConfigManager, MonitoringConfig
from ..core.system import SystemDetector
from ..ui.console import ConsoleUI
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SetupWizard:
    """Interactive setup wizard for Android Crash Monitor."""
    
    def __init__(self):
        self.console = Console()
        self.ui = ConsoleUI()
        self.system_detector = SystemDetector()
        self.config_manager = ConfigManager()
        self.adb_manager: Optional[ADBManager] = None
        
        # Setup state
        self.system_info = None
        self.adb_path: Optional[Path] = None
        self.detected_devices = []
        self.setup_profile = "default"
    
    async def run(self) -> bool:
        """
        Run the complete setup wizard.
        
        Returns:
            bool: True if setup completed successfully, False otherwise
        """
        try:
            self._show_welcome()
            
            # Step 1: System Detection
            if not await self._detect_system():
                return False
            
            # Step 2: ADB Setup
            if not await self._setup_adb():
                return False
            
            # Step 3: Device Discovery
            if not await self._discover_devices():
                return False
            
            # Step 4: Configuration
            if not await self._create_configuration():
                return False
            
            # Step 5: Final Validation
            if not await self._validate_setup():
                return False
            
            self._show_completion()
            return True
            
        except KeyboardInterrupt:
            self.ui.error("\n\nSetup interrupted by user.")
            return False
        except Exception as e:
            logger.exception("Setup wizard failed")
            self.ui.error(f"Setup failed: {e}")
            return False
    
    def _show_welcome(self) -> None:
        """Display welcome message and setup overview."""
        self.console.clear()
        
        title = Text("Android Crash Monitor Setup", style="bold blue")
        welcome_text = """
🚀 Quick setup to get you monitoring Android crashes!

This will:
• Configure ADB if needed
• Detect connected devices  
• Set up monitoring with smart defaults

Typically takes 1-2 minutes.
        """.strip()
        
        panel = Panel(
            Align.center(welcome_text),
            title=title,
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
        if not Confirm.ask("Ready to begin?", default=True):
            self.ui.info("Setup cancelled by user.")
            sys.exit(0)
    
    async def _detect_system(self) -> bool:
        """Detect system capabilities and present findings."""
        self.ui.header("System Detection")
        
        with self.ui.spinner("Analyzing your system..."):
            self.system_info = await self.system_detector.get_system_info()
        
        # Display essential system information
        self.ui.success(f"System: {self.system_info.os} ({self.system_info.arch})")
        
        if not self.system_info.download_tools:
            self.ui.error("No download tools (curl/wget) found")
            return False
        
        # Check for existing Android development tools
        if self.system_info.has_android_sdk:
            self.ui.success("Android SDK detected")
        
        self.console.print()
        return True
    
    async def _setup_adb(self) -> bool:
        """Handle ADB detection and installation."""
        self.ui.header("ADB Setup")
        
        # Try to detect existing ADB
        try:
            self.adb_manager = ADBManager()
            adb_version = await self._get_adb_version()
            self.ui.success(f"ADB ready: {adb_version}")
            self.console.print()
            return True
            
        except ADBNotFoundError:
            self.ui.warning("ADB not found on your system")
        
        # Offer installation options
        return await self._install_adb()
    
    async def _install_adb(self) -> bool:
        """Guide user through ADB installation."""
        installation_methods = self._get_installation_methods()
        
        if not installation_methods:
            self.ui.error("No automatic installation methods available for your system")
            self._show_manual_installation_guide()
            return await self._verify_manual_installation()
        
        self.ui.info("ADB installation options:")
        for i, (method, description) in enumerate(installation_methods, 1):
            self.console.print(f"  {i}. {description}")
        
        self.console.print(f"  {len(installation_methods) + 1}. Manual installation (I'll install it myself)")
        
        while True:
            try:
                choice = Prompt.ask(
                    "Choose installation method",
                    choices=[str(i) for i in range(1, len(installation_methods) + 2)],
                    default="1"
                )
                choice_idx = int(choice) - 1
                break
            except (ValueError, KeyboardInterrupt):
                self.ui.error("Invalid choice. Please try again.")
        
        if choice_idx == len(installation_methods):
            # Manual installation chosen
            self._show_manual_installation_guide()
            return await self._verify_manual_installation()
        
        # Automatic installation
        method, description = installation_methods[choice_idx]
        return await self._run_automatic_installation(method)
    
    def _get_installation_methods(self) -> List[Tuple[str, str]]:
        """Get available ADB installation methods based on system."""
        methods = []
        
        if "brew" in self.system_info.package_managers:
            methods.append(("brew", "Homebrew: brew install android-platform-tools"))
        
        if "apt" in self.system_info.package_managers:
            methods.append(("apt", "APT: sudo apt install android-tools-adb"))
        
        if "dnf" in self.system_info.package_managers:
            methods.append(("dnf", "DNF: sudo dnf install android-tools"))
        
        if "pacman" in self.system_info.package_managers:
            methods.append(("pacman", "Pacman: sudo pacman -S android-tools"))
        
        if "zypper" in self.system_info.package_managers:
            methods.append(("zypper", "Zypper: sudo zypper install android-tools"))
        
        return methods
    
    async def _run_automatic_installation(self, method: str) -> bool:
        """Run automatic ADB installation using the specified method."""
        commands = {
            "brew": ["brew", "install", "android-platform-tools"],
            "apt": ["sudo", "apt", "update", "&&", "sudo", "apt", "install", "-y", "android-tools-adb"],
            "dnf": ["sudo", "dnf", "install", "-y", "android-tools"],
            "pacman": ["sudo", "pacman", "-S", "--noconfirm", "android-tools"],
            "zypper": ["sudo", "zypper", "install", "-y", "android-tools"]
        }
        
        if method not in commands:
            self.ui.error(f"Unknown installation method: {method}")
            return False
        
        command = commands[method]
        
        self.ui.info(f"Running: {' '.join(command)}")
        
        if not Confirm.ask("Proceed with installation?", default=True):
            return False
        
        try:
            with self.ui.spinner(f"Installing ADB via {method}..."):
                if method == "apt":
                    # APT needs special handling for the && operator
                    result1 = subprocess.run(["sudo", "apt", "update"], 
                                           capture_output=True, text=True, timeout=300)
                    if result1.returncode != 0:
                        raise subprocess.CalledProcessError(result1.returncode, "apt update")
                    
                    result = subprocess.run(["sudo", "apt", "install", "-y", "android-tools-adb"],
                                          capture_output=True, text=True, timeout=300)
                else:
                    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.ui.success("ADB installed successfully!")
                
                # Try to initialize ADB manager again
                try:
                    self.adb_manager = ADBManager()
                    adb_version = await self._get_adb_version()
                    self.ui.success(f"ADB verified: {adb_version}")
                    return True
                except ADBNotFoundError:
                    self.ui.warning("Installation completed but ADB still not found in PATH")
                    self.ui.info("You may need to restart your terminal or add ADB to your PATH")
                    return await self._verify_manual_installation()
            else:
                self.ui.error(f"Installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.ui.error("Installation timed out")
            return False
        except subprocess.CalledProcessError as e:
            self.ui.error(f"Installation failed: {e}")
            return False
        except Exception as e:
            self.ui.error(f"Unexpected error during installation: {e}")
            return False
    
    def _show_manual_installation_guide(self) -> None:
        """Show manual ADB installation instructions."""
        os_guides = {
            "Darwin": """
For macOS, you can install ADB using:

1. Homebrew (recommended):
   brew install android-platform-tools

2. Download Android SDK Platform Tools:
   - Visit: https://developer.android.com/studio/releases/platform-tools
   - Download the macOS version
   - Extract and add to your PATH

3. Install Android Studio (includes ADB):
   - Download from: https://developer.android.com/studio
   - ADB will be in: ~/Library/Android/sdk/platform-tools/
            """.strip(),
            
            "Linux": """
For Linux, you can install ADB using:

1. Package manager:
   - Ubuntu/Debian: sudo apt install android-tools-adb
   - Fedora/CentOS: sudo dnf install android-tools
   - Arch Linux: sudo pacman -S android-tools

2. Download Android SDK Platform Tools:
   - Visit: https://developer.android.com/studio/releases/platform-tools
   - Download the Linux version
   - Extract and add to your PATH
            """.strip(),
            
            "Windows": """
For Windows, you can install ADB using:

1. Download Android SDK Platform Tools:
   - Visit: https://developer.android.com/studio/releases/platform-tools
   - Download the Windows version
   - Extract to a folder (e.g., C:\\platform-tools)
   - Add the folder to your PATH environment variable

2. Install via Chocolatey:
   choco install adb

3. Install Android Studio (includes ADB):
   - Download from: https://developer.android.com/studio
            """.strip()
        }
        
        guide = os_guides.get(self.system_info.os, "Please install ADB for your operating system")
        
        panel = Panel(
            guide,
            title="Manual ADB Installation",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    async def _verify_manual_installation(self) -> bool:
        """Wait for user to manually install ADB and verify."""
        self.ui.info("Please install ADB using the instructions above.")
        
        while True:
            if Confirm.ask("Have you installed ADB?", default=False):
                try:
                    self.adb_manager = ADBManager()
                    adb_version = await self._get_adb_version()
                    self.ui.success(f"ADB verified: {adb_version}")
                    return True
                except ADBNotFoundError:
                    self.ui.error("ADB still not found. Please check your installation.")
                    if not Confirm.ask("Try again?", default=True):
                        return False
            else:
                if not Confirm.ask("Continue without ADB verification?", default=False):
                    return False
                else:
                    return True
    
    async def _get_adb_version(self) -> str:
        """Get ADB version string."""
        try:
            result = await self.adb_manager.run_command(["version"], timeout=5)
            return result.stdout.split('\n')[0] if result.stdout else "Unknown version"
        except Exception:
            return "Unknown version"
    
    async def _discover_devices(self) -> bool:
        """Discover and configure Android devices."""
        self.ui.header("Device Discovery")
        
        if not self.adb_manager:
            self.ui.warning("Skipping device discovery (ADB not available)")
            return True
        
        # Start ADB server
        with self.ui.spinner("Starting ADB server..."):
            try:
                await self.adb_manager.run_command(["start-server"], timeout=10)
            except Exception as e:
                self.ui.warning(f"Failed to start ADB server: {e}")
        
        # Discover devices
        with self.ui.spinner("Scanning for connected devices..."):
            self.detected_devices = await self.adb_manager.list_devices()
        
        if not self.detected_devices:
            self.ui.warning("No devices detected")
            self._show_device_connection_guide()
            
            # Wait for devices
            return await self._wait_for_devices()
        
        # Display found devices
        ready_devices = [d for d in self.detected_devices if d.status == "device"]
        if ready_devices:
            self.ui.success(f"Found {len(ready_devices)} ready device(s)")
        else:
            self.ui.warning(f"Found {len(self.detected_devices)} device(s) but none ready")
        
        # Check device states
        return await self._validate_device_states()
    
    def _show_device_connection_guide(self) -> None:
        """Show guide for connecting Android devices."""
        guide = """
To connect your Android device:

1. Enable Developer Options:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   - You'll see "Developer options enabled"

2. Enable USB Debugging:
   - Go to Settings → Developer Options
   - Turn on "USB Debugging"
   - Connect your device via USB cable

3. Trust this computer:
   - When prompted on your device, tap "Allow USB Debugging"
   - Check "Always allow from this computer" (recommended)

4. Verify connection:
   - Your device should appear in the device list below
        """.strip()
        
        panel = Panel(
            guide,
            title="Connect Android Device",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    async def _wait_for_devices(self) -> bool:
        """Wait for user to connect devices."""
        max_attempts = 6  # 30 seconds total
        attempt = 0
        
        while attempt < max_attempts:
            if Confirm.ask("Check for devices now?", default=True):
                with self.ui.spinner("Scanning for devices..."):
                    self.detected_devices = await self.adb_manager.list_devices()
                
                if self.detected_devices:
                    self.ui.success(f"Found {len(self.detected_devices)} device(s):")
                    self.ui.display_devices(self.detected_devices)
                    return await self._validate_device_states()
                else:
                    self.ui.warning("Still no devices detected")
                    attempt += 1
            else:
                break
        
        return Confirm.ask("Continue setup without devices?", default=True)
    
    async def _validate_device_states(self) -> bool:
        """Validate that devices are in a good state for monitoring."""
        unauthorized_devices = [d for d in self.detected_devices if d.status == "unauthorized"]
        offline_devices = [d for d in self.detected_devices if d.status == "offline"]
        
        if unauthorized_devices:
            self.ui.warning(f"{len(unauthorized_devices)} device(s) unauthorized")
            self.ui.info("Please check your device(s) and allow USB debugging")
            
            if Confirm.ask("Wait for authorization?", default=True):
                return await self._wait_for_authorization()
        
        if offline_devices:
            self.ui.warning(f"{len(offline_devices)} device(s) offline")
            self.ui.info("Please check USB connection and device state")
        
        online_devices = [d for d in self.detected_devices if d.status == "device"]
        if online_devices:
            self.ui.success(f"{len(online_devices)} device(s) ready for monitoring")
        
        return True
    
    async def _wait_for_authorization(self) -> bool:
        """Wait for devices to be authorized."""
        for attempt in range(3):
            self.ui.info(f"Attempt {attempt + 1}/3 - Please check your device(s) for authorization prompts")
            
            with self.ui.spinner("Waiting for authorization..."):
                await asyncio.sleep(5)
                self.detected_devices = await self.adb_manager.list_devices()
            
            unauthorized = [d for d in self.detected_devices if d.status == "unauthorized"]
            if not unauthorized:
                self.ui.success("All devices authorized!")
                self.ui.display_devices(self.detected_devices)
                return True
            
            if attempt < 2:  # Not the last attempt
                if not Confirm.ask("Try again?", default=True):
                    break
        
        return True  # Continue even if not all devices are authorized
    
    async def _create_configuration(self) -> bool:
        """Create initial configuration profiles."""
        self.ui.header("Configuration Setup")
        
        # Use automatic profile naming
        profile_name = "default"
        self.setup_profile = profile_name
        
        # Create monitoring configuration with smart defaults
        config = MonitoringConfig()
        
        # Configure based on detected devices
        if self.detected_devices:
            device_serials = [d.serial for d in self.detected_devices if d.status == "device"]
            if device_serials:
                config.target_devices = device_serials
        
        # Set ADB path if we found it
        if self.adb_manager and self.adb_manager.adb_path:
            config.adb_path = str(self.adb_manager.adb_path)
        
        # Set log level to DEBUG automatically (capture all logs)
        config.log_level = "DEBUG"
        
        # Output directory with smart defaults
        default_output = self.config_manager.get_logs_dir()
        
        if Confirm.ask(f"Use default log directory ({default_output})?", default=True):
            config.output_dir = default_output
        else:
            output_dir = Prompt.ask(
                "Custom log directory",
                default=str(default_output)
            )
            config.output_dir = Path(output_dir)
        
        # Auto-configure log rotation with smart defaults
        config.auto_rotate_logs = True
        default_size_mb = 50  # 50MB default for better performance
        
        if Confirm.ask(f"Use default max log file size ({default_size_mb}MB)?", default=True):
            config.max_log_size = default_size_mb * 1024 * 1024
        else:
            max_size = Prompt.ask(
                "Custom max log file size (MB)",
                default=str(default_size_mb)
            )
            try:
                config.max_log_size = int(max_size) * 1024 * 1024  # Convert to bytes
            except ValueError:
                config.max_log_size = default_size_mb * 1024 * 1024  # Fallback to default
                self.ui.warning(f"Invalid size, using default: {default_size_mb}MB")
        
        # Save configuration
        try:
            self.config_manager.save_profile(profile_name, config)
            self.config_manager.set_active_profile(profile_name)
            
            self.ui.success(f"Configuration saved as '{profile_name}' profile")
            
            return True
            
        except Exception as e:
            self.ui.error(f"Failed to save configuration: {e}")
            return False
    
    async def _validate_setup(self) -> bool:
        """Perform final validation of the complete setup."""
        self.ui.header("Setup Validation")
        
        validation_results = []
        
        # Check ADB
        if self.adb_manager:
            try:
                with self.ui.spinner("Testing ADB connectivity..."):
                    devices = await self.adb_manager.list_devices()
                validation_results.append(("ADB", True, f"Working - {len(devices)} device(s) detected"))
            except Exception as e:
                validation_results.append(("ADB", False, f"Error: {e}"))
        else:
            validation_results.append(("ADB", False, "Not configured"))
        
        # Check configuration
        try:
            active_config = self.config_manager.get_active_config()
            validation_results.append(("Configuration", True, f"Ready for monitoring"))
        except Exception as e:
            validation_results.append(("Configuration", False, f"Error: {e}"))
        
        # Check output directory
        try:
            config = self.config_manager.get_active_config()
            if config.output_dir.exists() or config.output_dir.parent.exists():
                validation_results.append(("Output Directory", True, str(config.output_dir)))
            else:
                config.output_dir.mkdir(parents=True, exist_ok=True)
                validation_results.append(("Output Directory", True, f"Created: {config.output_dir}"))
        except Exception as e:
            validation_results.append(("Output Directory", False, f"Error: {e}"))
        
        # Display validation results
        self.console.print()
        for component, success, message in validation_results:
            if success:
                self.ui.success(f"{component}: {message}")
            else:
                self.ui.error(f"{component}: {message}")
        
        # Overall result
        all_passed = all(result[1] for result in validation_results)
        
        self.console.print()
        if all_passed:
            self.ui.success("✅ All validation checks passed!")
        else:
            self.ui.warning("⚠️  Some validation checks failed")
            
            if not Confirm.ask("Continue despite validation failures?", default=True):
                return False
        
        return True
    
    def _show_completion(self) -> None:
        """Show setup completion message with next steps."""
        completion_text = """
🎉 Setup Complete!

Your Android Crash Monitor is ready!

Start monitoring: acm monitor
View devices: acm devices
Get help: acm --help
        """.strip()
        
        panel = Panel(
            Align.center(completion_text),
            title=Text("Setup Complete", style="bold green"),
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()


async def run_setup() -> bool:
    """
    Run the setup wizard.
    
    Returns:
        bool: True if setup completed successfully
    """
    wizard = SetupWizard()
    return await wizard.run()


if __name__ == "__main__":
    # For testing the setup wizard directly
    asyncio.run(run_setup())