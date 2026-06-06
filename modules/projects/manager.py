"""
CRUD for projects.
"""
from datetime import date
from sqlalchemy.orm import Session
from core.models import Project, Task

def get_tasks_due_today(session: Session) -> int:
    """Return count of incomplete tasks due today."""
    return session.query(Task).filter(
        Task.due_date == date.today().isoformat(),
        Task.completed == False
    ).count()

def create_project(session: Session, name: str, path: str, services: list = None) -> Project:
    """Create a new project record."""
    project = Project(name=name, path=path, services=services or [])
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

def get_projects(session: Session) -> list[Project]:
    """Retrieve all projects."""
    return session.query(Project).all()

def delete_project(session: Session, project_id: int) -> bool:
    """Delete a project by id."""
    project = session.query(Project).filter(Project.id == project_id).first()
    if project:
        session.delete(project)
        session.commit()
        return True
    return False

def create_task(session: Session, title: str, due_date: str, project_id: int = None) -> Task:
    """Create a new task."""
    task = Task(title=title, due_date=due_date, completed=False, project_id=project_id)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def get_tasks(session: Session) -> list[Task]:
    """Retrieve all tasks."""
    return session.query(Task).all()
