"""
Search result data model.
"""
from dataclasses import dataclass

@dataclass
class SearchResult:
    doc_type: str        # "file", "code", "clipboard", "project"
    title: str           # Filename, project name, or clipboard snippet
    subtitle: str        # Relative folder path, project tags, or clip date
    path: str            # Absolute file path or clipboard reference ID
    score: float = 0.0   # Matches ranking score
    highlights: str = "" # Highlighted text snippet from file contents
