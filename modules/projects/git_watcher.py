"""
watchdog — git status, changes.
"""
import time
from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError

_git_cache_time = 0.0
_git_cached_count = 0

def get_git_changes_count(projects) -> int:
    """Sum the number of unstaged changes and untracked files across all projects.
    
    If a project path is not a valid git repository or does not exist, it is silently skipped.
    """
    global _git_cache_time, _git_cached_count
    now = time.time()
    # Cache Git count for 10 seconds to reduce CPU and disk overhead
    if now - _git_cache_time > 10.0:
        total = 0
        for project in projects:
            if not project.path:
                continue
            try:
                repo = Repo(project.path)
                total += len(repo.index.diff(None)) + len(repo.untracked_files)
            except (InvalidGitRepositoryError, NoSuchPathError):
                pass
            except Exception:
                pass
        _git_cached_count = total
        _git_cache_time = now
    return _git_cached_count
