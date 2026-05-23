"""
Ingestion dispatcher — routes file events to parsers, chunks, and indexes (Layers 2-4).
"""
import logging
from pathlib import Path
from config import FILE_TYPE_MAP
from ingestion.chunker import chunk_document
from retrieval.vector_store import upsert_chunks, delete_by_source
from retrieval.bm25_store import rebuild_bm25

log = logging.getLogger(__name__)


def _load_parser(parser_key: str):
    """Lazily import and return the parse() function for *parser_key*."""
    if parser_key == 'pdf':
        from ingestion.parsers.pdf_parser import parse
    elif parser_key == 'pptx':
        from ingestion.parsers.pptx_parser import parse
    elif parser_key == 'docx':
        from ingestion.parsers.docx_parser import parse
    elif parser_key == 'image':
        from ingestion.parsers.image_parser import parse
    elif parser_key == 'csv':
        from ingestion.parsers.csv_parser import parse
    elif parser_key == 'text':
        from ingestion.parsers.text_parser import parse
    else:
        return None
    return parse  # type: ignore[return-value]


def ingest(path: Path, event_type: str) -> None:
    """
    Ingest a single file event into the RAG pipeline.

    Args:
        path:       Path to the file (may not exist for DELETE events)
        event_type: 'CREATE', 'MODIFY', or 'DELETE'
    """
    path = Path(path)

    # ── Delete ─────────────────────────────────────────────────────
    if event_type == 'DELETE':
        log.info(f'Removing index for deleted file: {path.name}')
        try:
            delete_by_source(str(path))
            rebuild_bm25()
        except Exception as e:
            log.error(f'Delete index failed {path.name}: {e}')
        return

    # ── Route to parser ────────────────────────────────────────────
    ext        = path.suffix.lower()
    parser_key = FILE_TYPE_MAP.get(ext)
    if parser_key is None:
        log.debug(f'No parser for extension: {ext!r} — skipping {path.name}')
        return

    parser = _load_parser(parser_key)
    if parser is None:
        log.warning(f'Unknown parser key: {parser_key}')
        return

    log.info(f'[{event_type}] Ingesting: {path.name}')
    try:
        docs = parser(path)
        if not docs:
            log.warning(f'No content extracted from {path.name}')
            return

        all_chunks = []
        for doc in docs:
            all_chunks.extend(chunk_document(doc))

        if not all_chunks:
            log.warning(f'No chunks produced for {path.name}')
            return

        upsert_chunks(all_chunks)
        rebuild_bm25()

        child_count = sum(1 for c in all_chunks if c['chunk_type'] == 'child')
        log.info(f'Indexed {path.name}: {child_count} child chunks '
                 f'({len(docs)} page(s))')

    except Exception as e:
        log.error(f'Ingestion failed for {path.name}: {e}', exc_info=True)
