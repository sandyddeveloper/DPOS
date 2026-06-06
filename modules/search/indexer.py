"""
watchdog — git status, changes.
Background indexer and directory watcher.
"""
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core.models import Project
from modules.search.providers.file_provider import index_file, delete_file_index

EXCLUDE_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv", 
    "dist", "build", "target", "out", ".idea", ".vscode"
}

class SearchEventHandler(FileSystemEventHandler):
    """Listens to filesystem changes and syncs them to SQLite and Whoosh index."""
    def __init__(self, session_factory, project_id: int, project_name: str):
        self.session_factory = session_factory
        self.project_id = project_id
        self.project_name = project_name

    def on_created(self, event):
        if event.is_directory:
            return
        if self._is_excluded(event.src_path):
            return
        session = self.session_factory()
        try:
            index_file(session, event.src_path, self.project_id, self.project_name)
        finally:
            session.close()

    def on_modified(self, event):
        if event.is_directory:
            return
        if self._is_excluded(event.src_path):
            return
        session = self.session_factory()
        try:
            index_file(session, event.src_path, self.project_id, self.project_name)
        finally:
            session.close()

    def on_deleted(self, event):
        if event.is_directory:
            return
        if self._is_excluded(event.src_path):
            return
        session = self.session_factory()
        try:
            delete_file_index(session, event.src_path)
        finally:
            session.close()

    def _is_excluded(self, path: str) -> bool:
        """Check if any folder in the path is in the exclude list."""
        parts = os.path.normpath(path).split(os.sep)
        return any(p in EXCLUDE_DIRS for p in parts)


def crawl_project(session_factory, project_id: int, project_name: str, project_path: str):
    """Walks the project directory and indexes all non-excluded files."""
    session = session_factory()
    try:
        for root, dirs, files in os.walk(project_path):
            # Prune excluded directories in-place to avoid walk scanning them
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                index_file(session, file_path, project_id, project_name)
    except Exception as e:
        print(f"Error crawling project folder {project_path}: {e}")
    finally:
        session.close()


_observer = None
_running = False

def start_indexer(session_factory):
    """Starts the background indexer thread and watchdog observer."""
    global _observer, _running
    if _running:
        return
    _running = True
    
    def run():
        global _observer, _running
        session = session_factory()
        try:
            projects = session.query(Project).all()
        except Exception as e:
            print(f"Search indexer failed to load projects: {e}")
            projects = []
        finally:
            session.close()

        # 1. Perform initial crawl for all projects
        for p in projects:
            if p.path and os.path.exists(p.path):
                print(f"Crawling project: {p.name} at {p.path}")
                crawl_project(session_factory, p.id, p.name, p.path)

        # 2. Start watchdog directory observer
        _observer = Observer()
        watch_count = 0
        for p in projects:
            if p.path and os.path.exists(p.path):
                handler = SearchEventHandler(session_factory, p.id, p.name)
                _observer.schedule(handler, p.path, recursive=True)
                watch_count += 1
                
        if watch_count > 0:
            _observer.start()
            print(f"Universal Search File Watcher active for {watch_count} projects.")
        
        # Keep background thread alive
        try:
            while _running:
                time.sleep(1)
        except Exception:
            pass
        finally:
            if _observer and _observer.is_alive():
                _observer.stop()
                _observer.join()

    t = threading.Thread(target=run, name="DPOS-Search-Indexer", daemon=True)
    t.start()

def stop_indexer():
    """Stops the background indexer thread and watchdog observer."""
    global _running, _observer
    _running = False
    if _observer:
        try:
            _observer.stop()
            _observer.join()
        except Exception:
            pass
        _observer = None

