from config import RRF_K


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = RRF_K
) -> list[tuple[str, float]]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.

    Args:
        ranked_lists: list of lists of chunk_ids, each sorted best-first
        k: damping constant (default 60, from the original RRF paper)

    Returns:
        list of (chunk_id, rrf_score) sorted by score descending
    """
    scores = {}
    for ranked_list in ranked_lists:
        for rank, chunk_id in enumerate(ranked_list, 1):
            # Each list contributes 1/(rank + k) to the chunk's total score
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rank + k)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)