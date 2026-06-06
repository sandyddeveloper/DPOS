"""
OS detection, platform-specific paths.
"""
import sys
import os

def is_windows() -> bool:
    """Return True if the current platform is Windows."""
    return sys.platform == "win32"

def is_mac() -> bool:
    """Return True if the current platform is macOS."""
    return sys.platform == "darwin"

def is_linux() -> bool:
    """Return True if the current platform is Linux."""
    return sys.platform.startswith("linux")

def get_platform_name() -> str:
    """Return the name of the operating system platform."""
    if is_windows():
        return "Windows"
    elif is_mac():
        return "macOS"
    elif is_linux():
        return "Linux"
    return sys.platform

def get_default_dpos_data_dir() -> str:
    """Return platform-specific default storage path for application data."""
    if is_windows():
        base = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    elif is_mac():
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        
    return os.path.join(base, "DPOS")
