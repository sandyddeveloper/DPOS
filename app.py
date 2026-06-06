"""
App class — wires all modules together.
"""
import os
import sys
from PyQt6.QtWidgets import QApplication
from core.database import init_db, SessionLocal
from core.models import Project, Task
from services.service_manager import ServiceManager
from ui.app_window import MainWindow

def scan_and_update_projects(session):
    """Scans Projects folder and adds any new projects not already in database."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    discovered_dirs = []
    if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
        for entry in os.scandir(parent_dir):
            if entry.is_dir() and not entry.name.startswith('.'):
                discovered_dirs.append(entry.path)
                
    if not discovered_dirs:
        discovered_dirs.append(current_dir)
        
    existing_paths = {p.path for p in session.query(Project).all()}
    
    def clean_project_name(folder_name: str) -> str:
        import re
        words = re.split(r'[-_\s]+', folder_name)
        cleaned = " ".join(word.capitalize() for word in words if word)
        return cleaned if cleaned else folder_name

    new_projects = []
    for path in discovered_dirs:
        if path in existing_paths:
            continue
            
        folder_name = os.path.basename(path)
        name = clean_project_name(folder_name)
        
        services = []
        is_python = any(
            os.path.exists(os.path.join(path, f)) 
            for f in ["manage.py", "requirements.txt", "pyproject.toml"]
        )
        is_node = os.path.exists(os.path.join(path, "package.json"))
        
        if is_python:
            services.append({"type": "process", "process_name": "python.exe"})
            services.append({"type": "port", "port": 8000})
        elif is_node:
            services.append({"type": "process", "process_name": "node.exe"})
            services.append({"type": "port", "port": 3000})
        else:
            services.append({"type": "process", "process_name": "python.exe"})
            
        proj = Project(
            name=name,
            path=path,
            services=services
        )
        new_projects.append(proj)
        
    if new_projects:
        session.add_all(new_projects)
        session.commit()
        print(f"Dynamically discovered and added {len(new_projects)} new projects!")
    else:
        print("No new projects discovered.")

def register_windows_daily_scan_task():
    """Registers a daily task in Windows Task Scheduler to run the DPOS scanner at 1:00 AM.
    
    Includes configuration to run immediately upon system boot/login if a scheduled run is missed.
    """
    import sys
    import subprocess
    import tempfile
    import os
    
    if sys.platform != "win32":
        return
        
    task_name = "DPOS_Daily_Scan"
    
    # Check if task already exists
    try:
        res = subprocess.run(
            ["schtasks", "/query", "/tn", task_name], 
            capture_output=True, 
            text=True, 
            check=False
        )
        if res.returncode == 0:
            return
    except Exception:
        pass
        
    # Determine the executable/script path
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        action_path = exe_path
        action_args = "--scan"
    else:
        python_exe = sys.executable
        main_py = os.path.abspath(sys.argv[0])
        action_path = python_exe
        action_args = f'"{main_py}" --scan'
        
    # XML template to configure Task Scheduler with missed runs behavior and wake-up trigger
    xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>DPOS daily filesystem project scanner.</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-06-06T01:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{action_path}"</Command>
      <Arguments>{action_args}</Arguments>
    </Exec>
  </Actions>
</Task>
"""
    temp_dir = tempfile.gettempdir()
    temp_xml_path = os.path.join(temp_dir, "dpos_task.xml")
    
    try:
        with open(temp_xml_path, "w", encoding="utf-16") as f:
            f.write(xml_content)
            
        subprocess.run(
            ["schtasks", "/create", "/xml", temp_xml_path, "/tn", task_name, "/f"],
            capture_output=True,
            check=True
        )
        print("DPOS Daily Scan task successfully registered in Windows Task Scheduler.")
    except Exception as e:
        print(f"Error registering Windows Task Scheduler: {e}")
    finally:
        if os.path.exists(temp_xml_path):
            try:
                os.remove(temp_xml_path)
            except Exception:
                pass

def create_desktop_shortcut():
    """Creates a Windows Desktop shortcut pointing to the compiled DPOS executable."""
    import sys
    import os
    import subprocess
    
    if sys.platform != "win32":
        return
        
    try:
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            desktop_raw, _ = winreg.QueryValueEx(key, "Desktop")
            desktop_dir = os.path.expandvars(desktop_raw)
        except Exception:
            desktop_dir = os.path.join(os.environ["USERPROFILE"], "Desktop")
            
        shortcut_path = os.path.join(desktop_dir, "DPOS.lnk").replace('\\', '/')
        
        # Resolve target executable path
        if getattr(sys, 'frozen', False):
            target_path = sys.executable.replace('\\', '/')
            working_dir = os.path.dirname(target_path).replace('\\', '/')
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            target_path = os.path.join(current_dir, "dist", "DPOS", "DPOS.exe").replace('\\', '/')
            working_dir = os.path.join(current_dir, "dist", "DPOS").replace('\\', '/')
            
        # PowerShell script to create the shortcut with the embedded icon from the .exe
        ps_script = f"""$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.IconLocation = "{target_path}"
$Shortcut.Save()
"""
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            check=True
        )
        print("Desktop shortcut 'DPOS.lnk' created successfully.")
    except Exception as e:
        print(f"Error creating desktop shortcut: {e}")

