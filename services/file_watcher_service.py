"""
Wraps modules/search/indexer.py.
"""
from modules.search.indexer import start_indexer, stop_indexer

class FileWatcherService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def start(self):
        start_indexer(self.session_factory)

    def stop(self):
        stop_indexer()
