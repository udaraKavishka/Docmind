"""
ChromaDB vector store — upsert, delete, and query chunks (Layer 3).
Uses PersistentClient (no HTTP server required).
"""
from __future__ import annotations

import logging
from typing import Any, Optional
import chromadb
from chromadb import Collection
from chromadb.config import Settings
from config import CHROMA_DIR
from retrieval.embedder import embed_batch

log = logging.getLogger(__name__)

_client: Optional[Any] = None
_collection: Optional[Collection] = None

COLLECTION_NAME = 'rag_chunks'
# Placeholder zero-vector for parent chunks (not used for retrieval)
_ZERO_DIM = 768


def get_collection() -> Collection:
    """Return (or lazily create) the ChromaDB collection."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={'hnsw:space': 'cosine'},
        )
        assert _collection is not None
        log.info(f'ChromaDB collection ready: {COLLECTION_NAME} ({_collection.count()} chunks)')
    assert _collection is not None
    return _collection


def upsert_chunks(chunks: list[dict]) -> None:
    """
    Upsert a list of chunk dicts into ChromaDB.
    Child chunks are embedded; parent chunks use a zero-vector placeholder
    (parents are retrieved by ID, not by similarity search).

    Each chunk dict must have: chunk_id, text, source, chunk_type
    Optional keys:  page, language, doc_type, parent_id
    """
    col = get_collection()

    children = [c for c in chunks if c.get('chunk_type') == 'child']
    parents  = [c for c in chunks if c.get('chunk_type') == 'parent']

    # ── Embed + upsert child chunks ────────────────────────────────
    if children:
        texts:      list[str]        = [c['text'] for c in children]
        embeddings: Any              = embed_batch(texts)
        col.upsert(
            ids        = [c['chunk_id'] for c in children],
            documents  = texts,
            embeddings = embeddings,
            metadatas  = [_meta(c) for c in children],
        )

    # ── Upsert parent chunks (zero-vector, retrieved by ID only) ───
    if parents:
        zero_vec: Any = [[0.0] * _ZERO_DIM] * len(parents)
        col.upsert(
            ids        = [f'parent_{c["chunk_id"]}' for c in parents],
            documents  = [c['text'] for c in parents],
            embeddings = zero_vec,
            metadatas  = [_meta(c) for c in parents],
        )

    log.info(f'Upserted {len(children)} child + {len(parents)} parent chunks')


def delete_by_source(source: str) -> None:
    """Remove every chunk (child + parent) that belongs to *source*."""
    col = get_collection()
    result: Any = col.get(where={'source': source}, include=[])
    ids = result.get('ids', [])
    if ids:
        col.delete(ids=ids)
        log.info(f'Deleted {len(ids)} chunks for: {source}')


def _meta(chunk: dict) -> dict:
    """Build a ChromaDB-safe metadata dict from a chunk."""
    return {
        'source':    chunk.get('source', ''),
        'page':      chunk.get('page', 0),
        'language':  chunk.get('language', ''),
        'type':      chunk.get('chunk_type', ''),
        'doc_type':  chunk.get('doc_type', ''),
        'parent_id': chunk.get('parent_id', ''),
    }
