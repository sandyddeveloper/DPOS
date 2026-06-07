"""
DPOS FastAPI Backend API
Hosts REST endpoints for Next.js UI, controls background services, and runs setup tasks.
"""
import os
import sys
import threading
from datetime import date
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure root dir is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import init_db, SessionLocal
from core.models import Project, Task, ClipEntry
from services.service_manager import ServiceManager
from modules.monitor.collector import get_snapshot
from modules.projects.git_watcher import get_git_changes_count
from modules.projects.service_checker import has_running_service
from modules.clipboard.categories import detect_category
from modules.search import searcher
import pyperclip

# Import DPOS app core tasks
from app import (
    register_windows_daily_scan_task,
    create_desktop_shortcut,
    register_windows_uninstall_entry,
    scan_and_update_projects,
    get_last_scan_date
)

service_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global service_manager
    print("--------------------------------------------------")
    print("Starting DPOS FastAPI Backend Sidecar...")
    print("--------------------------------------------------")
    
    # 1. Initialize SQLite Database Tables
    init_db()
    
    # 2. Seed Database if empty
    session = SessionLocal()
    try:
        proj_count = session.query(Project).count()
        scan_and_update_projects(session, force=True)
        if proj_count == 0:
            first_proj = session.query(Project).first()
            if first_proj:
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
                print("Database seeded with default tasks.")
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

    # 3. Register scheduler daily task, desktop shortcut, and Add/Remove Programs registry entry
    try:
        register_windows_daily_scan_task()
    except Exception as e:
        print(f"Failed to register task scheduler: {e}")
        
    try:
        create_desktop_shortcut()
    except Exception as e:
        print(f"Failed to create desktop shortcut: {e}")
        
    try:
        register_windows_uninstall_entry()
    except Exception as e:
        print(f"Failed to register uninstall registry entry: {e}")

    # 4. Check if daily scan was missed and run it in background
    last_scan = get_last_scan_date()
    today = date.today().isoformat()
    if last_scan != today:
        print("Daily scan was missed or has not run today. Launching startup scan in background...")
        def run_scan():
            s = SessionLocal()
            try:
                scan_and_update_projects(s)
                print("Startup background scan complete.")
            except Exception as ex:
                print(f"Error during startup background scan: {ex}")
            finally:
                s.close()
        threading.Thread(target=run_scan, name="DPOS-FastAPI-Startup-Scan", daemon=True).start()

    # 5. Start background monitoring services (clipboard, watchers, etc.)
    service_manager = ServiceManager(SessionLocal)
    service_manager.start_all()
    
    yield
    
    # 6. Shutdown and cleanup background threads
    if service_manager:
        service_manager.stop_all()
    print("DPOS FastAPI Backend Sidecar shut down successfully.")


app = FastAPI(title="DPOS API Backend", lifespan=lifespan)

# Enable CORS for local file scheme and localhost requests from Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 1. SYSTEM MONITOR ENDPOINT
# ==========================================

@app.get("/api/monitor/snapshot")
def get_monitor_snapshot():
    # Load memory/cpu metrics
    try:
        snap = get_snapshot()
    except Exception as e:
        snap = {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0
        }
        
    # Read listening ports using psutil
    ports = []
    try:
        import psutil
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN':
                ports.append({
                    "port": conn.laddr.port,
                    "pid": conn.pid or 0
                })
        ports.sort(key=lambda x: x["port"])
    except Exception:
        pass
        
    # Read Docker container statuses
    containers = []
    docker_online = True
    try:
        import docker
        client = docker.from_env()
        for c in client.containers.list(all=True)[:10]:
            containers.append({
                "name": c.name,
                "status": c.status.upper()
            })
    except Exception:
        docker_online = False
        
    return {
        **snap,
        "ports": ports[:10],
        "containers": containers,
        "docker_online": docker_online
    }


# ==========================================
# 2. PROJECTS ENDPOINTS
# ==========================================

class ProjectCreate(BaseModel):
    name: str
    path: str
    tags: Optional[str] = ""
    services: Optional[list] = []

@app.get("/api/projects")
def list_projects():
    session = SessionLocal()
    try:
        projects = session.query(Project).all()
        result = []
        for p in projects:
            try:
                git_changes = get_git_changes_count([p])
            except Exception:
                git_changes = 0
            
            result.append({
                "id": p.id,
                "name": p.name,
                "path": p.path,
                "tags": [t.strip() for t in p.tags.split(",") if t.strip()] if p.tags else [],
                "services": p.services or [],
                "is_active": has_running_service(p),
                "git_changes": git_changes
            })
        return result
    finally:
        session.close()

@app.post("/api/projects")
def create_project(data: ProjectCreate):
    session = SessionLocal()
    try:
        p = Project(
            name=data.name,
            path=data.path,
            tags=data.tags,
            services=data.services
        )
        session.add(p)
        session.commit()
        session.refresh(p)
        return {"success": True, "id": p.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int):
    session = SessionLocal()
    try:
        p = session.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")
        session.delete(p)
        session.commit()
        return {"success": True}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


