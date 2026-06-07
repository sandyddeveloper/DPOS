"""
Project search provider.
"""
from sqlalchemy import or_
from sqlalchemy.orm import Session
from core.models import Project
from modules.search.providers.result import SearchResult

def search(query: str, session: Session) -> list[SearchResult]:
    """Search for projects in SQLite by name, path, or tags."""
    if not query.strip():
        return []

    # Simple LIKE queries for the small projects table
    projects = session.query(Project).filter(
        or_(
            Project.name.ilike(f"%{query}%"),
            Project.path.ilike(f"%{query}%"),
            Project.tags.ilike(f"%{query}%")
        )
    ).all()

    results = []
    for p in projects:
        # Prioritize title matches with a higher score
        score = 2.0 if query.lower() in p.name.lower() else 1.0
        results.append(SearchResult(
            doc_type="project",
            title=p.name,
            subtitle=p.path + (f" [{p.tags}]" if p.tags else ""),
            path=p.path,
            score=score
        ))
    return results
