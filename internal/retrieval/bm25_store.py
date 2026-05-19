import pickle
import logging
from pathlib import Path
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.config import Settings
from config import BM25_PATH, CHROMA_DIR

log = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """
    Simple whitespace tokenizer.

    Why not a language-specific tokenizer?
    Whitespace splitting works across Sinhala, Tamil, and English
    without any language-specific dependencies. For higher accuracy
    on Sinhala morphology, you could add a Sinhala stemmer later.
    """
    return text.lower().split()


def rebuild_bm25() -> tuple:
    """
    Rebuild the BM25 index from all child chunks in ChromaDB.
    Call this after every batch ingestion.
    Returns (bm25, ids, docs) tuple.
    """
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False)
    )
    col      = client.get_collection('rag_chunks')
    all_data = col.get(
        where={'type': 'child'},
        include=['documents', 'metadatas']
    )
    ids  = all_data['ids']
    docs = all_data['documents']

    if not docs:
        log.warning('No child chunks found — BM25 index is empty')
        return None, [], []

    corpus = [_tokenize(d) for d in docs]
    bm25   = BM25Okapi(corpus)

    # Persist to disk
    BM25_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BM25_PATH, 'wb') as f:
        pickle.dump({'bm25': bm25, 'ids': ids, 'docs': docs}, f)

    log.info(f'BM25 index rebuilt: {len(docs)} chunks')
    return bm25, ids, docs


def load_bm25() -> tuple:
    """Load persisted BM25 index, or rebuild if not found."""
    if BM25_PATH.exists():
        with open(BM25_PATH, 'rb') as f:
            data = pickle.load(f)
        log.info(f'BM25 index loaded: {len(data["ids"])} chunks')
        return data['bm25'], data['ids'], data['docs']

    log.info('BM25 index not found — rebuilding from ChromaDB...')
    return rebuild_bm25()


def bm25_search(query: str, top_k: int = 50) -> list[tuple]:
    """
    Search the BM25 index.
    Returns list of (chunk_id, text, score) tuples sorted by score descending.
    """
    bm25, ids, docs = load_bm25()
    if bm25 is None:
        return []

    tokenized_query = _tokenize(query)
    scores          = bm25.get_scores(tokenized_query)

    # Zip scores with IDs and docs, sort descending, take top_k
    ranked = sorted(
        zip(scores, ids, docs),
        reverse=True
    )[:top_k]

    # Filter out zero-score results (no keyword overlap at all)
    return [
        (chunk_id, doc, float(score))
        for score, chunk_id, doc in ranked
        if score > 0
    ]