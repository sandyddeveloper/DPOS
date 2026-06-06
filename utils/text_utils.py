"""
Truncate, highlight, sanitize.
"""
import re

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncates string to a specified length, appending a suffix if truncated."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + suffix

def sanitize_highlights(highlights: str) -> str:
    """Cleans up a text highlight snippet by replacing newlines with spaces and trimming whitespace."""
    if not highlights:
        return ""
    return highlights.replace("\n", " ").strip()

def highlight_text(text: str, query: str, class_name: str = "highlight") -> str:
    """Wraps occurrences of the query inside the text with HTML tags for search styling."""
    if not query or not text:
        return text
    
    pattern = re.escape(query)
    try:
        replaced = re.sub(f"({pattern})", rf'<span class="{class_name}">\1</span>', text, flags=re.IGNORECASE)
        return replaced
    except Exception:
        return text
