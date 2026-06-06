"""
Wraps modules/automation/scheduler.py.
"""
class SchedulerService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def start(self):
        print("Scheduler Service active.")

    def stop(self):
        print("Scheduler Service stopped.")
