"""
Plain-text parser — handles .txt, .md, .html, .htm files (Layer 2).
"""
import logging
from pathlib import Path
from ingestion.ocr import detect_language

log = logging.getLogger(__name__)


def parse(path: Path) -> list[dict]:
    """Read a text file and return a single ParsedDoc dict."""
    try:
        text = path.read_text(encoding='utf-8', errors='replace').strip()
    except Exception as e:
        log.error(f'Failed to read {path.name}: {e}')
        return []

    if not text:
        return []

    lang = detect_language(text[:300])
    return [{
        'text':     text,
        'source':   str(path),
        'page':     0,
        'language': lang,
        'doc_type': 'text',
    }]
