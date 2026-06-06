"""
Whoosh index schema definition and helpers.
"""
import os
from whoosh.fields import Schema, ID, TEXT
from whoosh.index import create_in, open_dir, exists_in
from config import DATA_DIR

# Unified search schema for file names, code contents, and clipboard history
search_schema = Schema(
    path=ID(stored=True, unique=True),       # Unique ID: file path or "clip_<id>"
    doc_type=ID(stored=True),                # "file", "code", or "clipboard"
    name=TEXT(stored=True),                  # Filename or clipboard summary
    content=TEXT(stored=True),               # Full text of file or clip content
    project=TEXT(stored=True),               # Associated project name (if code/file)
    extension=ID(stored=True)                # File extension (e.g. "py")
)

INDEX_DIR = os.path.join(DATA_DIR, "index")

def get_search_index():
    """Get the existing Whoosh index or create a new one if it doesn't exist."""
    os.makedirs(INDEX_DIR, exist_ok=True)
    if exists_in(INDEX_DIR):
        return open_dir(INDEX_DIR)
    return create_in(INDEX_DIR, search_schema)
