"""
Central configuration for DocMind — all paths and constants live here.
Never hardcode paths or model names anywhere else.
"""
from pathlib import Path

import os

BASE_DIR = Path(__file__).parent

# ── Service endpoints ───────────────────────────────────────────────────────
OCR_SERVICE_URL = os.getenv('DOCMIND_OCR_URL',    'http://localhost:8765')
OLLAMA_BASE_URL = os.getenv('DOCMIND_OLLAMA_URL', 'http://localhost:11434')

# ── Models ──────────────────────────────────────────────────────────────────
EMBED_MODEL  = os.getenv('DOCMIND_EMBED_MODEL',   'nomic-embed-text')
PRIMARY_LLM  = os.getenv('DOCMIND_PRIMARY_LLM',   'qwen3:8b')
FALLBACK_LLM = os.getenv('DOCMIND_FALLBACK_LLM',  'gemma3:4b')

# qwen3 thinking-mode prefixes
THINK_PREFIX    = '/think '
NO_THINK_PREFIX = '/no_think '

# ── Filesystem paths ────────────────────────────────────────────────────────
# DOCMIND_WATCHED_DIR env var overrides the default so you can point DocMind
# at any folder without changing code.  Example:
#   DOCMIND_WATCHED_DIR=/home/user/my_docs streamlit run app/main.py
WATCHED_DIR = Path(os.getenv('DOCMIND_WATCHED_DIR', str(BASE_DIR / 'watched_docs')))
CHROMA_DIR  = Path(os.getenv('DOCMIND_CHROMA_DIR',  str(BASE_DIR / 'chroma_db')))
BM25_PATH   = Path(os.getenv('DOCMIND_BM25_PATH',   str(BASE_DIR / 'bm25_index.pkl')))
LOG_DIR     = BASE_DIR / 'logs'


def set_watched_dir(new_path: str | Path) -> Path:
    """
    Change the watched directory at runtime and ensure it exists.
    Call this from the Streamlit sidebar or CLI to point DocMind at a new folder.
    Returns the resolved Path.
    """
    global WATCHED_DIR
    WATCHED_DIR = Path(new_path).expanduser().resolve()
    WATCHED_DIR.mkdir(parents=True, exist_ok=True)
    return WATCHED_DIR

# ── Chunking ─────────────────────────────────────────────────────────────────
PARENT_CHUNK_SIZE = 1024   # tokens per parent chunk
CHILD_CHUNK_SIZE  = 256    # tokens per child chunk
CHUNK_OVERLAP     = 50     # token overlap between adjacent chunks
EMBED_BATCH_SIZE  = 32     # texts per Ollama embedding call

# ── Retrieval ────────────────────────────────────────────────────────────────
DENSE_TOP_K  = 50    # dense candidates before RRF
RRF_K        = 60    # RRF damping constant (from original paper)
RERANK_TOP_N = 10    # reranker output size

# ── OCR quality thresholds ────────────────────────────────────────────────────
OCR_MIN_DPI      = 300   # retry with aggressive pipeline below this DPI
OCR_MIN_TEXT_LEN = 20    # retry if extracted text is shorter than this

# ── File-type map (extension → parser key) ──────────────────────────────────
FILE_TYPE_MAP = {
    '.pdf':  'pdf',
    '.pptx': 'pptx',
    '.ppt':  'pptx',
    '.docx': 'docx',
    '.doc':  'docx',
    '.png':  'image',
    '.jpg':  'image',
    '.jpeg': 'image',
    '.tiff': 'image',
    '.bmp':  'image',
    '.csv':  'csv',
    '.xlsx': 'csv',
    '.txt':  'text',
    '.md':   'text',
    '.html': 'text',
    '.htm':  'text',
}

# ── Auto-create required directories ────────────────────────────────────────
WATCHED_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
