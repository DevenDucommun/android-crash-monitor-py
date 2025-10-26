#!/usr/bin/env python3
"""
ADB Installer Module

Handles all ADB installation methods including:
- Automatic download from Android SDK
- Package manager installations (Homebrew, APT, DNF, Pacman)
- Manual installation instructions
- Installation verification
"""

import platform
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import requests
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn
from rich.prompt import Confirm, Prompt

from ...core.adb import ADBManager
from ...core.config import Config
from ...ui.console import ACMConsole


class ADBInstaller:
    """Manages ADB installation through various methods."""
    
    def __init__(self, config: Config, console: ACMConsole, adb_manager: ADBManager, auto_mode: bool = False):
        self.config = config
        self.console = console
        self.adb_manager = adb_manager
        self.auto_mode = auto_mode
        
    def handle_installation(self) -> bool:
        """
        Main entry point for ADB installation.
        Returns True if ADB is installed successfully, False otherwise.
        """
        self.console.step("ADB Installation")
        
        # First, try to detect existing ADB
        with self.console.status("Scanning for existing ADB installation..."):
            adb_info = self.adb_manager.detect_existing()
            
        if adb_info.installed:
            self.console.success(f"ADB already installed: {adb_info.version}")
            self.console.info(f"Location: {adb_info.path}")
            
            if not self.auto_mode:
                skip_install = Confirm.ask("Skip ADB installation?", default=True)
                if skip_install:
                    self.config.adb_path = str(adb_info.path)
                    return True
                    
        # Show installation options
        if not adb_info.installed or not self.auto_mode:
            return self._show_installation_options()
            
        return False
    
    def _show_installation_options(self) -> bool:
        """Show available ADB installation methods and execute chosen method."""
        system_info = self.config.system
        options = []
        
        # Add direct download option if available
        if system_info.get('has_download_tools', False):
            options.append(("auto", "⚡ Download and install ADB automatically (recommended)"))
            
        # Add package manager options
        package_managers = system_info.get('package_managers', [])
        for pm in package_managers:
            if pm == "homebrew":
                options.append(("brew", "🍺 Install ADB using Homebrew"))
            elif pm == "apt":
                options.append(("apt", "📦 Install ADB using APT (Ubuntu/Debian)"))
            elif pm == "dnf":
                options.append(("dnf", "📦 Install ADB using DNF (Fedora)")) 
            elif pm == "pacman":
                options.append(("pacman", "📦 Install ADB using Pacman (Arch)"))
                
        # Always add manual option
        options.append(("manual", "📖 Show manual installation instructions"))
        options.append(("skip", "⏭️  Skip ADB installation (not recommended)"))
        
        # Display options
        self.console.print("\\n[bold]Available installation methods:[/bold]")
        for i, (key, description) in enumerate(options, 1):
            self.console.print(f"  {i}. {description}")
            
        # Get user choice
        if self.auto_mode:
            choice = 1  # Automatic installation
        else:
            while True:
                try:
                    choice = int(Prompt.ask(f"\\nChoose installation method", 
                                          choices=[str(i) for i in range(1, len(options) + 1)]))
                    break
                except ValueError:
                    self.console.error("Please enter a valid number")
                    
        # Execute chosen installation method
        selected_key, _ = options[choice - 1]
        return self._execute_installation(selected_key)
    
    def _execute_installation(self, method: str) -> bool:
        """Execute the chosen ADB installation method."""
        try:
            if method == "auto":
                self.install_automatic()
            elif method == "brew":
                self.install_homebrew()
            elif method == "apt":
                self.install_apt()
            elif method == "dnf":
                self.install_dnf()
            elif method == "pacman":
                self.install_pacman()
            elif method == "manual":
                self.show_manual_instructions()
                return False
            elif method == "skip":
                self.console.warning("Skipping ADB installation - some features will be unavailable")
                return False
                
            # Verify installation
            return self.verify_installation()
            
        except Exception as e:
            self.console.error(f"Installation failed: {e}")
            if not self.auto_mode:
                if Confirm.ask("Try a different installation method?"):
                    return self._show_installation_options()
            return False
    
    def install_automatic(self) -> None:
        """Install ADB by direct download from Android SDK."""
        self.console.info("Downloading ADB from official Android SDK...")
        
        # Determine download URL based on platform
        system_info = self.config.system
        base_url = "https://dl.google.com/android/repository"
        
        os_name = system_info.get('os_name', platform.system()).lower()
        
        if os_name == "darwin":
            filename = "platform-tools_r36.0.0-darwin.zip"
        elif os_name == "linux":
            filename = "platform-tools_r36.0.0-linux.zip"
        elif os_name == "windows":
            filename = "platform-tools_r36.0.0-windows.zip"
        else:
            raise ValueError(f"Unsupported platform: {os_name}")
            
        download_url = f"{base_url}/{filename}"
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / filename
            
            # Download with progress bar
            self._download_file(download_url, zip_path)
            
            # Extract
            self.console.info("Extracting platform tools...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
                
            # Install to system location
            platform_tools_dir = temp_path / "platform-tools"
            self._install_to_system(platform_tools_dir)
    
    def _download_file(self, url: str, destination: Path) -> None:
        """Download file with progress bar."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            console=self.console.console,
        ) as progress:
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            task = progress.add_task("Downloading...", total=total_size)
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
    
    def _install_to_system(self, platform_tools_dir: Path) -> None:
        """Install ADB binary to system location."""
        adb_binary = platform_tools_dir / ("adb.exe" if platform.system() == "Windows" else "adb")
        
        if not adb_binary.exists():
            raise FileNotFoundError("ADB binary not found in downloaded package")
            
        # Determine installation directory
        if platform.system() == "Darwin":  # macOS
            install_dir = Path("/usr/local/bin")
        elif platform.system() == "Windows":
            install_dir = Path.home() / ".local" / "bin"
            install_dir.mkdir(parents=True, exist_ok=True)
        else:  # Linux
            install_dir = Path.home() / ".local" / "bin"
            install_dir.mkdir(parents=True, exist_ok=True)
            
        target_path = install_dir / adb_binary.name
        
        try:
            # Try to copy directly
            shutil.copy2(adb_binary, target_path)
            target_path.chmod(0o755)
            
        except PermissionError:
            # Need sudo for system directories
            if install_dir == Path("/usr/local/bin"):
                self.console.info("Administrator privileges required for installation...")
                cmd = ["sudo", "cp", str(adb_binary), str(target_path)]
                subprocess.run(cmd, check=True)
                subprocess.run(["sudo", "chmod", "755", str(target_path)], check=True)
            else:
                raise
                
        self.config.adb_path = str(target_path)
        self.console.success(f"ADB installed to {target_path}")
    
    def install_homebrew(self) -> None:
        """Install ADB using Homebrew."""
        self.console.info("Installing ADB via Homebrew...")
        result = subprocess.run(["brew", "install", "android-platform-tools"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Homebrew installation failed: {result.stderr}")
        self.console.success("ADB installed via Homebrew")
    
    def install_apt(self) -> None:
        """Install ADB using APT."""
        self.console.info("Installing ADB via APT...")
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "android-tools-adb"], check=True)
        self.console.success("ADB installed via APT")
    
    def install_dnf(self) -> None:
        """Install ADB using DNF."""
        self.console.info("Installing ADB via DNF...")
        subprocess.run(["sudo", "dnf", "install", "-y", "android-tools"], check=True)
        self.console.success("ADB installed via DNF")
    
    def install_pacman(self) -> None:
        """Install ADB using Pacman."""
        self.console.info("Installing ADB via Pacman...")
        subprocess.run(["sudo", "pacman", "-S", "android-tools"], check=True)
        self.console.success("ADB installed via Pacman")
    
    def show_manual_instructions(self) -> None:
        """Show manual installation instructions."""
        system_info = self.config.system
        os_name = system_info.get('os_name', platform.system()).lower()
        
        instructions_text = f"""
📖 Manual ADB Installation Instructions

1. Download Android SDK Platform Tools from:
   https://developer.android.com/studio/releases/platform-tools

2. Extract the downloaded ZIP file to a directory of your choice

3. Add the platform-tools directory to your PATH:
"""
        
        if os_name == "darwin":
            instructions_text += """
   macOS:
   echo 'export PATH="$PATH:/path/to/platform-tools"' >> ~/.zshrc
   source ~/.zshrc
"""
        elif os_name == "linux":
            instructions_text += """
   Linux:
   echo 'export PATH="$PATH:/path/to/platform-tools"' >> ~/.bashrc
   source ~/.bashrc
"""
        elif os_name == "windows":
            instructions_text += """
   Windows:
   - Right-click 'This PC' or 'Computer' > Properties
   - Click 'Advanced system settings'
   - Click 'Environment Variables'
   - Edit the 'Path' variable and add the path to platform-tools directory
"""
            
        instructions_text += "\\n4. Restart your terminal and verify: adb version"
        
        self.console.print(Panel(instructions_text.strip(),
                               title="[bold blue]Manual Installation[/bold blue]",
                               border_style="blue"))
        
        self.console.warning("After manual installation, restart this setup wizard.")
    
    def verify_installation(self) -> bool:
        """Verify that ADB is properly installed and accessible."""
        with self.console.status("Verifying ADB installation..."):
            adb_info = self.adb_manager.detect_existing()
            
        if adb_info.installed:
            self.console.success(f"ADB installation verified: {adb_info.version}")
            self.config.adb_path = str(adb_info.path)
            return True
        else:
            raise RuntimeError("ADB installation verification failed")
