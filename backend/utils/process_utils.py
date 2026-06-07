"""
subprocess wrappers, port checkers.
"""
import subprocess
import socket
import sys

def run_cmd_async(cmd: str, cwd: str = None) -> subprocess.Popen:
    """Launch a command asynchronously.
    
    Uses shell=True to support commands with spaces/arguments on both POSIX and Windows.
    Under Windows, it uses STARTF_USESHOWWINDOW to hide unwanted pop-up consoles.
    """
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
    return subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        startupinfo=startupinfo,
        text=True
    )

def is_port_open(port: int) -> bool:
    """Check if a local TCP port is in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False
