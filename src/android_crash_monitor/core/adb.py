#!/usr/bin/env python3
"""
ADB Manager for Android Crash Monitor

Handles Android Debug Bridge (ADB) operations including:
- ADB detection and validation  
- Device discovery and management
- Command execution with proper error handling
- Async operations support
"""

import asyncio
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import platform
import re


class ADBNotFoundError(Exception):
    """Raised when ADB cannot be found on the system."""
    pass


class ADBError(Exception):
    """General ADB operation error."""
    pass


@dataclass
class CommandResult:
    """Result of an ADB command execution."""
    returncode: int
    stdout: str
    stderr: str
    
    @property
    def success(self) -> bool:
        return self.returncode == 0


@dataclass
class AndroidDevice:
    """Information about an Android device."""
    serial: str
    status: str  # device, unauthorized, offline, etc.
    model: Optional[str] = None
    product: Optional[str] = None
    device: Optional[str] = None
    transport_id: Optional[str] = None
    
    @property
    def is_online(self) -> bool:
        """Check if device is online and ready."""
        return self.status == "device"
    
    @property
    def display_name(self) -> str:
        """Get human-readable device name."""
        if self.model:
            return f"{self.model} ({self.serial})"
        return self.serial


class ADBManager:
    """Manages ADB operations and device interactions."""
    
    def __init__(self):
        self.adb_path: Optional[Path] = None
        self._detect_adb()
    
    def _detect_adb(self) -> None:
        """Detect ADB installation on the system."""
        # First check PATH
        adb_cmd = shutil.which('adb')
        if adb_cmd:
            self.adb_path = Path(adb_cmd)
            return
        
        # Check common installation paths
        common_paths = self._get_common_adb_paths()
        for path in common_paths:
            if path.exists() and self._is_valid_adb(path):
                self.adb_path = path
                return
        
        raise ADBNotFoundError("ADB not found on system")
    
    def _get_common_adb_paths(self) -> List[Path]:
        """Get common ADB installation paths based on OS."""
        paths = []
        system = platform.system()
        
        if system == "Darwin":  # macOS
            paths.extend([
                Path("/usr/local/bin/adb"),
                Path("/opt/homebrew/bin/adb"),
                Path.home() / "Library/Android/sdk/platform-tools/adb",
                Path("/Applications/Android Studio.app/Contents/bin/adb"),
            ])
        elif system == "Linux":
            paths.extend([
                Path("/usr/bin/adb"),
                Path("/usr/local/bin/adb"),
                Path.home() / ".local/bin/adb",
                Path.home() / "Android/Sdk/platform-tools/adb",
                Path("/opt/android-sdk/platform-tools/adb"),
            ])
        elif system == "Windows":
            paths.extend([
                Path.home() / "AppData/Local/Android/Sdk/platform-tools/adb.exe",
                Path("C:/Android/Sdk/platform-tools/adb.exe"),
                Path("C:/Program Files/Android/Android Studio/bin/adb.exe"),
            ])
        
        return paths
    
    def _is_valid_adb(self, path: Path) -> bool:
        """Check if the given path is a valid ADB executable."""
        try:
            result = subprocess.run(
                [str(path), "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and "Android Debug Bridge" in result.stdout
        except Exception:
            return False
    
    async def run_command(self, command: List[str], timeout: int = 30) -> CommandResult:
        """Run an ADB command asynchronously."""
        if not self.adb_path:
            raise ADBNotFoundError("ADB not available")
        
        cmd = [str(self.adb_path)] + command
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            return CommandResult(
                returncode=process.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else ""
            )
            
        except asyncio.TimeoutError:
            raise ADBError(f"Command timed out after {timeout}s: {' '.join(command)}")
        except Exception as e:
            raise ADBError(f"Failed to execute command: {e}")
    
    async def list_devices(self) -> List[AndroidDevice]:
        """List all connected Android devices."""
        result = await self.run_command(["devices", "-l"])
        
        if not result.success:
            raise ADBError(f"Failed to list devices: {result.stderr}")
        
        devices = []
        lines = result.stdout.strip().split("\n")
        
        for line in lines[1:]:  # Skip "List of devices attached" header
            line = line.strip()
            if not line:
                continue
            
            device = self._parse_device_line(line)
            if device:
                devices.append(device)
        
        return devices
    
    def _parse_device_line(self, line: str) -> Optional[AndroidDevice]:
        """Parse a single device line from adb devices output."""
        # Format: "serial status product:... model:... device:... transport_id:..."
        parts = line.split(None, 1)
        if len(parts) < 2:
            return None
        
        serial = parts[0]
        rest = parts[1]
        
        # Split status and properties
        status_and_props = rest.split(None, 1)
        status = status_and_props[0]
        
        device = AndroidDevice(serial=serial, status=status)
        
        # Parse properties if available
        if len(status_and_props) > 1:
            props_str = status_and_props[1]
            props = self._parse_device_properties(props_str)
            
            device.model = props.get("model")
            device.product = props.get("product")
            device.device = props.get("device")
            device.transport_id = props.get("transport_id")
        
        return device
    
    def _parse_device_properties(self, props_str: str) -> Dict[str, str]:
        """Parse device properties from adb devices -l output."""
        props = {}
        
        # Properties format: "key:value key:value ..."
        for part in props_str.split():
            if ":" in part:
                key, value = part.split(":", 1)
                props[key] = value
        
        return props
    
    async def get_device_property(self, device_serial: str, property_name: str) -> str:
        """Get a specific property from a device."""
        result = await self.run_command([
            "-s", device_serial,
            "shell", "getprop", property_name
        ])
        
        if result.success:
            return result.stdout.strip()
        else:
            raise ADBError(f"Failed to get property {property_name}: {result.stderr}")
    
    async def start_logcat(self, device_serial: Optional[str] = None, 
                          filters: Optional[List[str]] = None) -> asyncio.subprocess.Process:
        """Start logcat monitoring."""
        cmd = ["logcat", "-v", "threadtime"]
        
        if filters:
            cmd.extend(filters)
        
        full_cmd = [str(self.adb_path)]
        if device_serial:
            full_cmd.extend(["-s", device_serial])
        full_cmd.extend(cmd)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return process
        except Exception as e:
            raise ADBError(f"Failed to start logcat: {e}")
