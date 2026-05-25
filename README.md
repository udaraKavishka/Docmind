<div align="center">

# 🧠 DocMind

### A fully local, privacy-first, agentic RAG system

**Go · Python · Ollama · LangGraph · ChromaDB · Streamlit**

![Go](https://img.shields.io/badge/Go-1.23-00ADD8?style=flat&logo=go&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=flat)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-4A90D9?style=flat)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6B35?style=flat)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Languages](https://img.shields.io/badge/Languages-Sinhala%20·%20Tamil%20·%20English-green?style=flat)

*Query your documents in Sinhala, Tamil, and English — with zero data leaving your machine.*

</div>

---

## What is DocMind?

DocMind is a **fully local, agentic Retrieval-Augmented Generation (RAG) system**. Drop any document into a watched folder and immediately ask questions about it in natural language — across Sinhala, Tamil, and English. No API keys, no cloud calls, no data leaving your machine.

### Core Features

| Property | Description |
|---|---|
| 🔒 100% local | No API keys, works offline, zero cloud dependencies |
| 🔍 Advanced RAG | Hybrid search (dense + BM25), cross-encoder reranking, parent-child chunking, RRF fusion |
| 🤖 Agentic pipeline | LangGraph: query planning → hybrid retrieval → generation → self-critique loop |
| 🌐 Multilingual OCR | Sinhala, Tamil, and English across all document types |
| 📄 Universal documents | PDF, PPTX, DOCX, images, CSV/Excel, TXT, Markdown, HTML |
| 🎓 Layered architecture | Each of 6 layers is independent and observable |

---

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| LLM inference | Ollama | Local model serving |
| Primary LLM | `qwen3:8b` | Generation with chain-of-thought (`/think` mode) |
| Fallback LLM | `gemma3:4b` | Fast planner/critic JSON output (`/no_think` mode) |
| Embeddings | `nomic-embed-text` | 100+ language MoE embeddings (274 MB) |
| Vector DB | ChromaDB ≥ 0.5 | Local persistent store, cosine similarity |
| Sparse search | rank-bm25 | Language-agnostic BM25, whitespace tokenised |
| Reranker | BGE-reranker-v2-m3 | Multilingual cross-encoder (FlagEmbedding) |
| OCR engine | Tesseract 5 | `sin + tam + eng` language packs |
| Image preprocessing | OpenCV + Pillow | Grayscale → Otsu → denoise |
| Agent framework | LangGraph ≥ 0.2 | Stateful graph with conditional edges |
| File watching (Go) | fsnotify | Debounced folder watcher (Go binary) |
| File watching (Py) | watchdog | Python watcher thread (Streamlit app) |
| Frontend | Streamlit ≥ 1.35 | Chat UI with citation display |
| PDF parsing | pdfplumber | Text + table extraction, OCR fallback |
| PPTX | python-pptx | Slides + speaker notes |
| DOCX | python-docx | Paragraphs + tables |
| Tokeniser | tiktoken `cl100k_base` | Consistent token counting |
| Language detection | langdetect | OCR language routing |

---

## Project Structure

```
docmind/
├── app/
│   └── main.py                     # Streamlit entry point (L6)
│
├── agents/                         # LangGraph agent (L5)
│   ├── __init__.py
│   ├── state.py                    # AgentState TypedDict
│   ├── nodes.py                    # planner / retriever / generator / critic
│   └── graph.py                    # LangGraph assembly + run_agent()
│
├── retrieval/                      # Hybrid retrieval pipeline (L4-L5)
│   ├── __init__.py
│   ├── embedder.py                 # Ollama nomic-embed-text wrapper
│   ├── vector_store.py             # ChromaDB CRUD
│   ├── bm25_store.py               # BM25 index build/load/search
│   ├── fusion.py                   # Reciprocal Rank Fusion
│   ├── retriever.py                # Unified retrieve() interface
│   └── reranker.py                 # BGE cross-encoder reranker
│
├── ingestion/                      # Parsing + chunking pipeline (L1-L3)
│   ├── __init__.py
│   ├── watcher.py                  # watchdog-based file watcher
│   ├── dispatcher.py               # Routes files to parsers + indexes
│   ├── chunker.py                  # Parent-child chunker (tiktoken)
│   ├── ocr.py                      # OCR microservice HTTP client
│   └── parsers/
│       ├── __init__.py
│       ├── text_parser.py          # TXT / MD / HTML
│       ├── pdf_parser.py           # PDF digital + scanned
│       ├── pptx_parser.py          # PowerPoint slides + notes
│       ├── docx_parser.py          # Word paragraphs + tables
│       ├── image_parser.py         # PNG / JPEG / TIFF / BMP
│       └── csv_parser.py           # CSV / Excel → markdown table
│
├── ocr_service/                    # FastAPI OCR microservice at :8765 (L2)
│   ├── main.py
│   └── requirements.txt
│
├── cmd/docmind/main.go             # Go binary entry point
├── internal/                       # Go packages (L1 watcher + supporting)
│   ├── config/config.go
│   ├── watcher/watcher.go
│   ├── ingestion/dispatcher.go
│   ├── ingestion/parsers/          # Go parser implementations
│   ├── chunker/                    # Go chunker
│   ├── embedder/                   # Go Ollama embedder
│   ├── ocr/client.go               # Go OCR HTTP client
│   └── vectorstore/chroma.go       # Go ChromaDB HTTP client
│
├── config.py                       # Central Python configuration
├── requirements.txt                # Python dependencies
├── go.mod / go.sum                 # Go module
├── docmind.yaml                    # tmuxp session file
├── docs/                           # Layer-by-layer implementation guides
│   ├── L1_Document_Watcher.md
│   ├── L2_OCR_Parser.md
│   ├── L3_Chunker_Embedder.md
│   ├── L4_Hybrid_Retrieval.md
│   ├── L5_Reranker_Agent.md
│   └── L6_Streamlit_Frontend.md
├── watched_docs/                   # Drop documents here (auto-created)
├── chroma_db/                      # Vector database (auto-created)
├── bm25_index.pkl                  # BM25 index (auto-generated)
└── logs/                           # Log files (auto-created)
```

---

## Quick Start

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11 – 3.13 | [python.org](https://python.org) |
| Go | ≥ 1.23 | [go.dev](https://go.dev) |
| Ollama | latest | [ollama.ai](https://ollama.ai) |
| Tesseract | 5.x | see below |
| poppler-utils | any | `sudo apt install poppler-utils` |

**Minimum RAM:** 12 GB (16 GB recommended)

---

### 1. Clone the repository

```bash
git clone <your-repo-url> docmind
cd docmind
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Python 3.13 note:** If you see a Pillow build error, run:
> `pip install --upgrade pip` then retry.

### 3. Install Tesseract with multilingual language packs

```bash
# Ubuntu / Debian
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-sin \
    tesseract-ocr-tam \
    tesseract-ocr-eng \
    poppler-utils

# macOS (Homebrew)
brew install tesseract tesseract-lang poppler

# Verify
tesseract --list-langs   # must include: sin, tam, eng
```

### 4. Pull Ollama models (~10 GB total)

```bash
ollama pull qwen3:8b          # Primary LLM   — ~5.5 GB
ollama pull gemma3:4b         # Fallback LLM  — ~3.0 GB
ollama pull nomic-embed-text  # Embeddings    — ~274 MB

ollama list   # verify
```

### 5. Pre-cache the reranker (one-time, ~1.1 GB download)

```bash
python -c "
from FlagEmbedding import FlagReranker
FlagReranker('BAAI/bge-reranker-v2-m3')
print('Reranker cached successfully')
"
```

### 6. Build the Go binary (optional — for standalone file watcher)

```bash
go build ./cmd/docmind/
# or run directly:
go run ./cmd/docmind/
```

---

## Running DocMind

### Option A — tmuxp (recommended, all services in one command)

```bash
pip install tmuxp    # one-time
tmuxp load docmind.yaml
```

This opens 5 tmux windows:

| Window | Service | Port |
|---|---|---|
| `ocr-service` | FastAPI OCR microservice | 8765 |
| `go-watcher` | Go file watcher (optional) | — |
| `streamlit` | Streamlit chat UI | 8501 |
| `ollama` | Ollama LLM server | 11434 |
| `shell` | Free shell | — |

### Option B — Manual (4 terminals)

```bash
# Terminal 1 — Ollama
OLLAMA_KEEP_ALIVE=-1 ollama serve

# Terminal 2 — OCR microservice
uvicorn ocr_service.main:app --port 8765 --reload

# Terminal 3 — Streamlit app (includes Python file watcher)
streamlit run app/main.py

# Terminal 4 (optional) — Go file watcher
go run ./cmd/docmind/
```

**Open [http://localhost:8501](http://localhost:8501) in your browser.**

---

## Using DocMind

1. **Drop any file** into `watched_docs/` — it is indexed automatically (within ~5 seconds)
2. **Ask questions** in natural language in the chat box
3. Use the **Language Filter** sidebar to restrict retrieval to a specific script
4. Switch between **qwen3:8b** (better quality) and **gemma3:4b** (faster) in the sidebar
5. Enable **Debug mode** to see chunk scores, RRF scores, and raw text

### Re-indexing

Click **♻️ Re-index all** in the sidebar to re-embed every file in `watched_docs/`.

---

## Architecture

### Ingestion pipeline (triggered on file drop)

```
watched_docs/ ← drop file here
      │
      ▼  watchdog / fsnotify
 dispatcher.py
      │  routes by file extension
      ▼
 parser (pdf / pptx / docx / image / csv / text)
      │  → list of ParsedDoc dicts
      ▼
 chunker.py  (parent 1024 tok + child 256 tok, 50 tok overlap)
      │
      ▼
 retrieval/vector_store.py  → ChromaDB (child chunks embedded)
      │
      ▼
 retrieval/bm25_store.py  → bm25_index.pkl
```

### Query pipeline (triggered on user question)

```
User query
      │
      ▼  LangGraph: planner_node (gemma3:4b /no_think)
 sub-questions: ["Q1", "Q2", ...]
      │
      ▼  retriever_node
 dense_search (ChromaDB) ──┐
 bm25_search               ──┴→ RRF fusion → top-20
      │
      ▼  BGE reranker → top-10 chunks
      │  parent-chunk fetch (richer context for LLM)
      ▼
 generator_node (qwen3:8b /think) → cited answer
      │
      ▼  critic_node (gemma3:4b /no_think) → {"grounded": true/false}
      │  if not grounded → retry retriever (max 3×)
      ▼
 Streamlit: answer + source citations
```

---

## Supported Document Types

| Format | Parsing strategy |
|---|---|
| `.pdf` | pdfplumber text + tables; OCR fallback for scanned pages |
| `.pptx` / `.ppt` | python-pptx: slides + speaker notes |
| `.docx` / `.doc` | python-docx: paragraphs + tables |
| `.png` `.jpg` `.jpeg` `.tiff` `.bmp` | Tesseract OCR via microservice |
| `.csv` | Converted to markdown table |
| `.xlsx` | openpyxl → markdown table |
| `.txt` `.md` `.html` `.htm` | Direct read + language detection |

---

## Configuration

All settings live in `config.py` — never hardcode paths or model names elsewhere.

```python
# config.py — key parameters
PRIMARY_LLM       = 'qwen3:8b'       # Generator node
FALLBACK_LLM      = 'gemma3:4b'      # Planner + critic nodes
EMBED_MODEL       = 'nomic-embed-text'

PARENT_CHUNK_SIZE = 1024              # tokens per parent chunk
CHILD_CHUNK_SIZE  = 256               # tokens per child chunk
CHUNK_OVERLAP     = 50                # overlap between adjacent chunks

DENSE_TOP_K       = 50               # dense candidates before RRF
RRF_K             = 60               # RRF damping constant
RERANK_TOP_N      = 10               # reranker output size
```

---

## Running Tests

### Go tests

```bash
go test ./...           # all packages
go test -v ./internal/chunker/...   # chunker only
go test -v ./internal/config/...    # config only
```

### Python sanity check

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from config import PRIMARY_LLM
from agents.state import AgentState
from retrieval.fusion import reciprocal_rank_fusion
from ingestion.chunker import chunk_document
print('All core imports OK')
"
```

---

## Model RAM Budget (12 GB System)

| Component | RAM | Notes |
|---|---|---|
| qwen3:8b (Q4_K_M) | ~5.5 GB | Loaded during generation |
| gemma3:4b (Q4_K_M) | ~3.0 GB | Swap in for critic/planner |
| nomic-embed-text | ~0.3 GB | Ingestion only |
| bge-reranker-v2-m3 | ~1.1 GB | Stays resident after first query |
| ChromaDB index | ~0.5–1.5 GB | Scales with corpus |
| BM25 index (RAM) | ~0.1–0.3 GB | Resident in Python process |
| Streamlit + OS | ~2.0 GB | Reserved |
| **TOTAL** | **~9.9–11.1 GB** | ✅ Fits within 12 GB |

> **Tip:** Set `OLLAMA_KEEP_ALIVE=-1` to keep models in RAM between queries.

---

## Troubleshooting

### Pillow build fails on Python 3.13
```bash
pip install --upgrade pip
pip install pillow>=10.4.0
```

### Tesseract not found
```bash
which tesseract
tesseract --version
sudo apt-get install tesseract-ocr tesseract-ocr-sin tesseract-ocr-tam
```

### Ollama connection refused
```bash
ollama serve
curl http://localhost:11434/api/tags
```

### OCR microservice not responding
```bash
uvicorn ocr_service.main:app --port 8765
curl http://localhost:8765/health
```

### ChromaDB collection not found
The collection is created automatically on first ingestion. Drop a file into `watched_docs/` or click **Re-index all** in the sidebar.

### BM25 index is stale
```python
from retrieval.bm25_store import rebuild_bm25
rebuild_bm25()
```

### Go binary ChromaDB error
The Go binary logs `[CHROMA] could not create collection` if ChromaDB HTTP server isn't running at `:8000`. This is non-fatal — the file watcher continues. For full Go-side ingestion, run ChromaDB in server mode:
```bash
chroma run --path ./chroma_db --port 8000
```
The Python/Streamlit pipeline uses `PersistentClient` (no server required) and is the recommended path.

### Sinhala OCR accuracy is poor
- Ensure scan DPI ≥ 300
- Verify: `tesseract --list-langs | grep sin`
- Try higher contrast preprocessing (see `ocr_service/main.py` `preprocess_aggressive`)

---

## Performance Expectations (CPU-only, 12 GB RAM)

| Operation | Expected time |
|---|---|
| Ingest 1-page digital PDF | 3–8 s |
| Ingest 1-page scanned PDF | 8–20 s |
| Query planning (gemma3:4b) | 2–8 s |
| Dense + BM25 retrieval | 0.5–2 s |
| BGE reranking (20 chunks) | 1–3 s |
| Answer generation (qwen3:8b) | 15–45 s |
| **Full pipeline (warm cache)** | **20–60 s** |

---

<div align="center">

**DocMind** · Runs locally · Respects your privacy · Sinhala · Tamil · English

</div>
