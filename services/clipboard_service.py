"""
Wraps modules/clipboard/monitor.py.
"""
from modules.clipboard.monitor import start_clipboard_monitor, stop_clipboard_monitor

class ClipboardService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def start(self):
        start_clipboard_monitor(self.session_factory)

    def stop(self):
        stop_clipboard_monitor()
