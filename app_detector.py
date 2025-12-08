"""
Application detector module for SSDsaver.
Detects installed browsers and applications that can benefit from RAM caching.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class AppInfo:
    """Information about a detected application"""
    name: str
    display_name: str
    executable: str
    cache_paths: List[str]
    default_size: str
    is_installed: bool
    icon_name: str = "application-x-executable"

class AppDetector:
    """Detects installed applications and their cache locations"""
    
    # Application definitions
    APPS = {
        "chrome": {
            "display_name": "Google Chrome",
            "executables": ["google-chrome", "google-chrome-stable", "chrome"],
            "cache_paths": ["~/.cache/google-chrome/Default/Cache"],
            "default_size": "200M",
            "icon": "google-chrome"
        },
        "chromium": {
            "display_name": "Chromium",
            "executables": ["chromium", "chromium-browser"],
            "cache_paths": ["~/.cache/chromium/Default/Cache"],
            "default_size": "200M",
            "icon": "chromium-browser"
        },
        "firefox": {
            "display_name": "Mozilla Firefox",
            "executables": ["firefox"],
            # Broader pattern to catch .default, .default-release, .default-esr, etc.
            "cache_paths": ["~/.cache/mozilla/firefox/*.default*/cache2"],
            "default_size": "150M",
            "icon": "firefox"
        },
        "brave": {
            "display_name": "Brave Browser",
            "executables": ["brave", "brave-browser"],
            # Check both .config (older/some distros) and .cache (newer/standard)
            "cache_paths": [
                "~/.config/BraveSoftware/Brave-Browser/Default/Cache",
                "~/.cache/BraveSoftware/Brave-Browser/Default/Cache"
            ],
            "default_size": "200M",
            "icon": "brave-browser"
        },
        "edge": {
            "display_name": "Microsoft Edge",
            "executables": ["microsoft-edge", "microsoft-edge-stable"],
            "cache_paths": ["~/.config/microsoft-edge/Default/Cache"],
            "default_size": "200M",
            "icon": "microsoft-edge"
        },
        "opera": {
            "display_name": "Opera",
            "executables": ["opera"],
            "cache_paths": ["~/.cache/opera/Cache"],
            "default_size": "150M",
            "icon": "opera"
        },
        "vivaldi": {
            "display_name": "Vivaldi",
            "executables": ["vivaldi"],
            "cache_paths": ["~/.cache/vivaldi/Default/Cache"],
            "default_size": "150M",
            "icon": "vivaldi"
        },
        "discord": {
            "display_name": "Discord",
            "executables": ["discord"],
            "cache_paths": ["~/.config/discord/Cache", "~/.config/discord/Code Cache"],
            "default_size": "100M",
            "icon": "discord"
        },
        "slack": {
            "display_name": "Slack",
            "executables": ["slack"],
            "cache_paths": ["~/.config/Slack/Cache", "~/.config/Slack/Code Cache"],
            "default_size": "100M",
            "icon": "slack"
        },
        "steam": {
            "display_name": "Steam",
            "executables": ["steam"],
            "cache_paths": ["~/.local/share/Steam/appcache"],
            "default_size": "300M",
            "icon": "steam"
        },
        "apt": {
            "display_name": "APT Package Cache",
            "executables": ["apt", "apt-get"],
            "cache_paths": ["/var/cache/apt/archives"],
            "default_size": "500M",
            "icon": "system-software-install"
        },
        "thumbnails": {
            "display_name": "Thumbnail Cache",
            "executables": ["true"],  # Always available
            "cache_paths": ["~/.cache/thumbnails"],
            "default_size": "100M",
            "icon": "image-x-generic"
        }
    }
    
    @staticmethod
    def is_executable_available(executable: str) -> bool:
        """Check if an executable is available in PATH"""
        try:
            result = subprocess.run(
                ["which", executable],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def expand_cache_path(path: str) -> List[str]:
        """Expand a cache path pattern to actual paths"""
        expanded_path = os.path.expanduser(path)
        
        # Handle wildcards
        if '*' in expanded_path:
            from glob import glob
            return glob(expanded_path)
        
        return [expanded_path] if os.path.exists(expanded_path) else []
    
    @classmethod
    def detect_app(cls, app_id: str, app_def: Dict) -> Optional[AppInfo]:
        """Detect if a specific application is installed"""
        # Check if any of the executables are available
        is_installed = any(
            cls.is_executable_available(exe) 
            for exe in app_def["executables"]
        )
        
        if not is_installed:
            return None
        
        # Find the first available executable
        executable = next(
            (exe for exe in app_def["executables"] 
             if cls.is_executable_available(exe)),
            app_def["executables"][0]
        )
        
        return AppInfo(
            name=app_id,
            display_name=app_def["display_name"],
            executable=executable,
            cache_paths=app_def["cache_paths"],
            default_size=app_def["default_size"],
            is_installed=is_installed,
            icon_name=app_def.get("icon", "application-x-executable")
        )
    
    @classmethod
    def detect_all_apps(cls) -> List[AppInfo]:
        """Detect all installed applications"""
        detected = []
        
        for app_id, app_def in cls.APPS.items():
            app_info = cls.detect_app(app_id, app_def)
            if app_info:
                detected.append(app_info)
        
        return detected
    
    @classmethod
    def get_app_info(cls, app_id: str) -> Optional[AppInfo]:
        """Get information about a specific application"""
        if app_id not in cls.APPS:
            return None
        
        return cls.detect_app(app_id, cls.APPS[app_id])
