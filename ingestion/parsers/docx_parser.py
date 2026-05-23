"""
Word document parser — extracts paragraphs and tables from .docx files (Layer 2).
"""
import logging
from pathlib import Path
from ingestion.ocr import detect_language

log = logging.getLogger(__name__)

_MIN_CHARS = 10   # ignore documents with fewer characters than this


def parse(path: Path) -> list[dict]:
    """
    Parse a .docx file.
    Returns a single ParsedDoc dict containing all paragraphs and tables.
    """
    try:
        from docx import Document

        doc   = Document(str(path))
        parts: list[str] = []

        # All paragraphs (headings, body, lists)
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)

        # Tables as pipe-separated rows
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(' | '.join(cells))

        text = '\n'.join(parts).strip()
        if len(text) < _MIN_CHARS:
            return []

        lang = detect_language(text[:500])
        return [{
            'text':     text,
            'source':   str(path),
            'page':     0,
            'language': lang,
            'doc_type': 'docx',
        }]

    except Exception as e:
        log.error(f'DOCX parse error for {path.name}: {e}', exc_info=True)
        return []
