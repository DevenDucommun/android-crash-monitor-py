#!/usr/bin/env python3
"""
ADB Management Module

Handles Android Debug Bridge (ADB) operations including:
- ADB detection and validation
- Device discovery and management
- ADB command execution
- Version checking and updates
"""

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..ui.console import ACMConsole


@dataclass
class ADBInfo:
    """Information about ADB installation."""
    installed: bool = False
    path: Optional[Path] = None
    version: Optional[str] = None
    build_info: Optional[str] = None
    
    
@dataclass
class AndroidDevice:
    """Information about an Android device."""
    id: str
    status: str
    model: Optional[str] = None
    product: Optional[str] = None
    device: Optional[str] = None
    transport_id: Optional[str] = None
    
    @property
    def is_available(self) -> bool:
        """Check if device is available for use."""
        return self.status == 'device'
    
    @property
    def display_name(self) -> str:
        """Get a human-readable device name."""
        if self.model:
            return f"{self.model} ({self.id})"
        return self.id


class ADBManager:
    """Manages ADB operations and device interactions."""
    
    def __init__(self, console: ACMConsole):
        self.console = console
        self._adb_path: Optional[Path] = None
        self._version_cache: Optional[str] = None
    
    def detect_existing(self) -> ADBInfo:
        """Detect existing ADB installation."""
        info = ADBInfo()
        
        # First check if adb is in PATH
        adb_path = shutil.which('adb')
        if adb_path:
            info.installed = True
            info.path = Path(adb_path)
            info.version = self._get_version(Path(adb_path))
            return info
        
        # Check common installation paths
        common_paths = self._get_common_adb_paths()
        
        for path in common_paths:
            if path.exists() and path.is_file():
                try:
                    version = self._get_version(path)
                    if version:
                        info.installed = True
                        info.path = path
                        info.version = version
                        return info
                except Exception:
                    continue
        
        return info
    
    def set_adb_path(self, path: Path) -> bool:
        """Set the ADB path and validate it."""
        if not path.exists():
            return False
            
        version = self._get_version(path)
        if version:
            self._adb_path = path
            self._version_cache = version
            return True
        return False
    
    def get_adb_path(self) -> Optional[Path]:
        """Get the current ADB path."""
        if self._adb_path:
            return self._adb_path
            
        # Try to detect if not set
        info = self.detect_existing()
        if info.installed:
            self._adb_path = info.path
            return self._adb_path
            
        return None
    
    def list_devices(self, refresh: bool = False) -> List[AndroidDevice]:
        """List all connected Android devices."""
        adb_path = self.get_adb_path()
        if not adb_path:
            raise ADBError("ADB not found. Please install ADB first.")
        
        try:
            # Kill and restart ADB server for fresh device list
            if refresh:
                self._run_adb_command(['kill-server'], check_result=False)
                self._run_adb_command(['start-server'], check_result=False)
            
            result = self._run_adb_command(['devices', '-l'])
            devices = self._parse_device_list(result.stdout)
            
            # Get additional device information
            for device in devices:
                if device.is_available:
                    self._populate_device_info(device)
            
            return devices
            
        except subprocess.SubprocessError as e:
            raise ADBError(f"Failed to list devices: {e}")
    
    def get_device_info(self, device_id: str) -> Optional[AndroidDevice]:
        """Get detailed information about a specific device."""
        devices = self.list_devices()
        for device in devices:
            if device.id == device_id:
                return device
        return None
    
    def execute_command(self, device_id: Optional[str], command: List[str], 
                       timeout: int = 30) -> subprocess.CompletedProcess:
        """Execute an ADB command on a specific device."""
        adb_path = self.get_adb_path()
        if not adb_path:
            raise ADBError("ADB not found. Please install ADB first.")
        
        cmd = [str(adb_path)]
        
        if device_id:
            cmd.extend(['-s', device_id])
            
        cmd.extend(command)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result
            
        except subprocess.TimeoutExpired:
            raise ADBError(f"Command timed out after {timeout} seconds")
        except subprocess.CalledProcessError as e:
            raise ADBError(f"ADB command failed: {e.stderr or e.stdout}")
    
    def start_logcat(self, device_id: Optional[str], 
                    filters: Optional[List[str]] = None,
                    buffer: Optional[str] = None,
                    format: str = 'threadtime') -> subprocess.Popen:
        """Start logcat monitoring for a device."""
        cmd = ['logcat']
        
        if buffer:
            cmd.extend(['-b', buffer])
            
        cmd.extend(['-v', format])
        
        if filters:
            cmd.extend(filters)
        
        try:
            process = subprocess.Popen(
                [str(self.get_adb_path())] + 
                (['-s', device_id] if device_id else []) + cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            return process
            
        except Exception as e:
            raise ADBError(f"Failed to start logcat: {e}")
    
    def check_device_connection(self, device_id: str) -> bool:
        """Check if a device is properly connected."""
        try:
            result = self.execute_command(device_id, ['get-state'], timeout=10)
            return result.stdout.strip() == 'device'
        except ADBError:
            return False
    
    def get_device_properties(self, device_id: str, 
                            properties: List[str]) -> Dict[str, str]:
        """Get specific properties from a device."""
        result = {}
        
        try:
            for prop in properties:
                cmd_result = self.execute_command(
                    device_id, 
                    ['shell', 'getprop', prop],
                    timeout=10
                )
                result[prop] = cmd_result.stdout.strip()
                
        except ADBError as e:
            self.console.warning(f"Could not get device properties: {e}")
            
        return result
    
    def _get_version(self, adb_path: Path) -> Optional[str]:
        """Get ADB version from the binary."""
        try:
            result = subprocess.run(
                [str(adb_path), 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse version from output
                # Example: "Android Debug Bridge version 1.0.41"
                match = re.search(r'version\s+([\d.]+)', result.stdout)
                if match:
                    return match.group(1)
                    
                # Fallback: return first line
                first_line = result.stdout.split('\n')[0].strip()
                if first_line:
                    return first_line
                    
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
            
        return None
    
    def _get_common_adb_paths(self) -> List[Path]:
        """Get common ADB installation paths."""
        import platform
        
        paths = []
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            paths.extend([
                Path('/usr/local/bin/adb'),
                Path('/opt/homebrew/bin/adb'),
                Path.home() / 'Library/Android/sdk/platform-tools/adb',
                Path('/Applications/Android Studio.app/Contents/bin/adb'),
            ])
        elif system == 'Linux':
            paths.extend([
                Path('/usr/bin/adb'),
                Path('/usr/local/bin/adb'),
                Path.home() / '.local/bin/adb',
                Path.home() / 'Android/Sdk/platform-tools/adb',
                Path('/opt/android-sdk/platform-tools/adb'),
            ])
        elif system == 'Windows':
            paths.extend([
                Path.home() / 'AppData/Local/Android/Sdk/platform-tools/adb.exe',
                Path('C:/Android/Sdk/platform-tools/adb.exe'),
                Path('C:/Program Files/Android/Android Studio/bin/adb.exe'),
            ])
        
        return paths
    
    def _run_adb_command(self, command: List[str], check_result: bool = True,
                        timeout: int = 30) -> subprocess.CompletedProcess:
        """Run an ADB command."""
        adb_path = self.get_adb_path()
        if not adb_path:
            raise ADBError("ADB not found")
        
        cmd = [str(adb_path)] + command
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check_result
            )
            return result
            
        except subprocess.TimeoutExpired:
            raise ADBError(f"Command timed out: {' '.join(command)}")
        except subprocess.CalledProcessError as e:
            if check_result:
                raise ADBError(f"Command failed: {e.stderr or e.stdout}")
            return e
    
    def _parse_device_list(self, output: str) -> List[AndroidDevice]:
        """Parse device list output from 'adb devices -l'."""
        devices = []
        
        lines = output.strip().split('\n')
        for line in lines[1:]:  # Skip header line
            line = line.strip()
            if not line:
                continue
                
            # Parse device line
            # Format: "device_id status product:... model:... device:... transport_id:..."
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
                
            device_id = parts[0]
            rest = parts[1]
            
            # Split status and properties
            status_and_props = rest.split(None, 1)
            status = status_and_props[0]
            
            device = AndroidDevice(id=device_id, status=status)
            
            # Parse properties if available
            if len(status_and_props) > 1:
                props_str = status_and_props[1]
                props = self._parse_device_properties(props_str)
                
                device.model = props.get('model')
                device.product = props.get('product')
                device.device = props.get('device')
                device.transport_id = props.get('transport_id')
            
            devices.append(device)
            
        return devices
    
    def _parse_device_properties(self, props_str: str) -> Dict[str, str]:
        """Parse device properties from device list output."""
        props = {}
        
        # Properties are in format: "key:value key:value ..."
        for part in props_str.split():
            if ':' in part:
                key, value = part.split(':', 1)
                props[key] = value
                
        return props
    
    def _populate_device_info(self, device: AndroidDevice) -> None:
        """Populate additional device information."""
        if not device.model:
            try:
                properties = self.get_device_properties(
                    device.id, 
                    ['ro.product.model', 'ro.product.manufacturer']
                )
                
                model = properties.get('ro.product.model', '').strip()
                manufacturer = properties.get('ro.product.manufacturer', '').strip()
                
                if manufacturer and model:
                    device.model = f"{manufacturer} {model}"
                elif model:
                    device.model = model
                    
            except Exception:
                # If we can't get properties, use what we have
                pass


class ADBError(Exception):
    """ADB-related errors."""
    pass


# Convenience functions
def detect_adb() -> ADBInfo:
    """Convenience function to detect ADB."""
    from ..ui.console import ACMConsole
    console = ACMConsole()
    manager = ADBManager(console)
    return manager.detect_existing()


def list_android_devices() -> List[AndroidDevice]:
    """Convenience function to list Android devices."""
    from ..ui.console import ACMConsole
    console = ACMConsole()
    manager = ADBManager(console)
    return manager.list_devices()