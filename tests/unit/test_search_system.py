import pytest
from unittest.mock import patch, MagicMock
from whoosh.filedb.filestore import RamStorage
from sqlalchemy.orm import Session

from modules.search.providers.result import SearchResult
from modules.search.schema import search_schema
from modules.search.providers import project_provider, file_provider, clip_provider
from modules.search import searcher
from core.models import Project, FileEntry, ClipEntry

# 1. Result dataclass tests
def test_search_result_instantiation():
    res = SearchResult(
        doc_type="file",
        title="test.py",
        subtitle="/path/to/test.py",
        path="/path/to/test.py",
        score=2.5,
        highlights="<b>test</b>"
    )
    assert res.doc_type == "file"
    assert res.title == "test.py"
    assert res.subtitle == "/path/to/test.py"
    assert res.path == "/path/to/test.py"
    assert res.score == 2.5
    assert res.highlights == "<b>test</b>"


# 2. Project Provider tests
def test_project_provider_search():
    mock_session = MagicMock(spec=Session)
    
    # Mock some Project database objects
    p1 = Project(id=1, name="Alpha Portal", path="/projects/alpha", tags="web, python")
    p2 = Project(id=2, name="Beta Vault", path="/projects/beta", tags="database")
    
    # Mock session query results
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.all.return_value = [p1, p2]
    
    res = project_provider.search("Alpha", mock_session)
    assert len(res) == 2
    assert res[0].title == "Alpha Portal"
    assert res[0].doc_type == "project"
    assert "web" in res[0].subtitle
    assert res[0].score == 2.0  # title match boost
    assert res[1].score == 1.0


# 3. File Provider content indexing & search tests
@patch('modules.search.providers.file_provider.get_search_index')
def test_file_provider_whoosh_search(mock_get_index):
    # Set up in-memory RamStorage index for testing Whoosh queries
    storage = RamStorage()
    ix = storage.create_index(search_schema)
    mock_get_index.return_value = ix

    # Add a mock file to the in-memory index
    writer = ix.writer()
    writer.add_document(
        path="/projects/alpha/main.py",
        doc_type="code",
        name="main.py",
        content="def hello_world():\n    print('Welcome to DPOS')",
        project="Alpha Portal",
        extension="py"
    )
    writer.commit()

    mock_session = MagicMock(spec=Session)
    # Mock SQLite query to return no name matches to test content only
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.limit.return_value.all.return_value = []

    res = file_provider.search("hello_world", mock_session)
    assert len(res) == 1
    assert res[0].title == "main.py"
    assert res[0].doc_type == "code"
    assert "hello_world" in res[0].highlights


# 4. Clipboard Provider tests
@patch('modules.search.providers.clip_provider.get_search_index')
def test_clip_provider_indexing_and_search(mock_get_index):
    storage = RamStorage()
    ix = storage.create_index(search_schema)
    mock_get_index.return_value = ix

    # Index a mock clip
    clip = ClipEntry(id=42, content="SELECT * FROM users WHERE active = 1")
    clip_provider.index_entry(clip)

    mock_session = MagicMock(spec=Session)
    # Mock database retrieval
    import datetime
    clip.timestamp = datetime.datetime(2026, 6, 6, 14, 15, 0)
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = clip

    res = clip_provider.search("users", mock_session)
    assert len(res) == 1
    assert res[0].doc_type == "clipboard"
    assert "clip_42" in res[0].path
    assert "users" in res[0].highlights
    assert "2026-06-06" in res[0].subtitle


# 5. Searcher Fanning and Ranking tests
@patch('modules.search.providers.project_provider.search')
@patch('modules.search.providers.file_provider.search')
@patch('modules.search.providers.clip_provider.search')
def test_searcher_fanning_and_sorting(mock_clip_search, mock_file_search, mock_proj_search):
    mock_session = MagicMock(spec=Session)

    # Return matches with different scores
    r_proj = SearchResult(doc_type="project", title="Proj", subtitle="sub", path="/proj", score=1.0)
    r_file = SearchResult(doc_type="file", title="File", subtitle="sub", path="/file", score=3.0)
    r_clip = SearchResult(doc_type="clipboard", title="Clip", subtitle="sub", path="clip_1", score=2.0)

    mock_proj_search.return_value = [r_proj]
    mock_file_search.return_value = [r_file]
    mock_clip_search.return_value = [r_clip]

    # Search all
    res = searcher.search("test", mock_session)
    assert len(res) == 3
    # Sorted by score descending (3.0 -> 2.0 -> 1.0)
    assert res[0].doc_type == "file"
    assert res[1].doc_type == "clipboard"
    assert res[2].doc_type == "project"

    # Filtered search (only files)
    res_filtered = searcher.search("test", mock_session, doc_types=["file"])
    assert len(res_filtered) == 1
    assert res_filtered[0].doc_type == "file"
