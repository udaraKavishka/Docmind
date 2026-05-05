from pathlib import Path 

BASE_DIR = Path(__file__).parent
WATCHED_DIR = BASE_DIR / "watched_docs"
CHROMA_DIR = BASE_DIR / "chroma_db"
BM25_DIR = BASE_DIR / "bm25_index.pk1"
LOG_DIR = BASE_DIR / "logs"


#ollama configurations
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
PRIMARY_MODEL = "qwen3-8b"
FALLBACK_MODEL = "gemma3:4b"


#qwen thinking modes
THINK_PREFIX = "/think"
NO_THINK_PREFIX = "/no_think"


#chunking configurations
PARENT_CHUNK_SIZE = 1024
CHILD_CHUNK_SIZE = 256
CHUNK_OVERLAP = 50

#retreival configurations
DENSE_TOP_K = 50
RRF_K = 60
RERANK_TOP_N = 10


#supported file types and their corresponding processing methods
FILE_TYPE_MAP ={
    '.pdf':  'pdf',
    '.pptx': 'pptx',
    '.docx': 'docx',
    '.xlsx': 'excel',
    '.csv':  'csv',
    '.txt':  'text',
    '.md':   'text',
    '.html': 'html',
    '.png':  'image',
    '.jpg':  'image',
    '.jpeg': 'image',
    '.tiff': 'image',
    '.bmp':  'image',
}