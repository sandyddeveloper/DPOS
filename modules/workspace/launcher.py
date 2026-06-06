"""
subprocess orchestrator.
"""
import subprocess
from utils.process_utils import run_cmd_async

# Global dictionary tracking launched workspace processes by workspace/project name
_running_processes = {}

def launch_workspace(workspace_name: str, workspace_path: str, services: list) -> list[subprocess.Popen]:
    """Launch all command services defined in the workspace template config.
    
    Returns a list of launched Popen processes.
    """
    launched = []
    for svc in services:
        svc_type = svc.get("type", "command")
        cmd = svc.get("command")
        if svc_type == "command" and cmd:
            try:
                print(f"Launching workspace service command: '{cmd}' in {workspace_path}")
                proc = run_cmd_async(cmd, cwd=workspace_path)
                launched.append(proc)
            except Exception as e:
                print(f"Failed to launch workspace service '{cmd}': {e}")
                
    if launched:
        _running_processes[workspace_name] = launched
    return launched

def stop_workspace(workspace_name: str):
    """Terminate all running services associated with the given workspace."""
    if workspace_name in _running_processes:
        for proc in _running_processes[workspace_name]:
            try:
                proc.terminate()
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception:
                pass
        del _running_processes[workspace_name]

def get_running_workspaces() -> list[str]:
    """Return names of currently running workspaces."""
    return list(_running_processes.keys())
