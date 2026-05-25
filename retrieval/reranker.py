"""
Cross-encoder reranker using BGE-reranker-v2-m3 (Layer 5).
Lazy-loaded on first use; stays resident in RAM for subsequent queries.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

# Prevent transformers from importing TF/Keras code — we only need PyTorch.
# Must be set before FlagEmbedding (and therefore transformers) is imported.
os.environ.setdefault('USE_TF', '0')
os.environ.setdefault('USE_JAX', '0')

log        = logging.getLogger(__name__)
MODEL_NAME = 'BAAI/bge-reranker-v2-m3'
_reranker: Optional[Any] = None   # FlagReranker | None — lazy-loaded singleton


def get_reranker() -> Any:
    """Lazy-load the reranker on first call. Stays resident in RAM after."""
    global _reranker
    if _reranker is None:
        from FlagEmbedding import FlagReranker  # type: ignore[import-untyped]
        log.info(f'Loading reranker: {MODEL_NAME} (first load ~3-8 seconds)')
        # use_fp16=True halves memory usage with negligible accuracy loss
        _reranker = FlagReranker(MODEL_NAME, use_fp16=True)
    return _reranker


def rerank(
    query: str,
    candidates: list[dict],
    top_n: int = 10,
) -> list[dict]:
    """
    Rerank retrieved candidates using the BGE cross-encoder.

    Args:
        query:      The user query string
        candidates: List of dicts from retrieve() — must have 'text' key
        top_n:      Number of top results to return

    Returns:
        top_n candidates sorted by cross-encoder relevance score (highest first).
        Each dict gets a 'rerank_score' key added (0.0 to 1.0).
    """
    if not candidates:
        return []

    try:
        reranker = get_reranker()

        # Build (query, chunk_text) pairs for the cross-encoder
        pairs  = [(query, c['text']) for c in candidates]
        # normalize=True maps raw logit scores to [0, 1] range
        scores = reranker.compute_score(pairs, normalize=True)

        # Attach scores to candidate dicts
        for candidate, score in zip(candidates, scores):
            candidate['rerank_score'] = float(score)

        # Sort by rerank score descending, return top_n
        reranked = sorted(
            candidates,
            key=lambda x: x['rerank_score'],
            reverse=True,
        )

    except (ImportError, ModuleNotFoundError, AttributeError, ValueError) as e:
        # FlagEmbedding / torch not installed — degrade gracefully.
        # Fall back to RRF score ordering so the pipeline keeps working.
        log.warning(
            f'Reranker unavailable ({e}) — falling back to RRF score ordering. '
            f'Install FlagEmbedding + torch to enable cross-encoder reranking.'
        )
        for c in candidates:
            # Ensure rerank_score exists so downstream display code works
            c.setdefault('rerank_score', float(c.get('rrf_score', 0.0)))
        reranked = sorted(
            candidates,
            key=lambda x: x.get('rerank_score', 0.0),
            reverse=True,
        )

    return reranked[:top_n]
