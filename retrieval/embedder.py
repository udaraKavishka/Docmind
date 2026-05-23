"""
Embedding via Ollama — wraps nomic-embed-text (or any model in config).
"""
import logging
import requests
from config import OLLAMA_BASE_URL, EMBED_MODEL, EMBED_BATCH_SIZE

log = logging.getLogger(__name__)

EMBED_URL = f'{OLLAMA_BASE_URL}/api/embeddings'
_http = requests.Session()


def embed_text(text: str) -> list[float]:
    """
    Embed a single text string using Ollama.
    Returns a list of floats (the embedding vector).
    """
    resp = _http.post(EMBED_URL, json={
        'model':  EMBED_MODEL,
        'prompt': text,
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()['embedding']


def embed_batch(texts: list[str], batch_size: int = EMBED_BATCH_SIZE) -> list[list[float]]:
    """
    Embed a list of texts in batches to avoid OOM on 12 GB RAM.
    Returns a list of embedding vectors in the same order as inputs.
    """
    embeddings = []
    total_batches = (len(texts) - 1) // batch_size + 1 if texts else 0

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_num = i // batch_size + 1
        log.info(f'Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)')
        for text in batch:
            embeddings.append(embed_text(text))

    return embeddings
