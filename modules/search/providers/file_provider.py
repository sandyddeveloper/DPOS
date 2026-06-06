"""
File and Code search provider.
"""
import os
from sqlalchemy.orm import Session
from core.models import FileEntry, Project
from modules.search.providers.result import SearchResult
from modules.search.schema import get_search_index

from utils.file_utils import is_text_file

def search(query: str, session: Session, doc_types: list[str] = None) -> list[SearchResult]:
    """Search files by name in SQLite and content in Whoosh."""
    if not query.strip():
        return []

    search_results = []
    seen_paths = set()

    # Determine types to search
    do_file = "file" in doc_types if doc_types else True
    do_code = "code" in doc_types if doc_types else True

    # 1. SQLite Filename Search
    if do_file or do_code:
        db_files = session.query(FileEntry).filter(
            FileEntry.name.ilike(f"%{query}%")
        ).limit(30).all()

        for f in db_files:
            dtype = "code" if f.project_id else "file"
            if doc_types and dtype not in doc_types:
                continue

            seen_paths.add(f.path)
            search_results.append(SearchResult(
                doc_type=dtype,
                title=f.name,
                subtitle=f.path,
                path=f.path,
                score=1.5  # Base score boost for name matching
            ))

    # 2. Whoosh Content Search
    ix = get_search_index()
    with ix.searcher() as searcher:
        from whoosh.qparser import QueryParser
        from whoosh.query import And, Or, Term

        parser = QueryParser("content", ix.schema)
        try:
            content_q = parser.parse(query)
        except Exception:
            return search_results

        # Filter by doc_types in Whoosh
        type_terms = []
        if do_file:
            type_terms.append(Term("doc_type", "file"))
        if do_code:
            type_terms.append(Term("doc_type", "code"))

        if not type_terms:
            return search_results

        type_q = Or(type_terms)
        q = And([content_q, type_q])

        whoosh_results = searcher.search(q, limit=30)
        for r in whoosh_results:
            path = r["path"]
            highlights = r.highlights("content")
            score = r.score

            # Check for name match duplicate
            existing = next((x for x in search_results if x.path == path), None)
            if existing:
                existing.highlights = highlights
                # Boost score if the file matches both name and content
                existing.score = max(existing.score, score + 1.0)
            else:
                seen_paths.add(path)
                dtype = r.get("doc_type", "file")
                results_name = r.get("name", os.path.basename(path))
                search_results.append(SearchResult(
                    doc_type=dtype,
                    title=results_name,
                    subtitle=path,
                    path=path,
                    score=score,
                    highlights=highlights
                ))

    return search_results

def index_file(session: Session, file_path: str, project_id: int = None, project_name: str = None):
    """Indexes a single file's metadata in SQLite and content in Whoosh if text-readable."""
    if not os.path.exists(file_path):
        return

    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    ext = ext.lstrip(".").lower()

    # 1. Update SQLite
    file_entry = session.query(FileEntry).filter(FileEntry.path == file_path).first()
    if not file_entry:
        file_entry = FileEntry(
            path=file_path,
            name=filename,
            extension=ext,
            project_id=project_id
        )
        session.add(file_entry)
    else:
        file_entry.name = filename
        file_entry.extension = ext
        file_entry.project_id = project_id
    session.commit()

    # 2. Update Whoosh content index if text file
    if is_text_file(filename):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            ix = get_search_index()
            writer = ix.writer()
            doc_type = "code" if project_id is not None else "file"
            
            writer.update_document(
                path=file_path,
                doc_type=doc_type,
                name=filename,
                content=content,
                project=project_name or "",
                extension=ext
            )
            writer.commit()
        except Exception as e:
            print(f"Error content-indexing {file_path}: {e}")

def delete_file_index(session: Session, file_path: str):
    """Deletes a file index from both SQLite and Whoosh."""
    # Delete from SQLite
    session.query(FileEntry).filter(FileEntry.path == file_path).delete()
    session.commit()

    # Delete from Whoosh
    try:
        ix = get_search_index()
        writer = ix.writer()
        writer.delete_by_term("path", file_path)
        writer.commit()
    except Exception as e:
        print(f"Error removing Whoosh index for {file_path}: {e}")
