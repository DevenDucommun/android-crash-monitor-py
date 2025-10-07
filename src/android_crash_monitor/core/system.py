#!/usr/bin/env python3
"""
System Detection Module

Provides intelligent system detection capabilities including:
- Operating system and architecture detection
- Package manager discovery
- Download tool availability
- Python environment information
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .config import SystemInfo


class SystemDetector:
    """Detects system information and capabilities."""
    
    def __init__(self):
        self._cache = {}
    
    def detect_all(self) -> SystemInfo:
        """Detect all system information at once."""
        return SystemInfo(
            os=self.get_os_name(),
            version=self.get_os_version(),
            arch=self.get_architecture(),
            python_version=self.get_python_version(),
            package_managers=self.detect_package_managers(),
            download_tools=self.get_download_tools(),
            has_android_sdk=self.get_android_home() is not None,
            has_java=self.get_java_version() is not None,
            java_version=self.get_java_version(),
            is_admin=self.is_admin()
        )
    
    async def get_system_info(self) -> SystemInfo:
        """Get system information (async version for compatibility)."""
        return self.detect_all()
    
    def get_os_name(self) -> str:
        """Get the operating system name."""
        if 'os_name' not in self._cache:
            system = platform.system()
            if system == 'Darwin':
                self._cache['os_name'] = 'macOS'
            elif system == 'Linux':
                self._cache['os_name'] = 'Linux'
            elif system == 'Windows':
                self._cache['os_name'] = 'Windows'
            else:
                self._cache['os_name'] = system
        return self._cache['os_name']
    
    def get_architecture(self) -> str:
        """Get the system architecture."""
        if 'architecture' not in self._cache:
            machine = platform.machine().lower()
            if machine in ('arm64', 'aarch64'):
                self._cache['architecture'] = 'ARM64'
            elif machine in ('x86_64', 'amd64'):
                self._cache['architecture'] = 'x64'
            elif machine in ('i386', 'i686', 'x86'):
                self._cache['architecture'] = 'x86'
            else:
                self._cache['architecture'] = machine.upper()
        return self._cache['architecture']
    
    def get_os_version(self) -> str:
        """Get the operating system version."""
        if 'os_version' not in self._cache:
            try:
                system = platform.system()
                if system == 'Darwin':
                    # macOS version
                    version = platform.mac_ver()[0]
                elif system == 'Linux':
                    # Linux distribution version
                    try:
                        with open('/etc/os-release', 'r') as version_file:
                            version = None
                            for line in version_file:
                                if line.startswith('VERSION='):
                                    version = line.split('=')[1].strip().strip('"')
                                    break
                            if not version:
                                version = platform.release()
                    except FileNotFoundError:
                        version = platform.release()
                elif system == 'Windows':
                    version = platform.release()
                else:
                    version = platform.release()
                self._cache['os_version'] = version or 'Unknown'
            except Exception:
                self._cache['os_version'] = 'Unknown'
        return self._cache['os_version']
    
    def get_download_tools(self) -> List[str]:
        """Get available download tools."""
        if 'download_tools' not in self._cache:
            tools = []
            if self._command_exists('curl'):
                tools.append('curl')
            if self._command_exists('wget'):
                tools.append('wget')
            self._cache['download_tools'] = tools
        return self._cache['download_tools']
    
    def get_python_version(self) -> str:
        """Get the Python version."""
        if 'python_version' not in self._cache:
            version = sys.version_info
            self._cache['python_version'] = f"{version.major}.{version.minor}.{version.micro}"
        return self._cache['python_version']
    
    def detect_package_managers(self) -> List[str]:
        """Detect available package managers."""
        if 'package_managers' not in self._cache:
            managers = []
            
            # Define package managers by platform
            candidates = {
                'macOS': [
                    ('brew', 'Homebrew'),
                    ('port', 'MacPorts'),
                ],
                'Linux': [
                    ('apt', 'APT'),
                    ('dnf', 'DNF'),
                    ('yum', 'YUM'),
                    ('pacman', 'Pacman'),
                    ('zypper', 'Zypper'),
                    ('emerge', 'Portage'),
                    ('apk', 'Alpine Package Keeper'),
                ],
                'Windows': [
                    ('choco', 'Chocolatey'),
                    ('winget', 'Windows Package Manager'),
                    ('scoop', 'Scoop'),
                ]
            }
            
            os_name = self.get_os_name()
            if os_name in candidates:
                for cmd, name in candidates[os_name]:
                    if self._command_exists(cmd):
                        managers.append(cmd)
            
            self._cache['package_managers'] = managers
        return self._cache['package_managers']
    
    def has_download_tools(self) -> bool:
        """Check if download tools (curl, wget) are available."""
        if 'has_download_tools' not in self._cache:
            has_curl = self._command_exists('curl')
            has_wget = self._command_exists('wget')
            self._cache['has_download_tools'] = has_curl or has_wget
        return self._cache['has_download_tools']
    
    def get_shell(self) -> str:
        """Get the current shell."""
        if 'shell' not in self._cache:
            shell = Path(os.environ.get('SHELL', '/bin/bash')).name
            self._cache['shell'] = shell
        return self._cache['shell']
    
    def get_terminal(self) -> Optional[str]:
        """Get the terminal emulator name."""
        if 'terminal' not in self._cache:
            terminal = None
            
            # Try to detect terminal from environment variables
            term_program = os.environ.get('TERM_PROGRAM')
            if term_program:
                terminal = term_program
            else:
                term = os.environ.get('TERM')
                if term:
                    terminal = term
            
            self._cache['terminal'] = terminal
        return self._cache['terminal']
    
    def is_admin(self) -> bool:
        """Check if running with administrator privileges."""
        if 'is_admin' not in self._cache:
            try:
                if self.get_os_name() == 'Windows':
                    import ctypes
                    self._cache['is_admin'] = ctypes.windll.shell32.IsUserAnAdmin() != 0
                else:
                    self._cache['is_admin'] = os.getuid() == 0
            except (ImportError, AttributeError, OSError):
                self._cache['is_admin'] = False
        return self._cache['is_admin']
    
    def get_java_version(self) -> Optional[str]:
        """Get Java version if available."""
        if 'java_version' not in self._cache:
            try:
                result = subprocess.run(['java', '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse version from stderr (Java outputs version to stderr)
                    version_line = result.stderr.split('\n')[0]
                    # Extract version number using regex
                    import re
                    match = re.search(r'"([^"]*)"', version_line)
                    if match:
                        self._cache['java_version'] = match.group(1)
                    else:
                        self._cache['java_version'] = 'Unknown'
                else:
                    self._cache['java_version'] = None
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                self._cache['java_version'] = None
        return self._cache['java_version']
    
    def get_android_home(self) -> Optional[Path]:
        """Get Android SDK home directory."""
        if 'android_home' not in self._cache:
            android_home = None
            
            # Check environment variables
            for env_var in ['ANDROID_HOME', 'ANDROID_SDK_ROOT']:
                path = os.environ.get(env_var)
                if path and Path(path).is_dir():
                    android_home = Path(path)
                    break
            
            # Check common installation locations
            if not android_home:
                common_paths = []
                if self.get_os_name() == 'macOS':
                    common_paths = [
                        Path.home() / 'Library/Android/sdk',
                        Path('/usr/local/share/android-sdk'),
                        Path('/opt/homebrew/share/android-sdk'),
                    ]
                elif self.get_os_name() == 'Linux':
                    common_paths = [
                        Path.home() / 'Android/Sdk',
                        Path('/usr/lib/android-sdk'),
                        Path('/opt/android-sdk'),
                    ]
                elif self.get_os_name() == 'Windows':
                    common_paths = [
                        Path.home() / 'AppData/Local/Android/Sdk',
                        Path('C:/Android/Sdk'),
                    ]
                
                for path in common_paths:
                    if path.is_dir() and (path / 'platform-tools').is_dir():
                        android_home = path
                        break
            
            self._cache['android_home'] = android_home
        return self._cache['android_home']
    
    def get_system_info_dict(self) -> dict:
        """Get all system information as a dictionary."""
        info = self.detect_all()
        result = {
            'os_name': info.os_name,
            'architecture': info.architecture,
            'python_version': info.python_version,
            'package_managers': info.package_managers,
            'has_download_tools': info.has_download_tools,
            'shell': self.get_shell(),
            'terminal': self.get_terminal(),
            'is_admin': self.is_admin(),
            'java_version': self.get_java_version(),
            'android_home': str(self.get_android_home()) if self.get_android_home() else None,
        }
        return result
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        return shutil.which(command) is not None
    
    def clear_cache(self) -> None:
        """Clear the detection cache."""
        self._cache.clear()


# Convenience functions
def detect_system() -> SystemInfo:
    """Convenience function to detect system information."""
    detector = SystemDetector()
    return detector.detect_all()


def get_os_name() -> str:
    """Get the operating system name."""
    detector = SystemDetector()
    return detector.get_os_name()


def get_package_managers() -> List[str]:
    """Get available package managers."""
    detector = SystemDetector()
    return detector.detect_package_managers()