"""
Clipboard history search provider.
"""
from sqlalchemy.orm import Session
from core.models import ClipEntry
from modules.search.providers.result import SearchResult
from modules.search.schema import get_search_index

def search(query: str, session: Session) -> list[SearchResult]:
    """Search clipboard history in Whoosh FTS index."""
    if not query.strip():
        return []

    ix = get_search_index()
    search_results = []
    
    with ix.searcher() as searcher:
        from whoosh.qparser import QueryParser
        from whoosh.query import And, Term

        parser = QueryParser("content", ix.schema)
        try:
            content_q = parser.parse(query)
        except Exception:
            return []

        type_q = Term("doc_type", "clipboard")
        q = And([content_q, type_q])

        results = searcher.search(q, limit=20)
        for r in results:
            path = r["path"]
            
            # Extract database record if available to retrieve real timestamp
            subtitle = "Clipboard Snippet"
            try:
                clip_id = int(path.replace("clip_", ""))
                clip = session.query(ClipEntry).filter(ClipEntry.id == clip_id).first()
                if clip:
                    # e.g., "Clipboard | 2026-06-06 14:15:00"
                    subtitle = f"Clipboard | {clip.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            except Exception:
                pass

            search_results.append(SearchResult(
                doc_type="clipboard",
                title=r.get("name", "Clipboard Snippet"),
                subtitle=subtitle,
                path=path,
                score=r.score,
                highlights=r.highlights("content")
            ))
            
    return search_results

def index_entry(clip: ClipEntry):
    """Write clipboard entry to the Whoosh search index."""
    try:
        ix = get_search_index()
        writer = ix.writer()
        
        # Summary description for clipboard card title
        summary = clip.content[:45].strip().replace("\n", " ")
        if len(clip.content) > 45:
            summary += "..."
        if not summary:
            summary = "Empty clipboard entry"

        writer.update_document(
            path=f"clip_{clip.id}",
            doc_type="clipboard",
            name=summary,
            content=clip.content,
            project="",
            extension=""
        )
        writer.commit()
    except Exception as e:
        print(f"Error indexing clipboard item: {e}")
