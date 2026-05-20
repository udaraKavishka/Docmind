import logging
from FlagEmbedding import FlagReranker

log        = logging.getLogger(__name__)
MODEL_NAME = 'BAAI/bge-reranker-v2-m3'
_reranker  = None   # Lazy-loaded singleton


def get_reranker() -> FlagReranker:
    """Lazy-load the reranker on first call. Stays resident in RAM after."""
    global _reranker
    if _reranker is None:
        log.info(f'Loading reranker: {MODEL_NAME} (first load ~3-8 seconds)')
        # use_fp16=True halves memory usage with negligible accuracy loss
        _reranker = FlagReranker(MODEL_NAME, use_fp16=True)
    return _reranker


def rerank(
    query: str,
    candidates: list[dict],
    top_n: int = 10
) -> list[dict]:
    """
    Rerank retrieved candidates using the BGE cross-encoder.

    Args:
        query:      The user query string
        candidates: List of dicts from retrieve() — must have 'text' key
        top_n:      Number of top results to return

    Returns:
        top_n candidates sorted by cross-encoder relevance score (highest first)
        Each dict gets a 'rerank_score' key added (0.0 to 1.0)
    """
    if not candidates:
        return []

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
        reverse=True
    )
    return reranked[:top_n]