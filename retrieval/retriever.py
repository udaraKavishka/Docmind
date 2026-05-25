"""
Unified retrieval interface — dense + BM25 + RRF fusion + parent lookup (Layer 4).
"""
from __future__ import annotations

import logging
from typing import Any, Optional
import chromadb
from chromadb import Collection
from chromadb.config import Settings
from config import CHROMA_DIR, DENSE_TOP_K
from retrieval.embedder import embed_text
from retrieval.bm25_store import bm25_search
from retrieval.fusion import reciprocal_rank_fusion

log = logging.getLogger(__name__)

_client: Optional[Any] = None
_collection: Optional[Collection] = None


def _get_collection() -> Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _client.get_collection('rag_chunks')
    assert _collection is not None
    return _collection


def dense_search(
    query: str,
    top_k: int = DENSE_TOP_K,
    language: Optional[str] = None,
) -> list[tuple[str, str, float]]:
    """
    Vector similarity search in ChromaDB.

    Returns:
        list of (chunk_id, text, distance) — lower distance = more similar (cosine).
    """
    col     = _get_collection()
    q_embed = embed_text(query)
    where: dict = {'type': 'child'}
    if language and language != 'all':
        where['language'] = language

    results: Any = col.query(
        query_embeddings=[q_embed],
        n_results=top_k,
        where=where,
        include=['documents', 'distances', 'metadatas'],
    )
    return list(zip(
        results['ids'][0],
        results['documents'][0],
        results['distances'][0],
    ))


def fetch_parent(child_id: str, child_text: str) -> dict:
    """
    Fetch the parent chunk for a given child chunk ID.
    Falls back to child text if the parent is not found.
    """
    col = _get_collection()
    try:
        child_result: Any = col.get(ids=[child_id], include=['metadatas'])
        child_meta = child_result['metadatas'][0]
        parent_id  = child_meta.get('parent_id')
        if parent_id:
            parent_data: Any = col.get(
                ids=[f'parent_{parent_id}'],
                include=['documents', 'metadatas'],
            )
            if parent_data['documents']:
                return {
                    'text': parent_data['documents'][0],
                    'meta': parent_data['metadatas'][0],
                }
    except Exception as e:
        log.warning(f'Parent fetch failed for {child_id}: {e}')

    # Fallback: return child text directly
    return {'text': child_text, 'meta': {}}


def retrieve(
    query: str,
    top_n: int = 20,
    language: Optional[str] = None,
) -> list[dict]:
    """
    Full hybrid retrieval pipeline:
      dense search + BM25 search → RRF fusion → parent lookup → top_n results.

    Args:
        query:    The search query string
        top_n:    Number of results to return after fusion
        language: Optional language filter ('sin', 'tam', 'eng', or None/all)

    Returns:
        List of dicts: chunk_id, text, child_text, rrf_score, meta, source
    """
    # ── Dense retrieval ────────────────────────────────────────────
    dense_results = dense_search(query, language=language)
    dense_ids     = [r[0] for r in dense_results]
    dense_map     = {r[0]: (r[1], r[2]) for r in dense_results}

    # ── Sparse BM25 retrieval ──────────────────────────────────────
    bm25_results = bm25_search(query)
    bm25_ids     = [r[0] for r in bm25_results]
    bm25_map     = {r[0]: (r[1], r[2]) for r in bm25_results}

    # ── RRF fusion ─────────────────────────────────────────────────
    fused     = reciprocal_rank_fusion([dense_ids, bm25_ids])
    top_fused = fused[:top_n]

    # ── Build result list with parent context ──────────────────────
    results = []
    for chunk_id, rrf_score in top_fused:
        child_text = (
            dense_map.get(chunk_id, ('', 0))[0]
            or bm25_map.get(chunk_id, ('', 0))[0]
        )
        parent_data = fetch_parent(chunk_id, child_text)
        results.append({
            'chunk_id':   chunk_id,
            'text':       parent_data['text'],   # parent text for LLM context
            'child_text': child_text,             # child text for debugging
            'rrf_score':  rrf_score,
            'meta':       parent_data['meta'],
            'source':     parent_data['meta'].get('source', ''),
        })

    return results
