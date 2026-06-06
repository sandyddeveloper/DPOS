"""
Start/stop/restart all services.
"""
from services.clipboard_service import ClipboardService
from services.file_watcher_service import FileWatcherService
from services.monitor_service import MonitorService
from services.scheduler_service import SchedulerService

class ServiceManager:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.services = {
            "clipboard": ClipboardService(session_factory),
            "file_watcher": FileWatcherService(session_factory),
            "monitor": MonitorService(session_factory),
            "scheduler": SchedulerService(session_factory)
        }

    def start_all(self):
        """Start all registered background services."""
        print("Starting all background services...")
        for name, service in self.services.items():
            try:
                service.start()
            except Exception as e:
                print(f"Failed to start service {name}: {e}")

    def stop_all(self):
        """Stop all registered background services."""
        print("Stopping all background services...")
        for name, service in self.services.items():
            try:
                service.stop()
            except Exception as e:
                print(f"Failed to stop service {name}: {e}")
