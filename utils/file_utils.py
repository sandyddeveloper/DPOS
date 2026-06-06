"""
Path helpers, extension detection.
"""
import os

# Extensions of files whose text content should be indexed
TEXT_EXTENSIONS = {
    "py", "js", "ts", "jsx", "tsx", "md", "txt", 
    "json", "sql", "yaml", "yml", "ini", "cfg", 
    "toml", "sh", "bat", "ps1", "html", "css", "xml"
}

def get_file_extension(filename: str) -> str:
    """Extract and return the lowercase file extension without leading dot."""
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()

def is_text_file(filename: str) -> bool:
    """Determine if a file is a text/code file based on its extension."""
    ext = get_file_extension(filename)
    return ext in TEXT_EXTENSIONS

def get_relative_path(absolute_path: str, base_path: str) -> str:
    """Return a relative path of a file if it falls under the base_path, else absolute."""
    try:
        rel = os.path.relpath(absolute_path, base_path)
        if not rel.startswith(".."):
            return rel
    except Exception:
        pass
    return absolute_path
