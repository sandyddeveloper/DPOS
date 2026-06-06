"""
All ORM models (Project, Task, Clip, etc.).
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    tags = Column(String, default="")  # comma-separated list of tags
    services = Column(JSON, default=list)  # List of service dicts, e.g. [{"type": "port", "port": 8000}]

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    def has_running_service(self) -> bool:
        """Check if any of the project's registered services are active."""
        from modules.projects.service_checker import has_running_service
        return has_running_service(self)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    due_date = Column(String, nullable=False)  # ISO date string (YYYY-MM-DD)
    completed = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    project = relationship("Project", back_populates="tasks")

class FileEntry(Base):
    __tablename__ = "file_entries"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    extension = Column(String, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    project = relationship("Project")

class ClipEntry(Base):
    __tablename__ = "clip_entries"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
