#!/usr/bin/env python3
"""
Android Crash Monitor - Setup Wizard (Refactored)

Modern, intelligent setup wizard that orchestrates specialized modules for:
- System detection
- ADB installation
- Device detection
- Configuration management
"""

from rich.prompt import Confirm

from ..core.adb import ADBManager
from ..core.config import Config
from ..core.system import SystemDetector
from ..ui.console import ACMConsole
from .detectors import DeviceDetectorUI, SystemDetectorUI
from .installers import ADBInstaller
from .ui import WizardUI


class SetupWizard:
    """
    Intelligent setup wizard for Android Crash Monitor.
    
    This wizard orchestrates specialized modules to provide a clean,
    maintainable setup experience with proper separation of concerns.
    """
    
    def __init__(self, config: Config, console: ACMConsole, auto_mode: bool = False):
        self.config = config
        self.console = console  
        self.auto_mode = auto_mode
        
        # Initialize core managers
        self.system = SystemDetector()
        self.adb_manager = ADBManager(console)
        
        # Initialize UI components
        self.ui = WizardUI(console, auto_mode)
        self.system_detector = SystemDetectorUI(config, console)
        self.device_detector = DeviceDetectorUI(config, console, self.adb_manager, auto_mode)
        self.adb_installer = ADBInstaller(config, console, self.adb_manager, auto_mode)
        
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
            # Welcome screen
            if not self.ui.show_welcome():
                raise KeyboardInterrupt("User cancelled setup")
            
            # System detection
            self.state['system_detected'] = self.system_detector.detect_and_display()
            
            # ADB installation
            self.state['adb_installed'] = self.adb_installer.handle_installation()
            
            # Device detection
            self.state['device_connected'] = self.device_detector.detect_and_display(
                self.state['adb_installed']
            )
            
            # Monitoring configuration
            self.ui.configure_monitoring(self.config)
            
            # Save configuration
            self.state['config_saved'] = self.ui.save_configuration(self.config)
            
            # Completion summary
            self.ui.show_completion(self.state)
            
        except KeyboardInterrupt:
            self.console.warning("\nSetup interrupted by user")
            if Confirm.ask("Save partial configuration?"):
                self.ui.save_configuration(self.config)
            raise
        except Exception as e:
            self.console.error(f"Setup failed: {e}")
            raise