# ==========================================
# 3. TASKS ENDPOINTS
# ==========================================

class TaskCreate(BaseModel):
    title: str
    due_date: str
    project_id: int

class TaskUpdate(BaseModel):
    completed: Optional[bool] = None
    title: Optional[str] = None
    due_date: Optional[str] = None

@app.get("/api/tasks")
def list_tasks(project_id: Optional[int] = None):
    session = SessionLocal()
    try:
        query = session.query(Task)
        if project_id is not None:
            query = query.filter(Task.project_id == project_id)
        tasks = query.all()
        return [{
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date,
            "completed": t.completed,
            "project_id": t.project_id
        } for t in tasks]
    finally:
        session.close()

@app.post("/api/tasks")
def create_task(data: TaskCreate):
    session = SessionLocal()
    try:
        t = Task(
            title=data.title,
            due_date=data.due_date,
            completed=False,
            project_id=data.project_id
        )
        session.add(t)
        session.commit()
        session.refresh(t)
        return {
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date,
            "completed": t.completed,
            "project_id": t.project_id
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, data: TaskUpdate):
    session = SessionLocal()
    try:
        t = session.query(Task).filter(Task.id == task_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if data.completed is not None:
            t.completed = data.completed
        if data.title is not None:
            t.title = data.title
        if data.due_date is not None:
            t.due_date = data.due_date
            
        session.commit()
        return {
            "id": t.id,
            "title": t.title,
            "due_date": t.due_date,
            "completed": t.completed,
            "project_id": t.project_id
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    session = SessionLocal()
    try:
        t = session.query(Task).filter(Task.id == task_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        session.delete(t)
        session.commit()
        return {"success": True}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


# ==========================================
# 4. CLIPBOARD HISTORY ENDPOINTS
# ==========================================

class ClipCreate(BaseModel):
    content: str

class CopyRequest(BaseModel):
    text: str

@app.get("/api/clipboard")
def get_clipboard(query: Optional[str] = None, filter: Optional[str] = None):
    session = SessionLocal()
    try:
        if query:
            results = searcher.search(query, session, doc_types=["clipboard"])
            clip_ids = []
            for r in results:
                try:
                    clip_ids.append(int(r.path.replace("clip_", "")))
                except ValueError:
                    pass
            
            clips = session.query(ClipEntry).filter(ClipEntry.id.in_(clip_ids)).all()
            clips_dict = {c.id: c for c in clips}
            clips = [clips_dict[cid] for cid in clip_ids if cid in clips_dict]
        else:
            clips = session.query(ClipEntry).order_by(ClipEntry.timestamp.desc()).limit(80).all()
        
        results = []
        for c in clips:
            category = detect_category(c.content)
            if filter and filter != "ALL" and category.upper() != filter.upper():
                continue
            results.append({
                "id": c.id,
                "content": c.content,
                "timestamp": c.timestamp.isoformat(),
                "category": category
            })
        return results
    finally:
        session.close()

@app.post("/api/clipboard")
def create_clip(data: ClipCreate):
    session = SessionLocal()
    try:
        c = ClipEntry(content=data.content)
        session.add(c)
        session.commit()
        session.refresh(c)
        
        try:
            from modules.search.providers import clip_provider
            clip_provider.index_entry(c)
        except Exception as index_err:
            print(f"Indexing error: {index_err}")
            
        return {
            "id": c.id,
            "content": c.content,
            "timestamp": c.timestamp.isoformat(),
            "category": detect_category(c.content)
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@app.post("/api/clipboard/copy")
def copy_to_clipboard(data: CopyRequest):
    try:
        pyperclip.copy(data.text)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clipboard/{clip_id}")
def delete_clip(clip_id: int):
    session = SessionLocal()
    try:
        c = session.query(ClipEntry).filter(ClipEntry.id == clip_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Clip not found")
        session.delete(c)
        session.commit()
        return {"success": True}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


# ==========================================
# 5. SCAN ENDPOINT
# ==========================================

@app.post("/api/scan")
def trigger_scan():
    session = SessionLocal()
    try:
        scan_and_update_projects(session, force=True)
        return {"success": True, "message": "Manual environment project scan completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    if "--scan" in sys.argv:
        print("Running DPOS scheduled filesystem scan...")
        from core.database import init_db, SessionLocal
        from app import scan_and_update_projects
        init_db()
        session = SessionLocal()
        try:
            scan_and_update_projects(session)
            print("Background scan complete.")
        except Exception as e:
            print(f"Error during background scan: {e}")
            sys.exit(1)
        finally:
            session.close()
        sys.exit(0)

    import uvicorn
    # Use standard local port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
