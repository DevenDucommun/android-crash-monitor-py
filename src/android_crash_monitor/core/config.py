#!/usr/bin/env python3
"""
Configuration Management System

Handles application configuration, profiles, and settings persistence
using Pydantic for validation and platformdirs for cross-platform paths.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from pydantic import BaseModel, Field, field_validator, ConfigDict
from platformdirs import user_config_dir, user_data_dir


class ConfigError(Exception):
    """Configuration-related errors."""
    pass


@dataclass
class SystemInfo:
    """System information detected during setup."""
    os: str = ""
    version: str = ""
    arch: str = ""
    python_version: str = ""
    package_managers: List[str] = None
    download_tools: List[str] = None
    has_android_sdk: bool = False
    has_java: bool = False
    java_version: Optional[str] = None
    is_admin: bool = False
    
    def __post_init__(self):
        if self.package_managers is None:
            self.package_managers = []
        if self.download_tools is None:
            self.download_tools = []


class MonitoringConfig(BaseModel):
    """Monitoring configuration settings."""
    # Setup wizard compatible fields
    target_devices: List[str] = Field(default_factory=list)
    adb_path: Optional[str] = None
    log_level: str = Field(default="DEBUG", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    output_dir: Path = Field(default_factory=lambda: Path.home() / "android_logs")
    auto_rotate_logs: bool = True
    max_log_size: int = 100 * 1024 * 1024  # 100MB in bytes
    
    # Additional monitoring settings
    auto_start: bool = True
    max_log_size_str: str = "100MB"  # For display purposes
    retention_days: int = Field(default=30, ge=1, le=365)
    buffer_size: int = Field(default=1024, ge=256, le=8192)
    refresh_interval: float = Field(default=1.0, ge=0.1, le=10.0)
    
    # Filtering options (empty list means capture all logs)
    default_filters: List[str] = Field(default_factory=list)
    excluded_packages: List[str] = Field(default_factory=list)
    
    # Export settings
    auto_export: bool = False
    export_format: str = Field(default="json", pattern="^(json|csv|html|txt)$")
    export_on_crash: bool = True
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class DeviceConfig(BaseModel):
    """Device-specific configuration."""
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    preferred_device: Optional[str] = None
    auto_connect: bool = True
    connection_timeout: int = Field(default=30, ge=5, le=300)


class Config(BaseModel):
    """Main application configuration."""
    # Setup information
    setup_complete: bool = False
    setup_version: str = "2.0.0"
    
    # System information (stored as dict since Pydantic doesn't handle dataclasses well)
    system: Dict[str, Any] = Field(default_factory=dict)
    
    # ADB configuration
    adb_path: Optional[str] = None
    adb_version: Optional[str] = None
    
    # Sub-configurations
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    device: DeviceConfig = Field(default_factory=DeviceConfig)
    
    # Profile information
    profile_name: str = "default"
    last_updated: Optional[str] = None
    
    @field_validator('adb_path')
    @classmethod
    def validate_adb_path(cls, v):
        if v and not Path(v).exists():
            raise ValueError(f"ADB path does not exist: {v}")
        return v
    
    def get_system_info(self) -> SystemInfo:
        """Get system information as SystemInfo object."""
        return SystemInfo(**self.system) if self.system else SystemInfo()
    
    def set_system_info(self, system_info: SystemInfo) -> None:
        """Set system information from SystemInfo object."""
        self.system = asdict(system_info)
    
    def save(self, config_file: Optional[Path] = None) -> None:
        """Save configuration to file."""
        config_manager = ConfigManager()
        config_manager.save_profile(self, self.profile_name, config_file)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConfigManager:
    """Manages configuration files and profiles."""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.app_name = "android-crash-monitor"
        self.config_dir = Path(user_config_dir(self.app_name))
        self.data_dir = Path(user_data_dir(self.app_name))
        
        # Create directories if they don't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Use provided config file or default
        self.config_file = config_file or (self.config_dir / "config.json")
        self.active_profile = "default"
        
    def load_profile(self, profile_name: str = "default") -> Config:
        """Load a configuration profile."""
        profile_file = self.config_dir / f"{profile_name}.json"
        
        if not profile_file.exists():
            # Return default config for new profiles
            config = Config(profile_name=profile_name)
            return config
            
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = Config(**data)
            config.profile_name = profile_name
            return config
            
        except (json.JSONDecodeError, ValueError) as e:
            raise ConfigError(f"Invalid configuration file {profile_file}: {e}")
        except FileNotFoundError:
            # Return default config if file not found
            return Config(profile_name=profile_name)
    
    def save_profile(self, config: Config, profile_name: Optional[str] = None,
                    config_file: Optional[Path] = None) -> None:
        """Save a configuration profile."""
        profile_name = profile_name or config.profile_name
        profile_file = config_file or (self.config_dir / f"{profile_name}.json")
        
        # Update metadata
        config.profile_name = profile_name
        config.last_updated = self._get_timestamp()
        
        try:
            # Ensure parent directory exists
            profile_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(config.dict(), f, indent=2, default=str)
                
        except (OSError, PermissionError) as e:
            raise ConfigError(f"Cannot save configuration to {profile_file}: {e}")
    
    def list_profiles(self) -> List[str]:
        """List all available configuration profiles."""
        profiles = []
        for config_file in self.config_dir.glob("*.json"):
            if config_file.name != "config.json":  # Skip main config
                profiles.append(config_file.stem)
        
        if not profiles:
            profiles = ["default"]
            
        return sorted(profiles)
    
    def delete_profile(self, profile_name: str) -> None:
        """Delete a configuration profile."""
        if profile_name == "default":
            raise ConfigError("Cannot delete the default profile")
            
        profile_file = self.config_dir / f"{profile_name}.json"
        if profile_file.exists():
            profile_file.unlink()
        else:
            raise ConfigError(f"Profile '{profile_name}' does not exist")
    
    def copy_profile(self, source_profile: str, target_profile: str) -> None:
        """Copy one profile to another."""
        source_config = self.load_profile(source_profile)
        source_config.profile_name = target_profile
        self.save_profile(source_config, target_profile)
    
    def get_data_dir(self) -> Path:
        """Get the application data directory."""
        return self.data_dir
    
    def get_config_dir(self) -> Path:
        """Get the application configuration directory."""
        return self.config_dir
    
    def save_profile(self, profile_name: str, config: MonitoringConfig) -> None:
        """Save a monitoring configuration profile (setup wizard compatible)."""
        profile_file = self.config_dir / f"{profile_name}.json"
        
        try:
            # Ensure parent directory exists
            profile_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict and handle Path serialization
            config_dict = config.dict()
            if 'output_dir' in config_dict and isinstance(config_dict['output_dir'], Path):
                config_dict['output_dir'] = str(config_dict['output_dir'])
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, default=str)
                
        except (OSError, PermissionError) as e:
            raise ConfigError(f"Cannot save configuration to {profile_file}: {e}")
    
    def set_active_profile(self, profile_name: str) -> None:
        """Set the active profile."""
        self.active_profile = profile_name
        # Save active profile info
        active_file = self.config_dir / "active_profile.txt"
        try:
            with open(active_file, 'w') as f:
                f.write(profile_name)
        except Exception:
            pass  # Non-critical failure
    
    def get_active_config(self) -> MonitoringConfig:
        """Get the active monitoring configuration."""
        profile_file = self.config_dir / f"{self.active_profile}.json"
        
        if not profile_file.exists():
            # Return default config if no profile exists
            return MonitoringConfig()
        
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle Path fields
            if 'output_dir' in data and isinstance(data['output_dir'], str):
                data['output_dir'] = Path(data['output_dir'])
            
            return MonitoringConfig(**data)
        except Exception as e:
            raise ConfigError(f"Failed to load active config: {e}")
    
    def get_logs_dir(self) -> Path:
        """Get the logs directory."""
        logs_dir = self.data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


class ConfigError(Exception):
    """Configuration-related errors."""
    pass


def get_default_config() -> Config:
    """Get a default configuration instance."""
    return Config()


def load_config(profile: str = "default", config_file: Optional[Path] = None) -> Config:
    """Convenience function to load configuration."""
    manager = ConfigManager(config_file)
    return manager.load_profile(profile)