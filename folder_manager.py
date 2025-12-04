"""
Folder manager module for SSDsaver.
Manages RAM disk bindings for multiple folders using log2ram-style mechanism.
"""

import os
import subprocess
from typing import List, Dict, Optional
from pathlib import Path
import configparser

class FolderManager:
    """Manages folder-to-RAM bindings"""
    
    CONFIG_DIR = "/etc/ssdsaver"
    CONFIG_FILE = "/etc/ssdsaver/folders.conf"
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self) -> Dict[str, Dict]:
        """Load folder configuration from file"""
        if os.path.exists(self.CONFIG_FILE):
            self.config.read(self.CONFIG_FILE)
        
        return self._config_to_dict()
    
    def _config_to_dict(self) -> Dict[str, Dict]:
        """Convert ConfigParser to dictionary"""
        result = {}
        for section in self.config.sections():
            result[section] = dict(self.config[section])
        return result
    
    def save_config(self, app_configs: Dict[str, Dict]) -> bool:
        """Save folder configuration to file"""
        # Clear existing config
        self.config = configparser.ConfigParser()
        
        # Add each app configuration
        for app_name, app_config in app_configs.items():
            self.config[app_name] = app_config
        
        try:
            # Ensure config directory exists
            os.makedirs(self.CONFIG_DIR, exist_ok=True)
            
            # Write config file (requires root)
            config_content = self._generate_config_content()
            
            # Use pkexec to write as root
            process = subprocess.run(
                ["pkexec", "tee", self.CONFIG_FILE],
                input=config_content.encode(),
                capture_output=True,
                timeout=30
            )
            
            return process.returncode == 0
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _generate_config_content(self) -> str:
        """Generate INI config file content"""
        from io import StringIO
        output = StringIO()
        self.config.write(output)
        return output.getvalue()
    
    def get_app_config(self, app_name: str) -> Optional[Dict]:
        """Get configuration for a specific app"""
        if app_name in self.config:
            return dict(self.config[app_name])
        return None
    
    def is_app_enabled(self, app_name: str) -> bool:
        """Check if an app is enabled"""
        config = self.get_app_config(app_name)
        if not config:
            return False
        return config.get("enabled", "false").lower() == "true"
    
    def enable_app(self, app_name: str, size: str = "200M", mode: str = "safe", 
                   paths: List[str] = None) -> bool:
        """Enable RAM caching for an application"""
        if app_name not in self.config:
            self.config[app_name] = {}
        
        self.config[app_name]["enabled"] = "true"
        self.config[app_name]["size"] = size
        self.config[app_name]["mode"] = mode
        
        if paths:
            self.config[app_name]["paths"] = ";".join(paths)
        
        return True
    
    def disable_app(self, app_name: str) -> bool:
        """Disable RAM caching for an application"""
        if app_name in self.config:
            self.config[app_name]["enabled"] = "false"
            return True
        return False
    
    def get_enabled_apps(self) -> List[str]:
        """Get list of enabled applications"""
        enabled = []
        for section in self.config.sections():
            if self.config[section].get("enabled", "false").lower() == "true":
                enabled.append(section)
        return enabled
    
    def get_total_ram_usage(self) -> int:
        """Calculate total RAM usage in MB"""
        total = 0
        for section in self.config.sections():
            if self.config[section].get("enabled", "false").lower() == "true":
                size_str = self.config[section].get("size", "0M")
                total += self._parse_size_to_mb(size_str)
        return total
    
    @staticmethod
    def _parse_size_to_mb(size_str: str) -> int:
        """Parse size string (e.g., '200M', '1G') to MB"""
        size_str = size_str.upper().strip()
        
        if size_str.endswith('G'):
            return int(size_str[:-1]) * 1024
        elif size_str.endswith('M'):
            return int(size_str[:-1])
        elif size_str.endswith('K'):
            return int(size_str[:-1]) // 1024
        else:
            # Assume bytes
            return int(size_str) // (1024 * 1024)
    
    def update_log2ram_config(self) -> bool:
        """Update log2ram configuration with all enabled folders"""
        enabled_apps = self.get_enabled_apps()
        
        # Build PATH_DISK list for log2ram
        path_disk_entries = ["/var/log"]  # Always include system logs
        
        for app_name in enabled_apps:
            app_config = self.get_app_config(app_name)
            if app_config and "paths" in app_config:
                paths = app_config["paths"].split(";")
                path_disk_entries.extend(paths)
        
        # Update log2ram.conf
        path_disk_value = ";".join(path_disk_entries)
        
        try:
            # Read current log2ram config
            log2ram_config = {}
            if os.path.exists("/etc/log2ram.conf"):
                with open("/etc/log2ram.conf", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            log2ram_config[key.strip()] = value.strip()
            
            # Update PATH_DISK
            log2ram_config["PATH_DISK"] = f'"{path_disk_value}"'
            
            # Write back
            config_lines = []
            for key, value in log2ram_config.items():
                config_lines.append(f"{key}={value}")
            
            config_content = "\n".join(config_lines) + "\n"
            
            # Use pkexec to write as root
            process = subprocess.run(
                ["pkexec", "tee", "/etc/log2ram.conf"],
                input=config_content.encode(),
                capture_output=True,
                timeout=30
            )
            
            return process.returncode == 0
        except Exception as e:
            print(f"Error updating log2ram config: {e}")
            return False
