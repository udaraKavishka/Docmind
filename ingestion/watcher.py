"""
Python file-system watcher using watchdog (Layer 1 — Python runtime).
Used by the Streamlit app to detect file changes in watched_docs/.
The Go binary provides an equivalent watcher for standalone use.
"""
import logging
import threading
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import WATCHED_DIR

log = logging.getLogger(__name__)


class _DebounceHandler(FileSystemEventHandler):
    """
    Watchdog event handler with per-file 2-second debounce.
    Prevents duplicate triggers from editors that write files in multiple steps.
    """

    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def _debounce(self, path: str, event_type: str) -> None:
        with self._lock:
            existing = self._timers.pop(path, None)
            if existing:
                existing.cancel()
            t = threading.Timer(2.0, self._fire, args=[path, event_type])
            self._timers[path] = t
            t.start()

    def _fire(self, path: str, event_type: str) -> None:
        with self._lock:
            self._timers.pop(path, None)
        try:
            self._callback(Path(path), event_type)
        except Exception as e:
            log.error(f'Ingestion callback error [{event_type}] {path}: {e}', exc_info=True)

    def on_created(self, event) -> None:
        if not event.is_directory:
            path = str(event.src_path)
            log.debug(f'Watcher CREATE: {path}')
            self._debounce(path, 'CREATE')

    def on_modified(self, event) -> None:
        if not event.is_directory:
            path = str(event.src_path)
            log.debug(f'Watcher MODIFY: {path}')
            self._debounce(path, 'MODIFY')

    def on_deleted(self, event) -> None:
        if not event.is_directory:
            path = str(event.src_path)
            log.info(f'Watcher DELETE: {path}')
            # Deletions are fired immediately (file is already gone)
            try:
                self._callback(Path(path), 'DELETE')
            except Exception as e:
                log.error(f'Delete callback error {path}: {e}')


def start_watcher(callback) -> None:
    """
    Start the watchdog observer on WATCHED_DIR.

    *callback* signature: callback(path: Path, event_type: str) → None
    event_type is one of 'CREATE', 'MODIFY', 'DELETE'.

    This function blocks forever (designed to run in a daemon thread).
    """
    WATCHED_DIR.mkdir(exist_ok=True)
    handler  = _DebounceHandler(callback)
    observer = Observer()
    observer.schedule(handler, str(WATCHED_DIR), recursive=True)
    observer.start()
    log.info(f'Watcher started: {WATCHED_DIR}')
    try:
        while True:
            time.sleep(1)
    except Exception:
        observer.stop()
    observer.join()
