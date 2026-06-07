"""
Poll ports, Docker containers.
"""
import psutil
import socket
import time

# Short-term cache for system metrics to prevent CPU hogging during rapid polling
_cache_time = 0.0
_cached_processes = set()
_cached_ports = set()

def _update_cache_if_needed():
    global _cache_time, _cached_processes, _cached_ports
    now = time.time()
    # Cache is valid for 1.5 seconds
    if now - _cache_time > 1.5:
        # Retrieve processes
        processes = set()
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name']:
                    processes.add(proc.info['name'].lower())
        except Exception:
            pass
        
        # Retrieve ports
        ports = set()
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr:
                    ports.add(conn.laddr.port)
        except Exception:
            pass
            
        _cached_processes = processes
        _cached_ports = ports
        _cache_time = now

def check_port_open(port: int) -> bool:
    """Check if the expected port is open using psutil, falling back to socket check."""
    _update_cache_if_needed()
    if port in _cached_ports:
        return True

    # Socket fallback (very reliable without admin privileges)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False

def check_process_running(process_name: str) -> bool:
    """Check if a process with a matching name exists."""
    _update_cache_if_needed()
    return process_name.lower() in _cached_processes

def has_running_service(project) -> bool:
    """Determine if at least one registered service in project.services is running."""
    services = getattr(project, "services", None)
    if not services:
        return False
        
    for svc in services:
        svc_type = svc.get("type")
        if svc_type == "port":
            port = svc.get("port")
            if port is not None and check_port_open(int(port)):
                return True
        elif svc_type == "process":
            proc_name = svc.get("process_name")
            if proc_name and check_process_running(proc_name):
                return True
    return False

def get_active_projects_count(projects) -> int:
    """Return count of projects that have at least one active service."""
    return len([p for p in projects if has_running_service(p)])
