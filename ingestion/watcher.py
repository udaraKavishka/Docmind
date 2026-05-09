import time
import threading
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from config import WATCHED_DIR, FILE_TYPE_MAP



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [WATCHER] - %(message)s'
)
log = logging.getLogger(__name__)

class DebounceHandler(FileSystemEventHandler):
    
    def __init__(self, ingest_fn, debounce_sec: float =2.0):
        self.ingest_fn = ingest_fn
        self.debounce_sec = debounce_sec
        self._pending= {}
        self._lock = threading.Lock()
        
    def _schedule(self, path : Path, action:str):
        
        with self._lock:
            if path in self._pending:
                self._pending[path].cancel()
            t = threading.Timer(
                self._debounce,
                self._dispatch,
                args=[path,action]
            )
            self._pending[path] = t
            t.start()
            
            
    