def register_windows_uninstall_entry():
    """Registers DPOS in the Windows Registry under Current User Uninstall keys.
    
    This makes the application show up in Windows Settings -> Installed Apps (Add/Remove Programs).
    """
    import sys
    import os
    import winreg
    import datetime
    
    if sys.platform != "win32":
        return
        
    try:
        # Determine the target executable and base directory
        if getattr(sys, 'frozen', False):
            target_path = sys.executable
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            target_path = os.path.join(current_dir, "dist", "DPOS", "DPOS.exe")
            
        install_dir = os.path.dirname(target_path)
        
        # Windows-native paths for registry fields (must use backslashes)
        target_path_win = os.path.normpath(target_path)
        install_dir_win = os.path.normpath(install_dir)
        
        # PowerShell-friendly paths with forward slashes for the command to avoid escaping issues
        install_dir_ps = install_dir.replace('\\', '/')
        
        # Command to remove the shortcut and unregister from registry on uninstall
        uninstall_cmd = (
            f'powershell.exe -Command "'
            f'Stop-Process -Name \\"DPOS\\" -ErrorAction SilentlyContinue; '
            f'Remove-Item -Path \\"$Home/Desktop/DPOS.lnk\\" -ErrorAction SilentlyContinue; '
            f'$regKey = Get-ItemProperty -Path \\"HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders\\"; '
            f'$desktopPath = [System.Environment]::ExpandEnvironmentVariables($regKey.Desktop).Replace(\\"\\\\\\", \\"/\\"); '
            f'Remove-Item -Path \\"$desktopPath/DPOS.lnk\\" -ErrorAction SilentlyContinue; '
            f'Remove-Item -Path \\"{install_dir_ps}\\" -Recurse -Force -ErrorAction SilentlyContinue; '
            f'Remove-Item -Path \\"HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DPOS\\" -Recurse -Force -ErrorAction SilentlyContinue'
            f'"'
        )
        
        # Open registry key for Uninstall
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DPOS"
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_SET_VALUE)
        
        # Calculate folder size for EstimatedSize (in KB)
        estimated_size = 0
        try:
            for dirpath, _, filenames in os.walk(install_dir_win):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        estimated_size += os.path.getsize(fp)
            estimated_size = estimated_size // 1024
        except Exception:
            estimated_size = 50000  # Default fallback to ~50MB if directory is not accessible yet
            
        install_date = datetime.datetime.now().strftime("%Y%m%d")
        
        # Set values to display in settings
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "DPOS - Desktop Personal OS")
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, target_path_win)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "0.1.0")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "SandyDeveloper")
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir_win)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
        winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, install_date)
        winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, estimated_size)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        
        winreg.CloseKey(key)
        print("DPOS successfully registered in Windows Settings -> Installed Apps.")
    except Exception as e:
        print(f"Error registering Windows Uninstall entry: {e}")


class App:
    def __init__(self):
        self.service_manager = None
        self.qt_app = None
        self.main_window = None

    def run(self):
        """Execute the startup sequence: init db, seed, start services, run GUI."""
        print("Booting DPOS (Desktop Personal OS)...")
        
        # 1. Initialize SQLite Database Tables
        init_db()
        
        # 2. Seed Database with default mock data if empty
        self._seed_if_empty()
        
        # Register daily task in Windows Task Scheduler
        register_windows_daily_scan_task()
        
        # Create Desktop Shortcut
        create_desktop_shortcut()
        
        # Register in Windows Settings -> Installed Apps
        register_windows_uninstall_entry()
        
        # 3. Start Background services (Clipboard monitor, file indexer watcher, etc.)
        self.service_manager = ServiceManager(SessionLocal)
        self.service_manager.start_all()
        
        # 4. Launch PyQt6 GUI Application window
        self.qt_app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.main_window.show()
        
        # Start GUI application event loop
        exit_code = self.qt_app.exec()
        
        # 5. Stop services on exit
        self.cleanup()
        return exit_code

    def _seed_if_empty(self):
        """Seeds SQLite database and scans environment for projects."""
        session = SessionLocal()
        try:
            proj_count = session.query(Project).count()
            scan_and_update_projects(session)
            
            # If database was empty, add default tasks to the first project
            if proj_count == 0:
                first_proj = session.query(Project).first()
                if first_proj:
                    from datetime import date
                    t1 = Task(
                        title="Update Dashboard UI Layout",
                        due_date=date.today().isoformat(),
                        completed=False,
                        project_id=first_proj.id
                    )
                    t2 = Task(
                        title="Review Git Watcher Pull Requests",
                        due_date=date.today().isoformat(),
                        completed=False,
                        project_id=first_proj.id
                    )
                    session.add_all([t1, t2])
                    session.commit()
                    print("Default tasks seeded successfully.")
        except Exception as e:
            session.rollback()
            print(f"Error seeding database: {e}")
        finally:
            session.close()

    def cleanup(self):
        """Clean up background monitoring threads and index observers."""
        if self.service_manager:
            self.service_manager.stop_all()
