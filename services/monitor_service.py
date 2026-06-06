"""
Wraps modules/monitor/collector.py.
"""
class MonitorService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def start(self):
        print("Monitor Service active.")

    def stop(self):
        print("Monitor Service stopped.")
