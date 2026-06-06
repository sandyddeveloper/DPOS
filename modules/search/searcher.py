"""
Unified searcher pipeline fanning out queries to appropriate search backends.
"""
from sqlalchemy.orm import Session
from modules.search.providers.result import SearchResult
from modules.search.providers import project_provider, file_provider, clip_provider

def search(query: str, session: Session, doc_types: list[str] = None) -> list[SearchResult]:
    """Unified searcher entry point.
    
    Fans the query out to the appropriate providers, merges results,
    and sorts them by score (descending).
    """
    if not query or not query.strip():
        return []

    query = query.strip()
    results = []

    # 1. Project Search (SQLite LIKE query)
    search_projects = not doc_types or "project" in doc_types
    if search_projects:
        try:
            results.extend(project_provider.search(query, session))
        except Exception as e:
            print(f"Error in Project Search: {e}")

    # 2. File and Code Search (SQLite + Whoosh FTS)
    search_files = not doc_types or "file" in doc_types or "code" in doc_types
    if search_files:
        try:
            results.extend(file_provider.search(query, session, doc_types))
        except Exception as e:
            print(f"Error in File/Code Search: {e}")

    # 3. Clipboard History Search (Whoosh FTS doc_type='clipboard')
    search_clipboard = not doc_types or "clipboard" in doc_types
    if search_clipboard:
        try:
            results.extend(clip_provider.search(query, session))
        except Exception as e:
            print(f"Error in Clipboard Search: {e}")

    # 4. Merged Rank Sorting (Higher score first)
    results.sort(key=lambda x: x.score, reverse=True)

    return results
