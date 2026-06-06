"""
psutil CPU, RAM, disk, ports.
"""
import psutil

def get_snapshot() -> dict:
    """Retrieve the current CPU and RAM usage metrics.
    
    Returns a dict with:
      - cpu_percent: Float (CPU utilization percentage, measured over 0.1s)
      - ram_percent: Float (RAM utilization percentage)
      - ram_used_gb: Float (RAM used in gigabytes)
      - ram_total_gb: Float (Total RAM installed in gigabytes)
    """
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_used_gb = ram.used / (1024 ** 3)
    ram_total_gb = ram.total / (1024 ** 3)
    
    return {
        "cpu_percent": cpu_percent,
        "ram_percent": ram_percent,
        "ram_used_gb": ram_used_gb,
        "ram_total_gb": ram_total_gb
    }
