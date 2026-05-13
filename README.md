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

DocMind is an **advanced, agentic Retrieval-Augmented Generation (RAG) system** that runs entirely on your local hardware. Drop any document into a watched folder and immediately ask questions about it in natural language — across Sinhala, Tamil, and English.

It is also a **structured learning project**. The codebase is divided into six independent layers, each with its own guide. Build and understand each layer before connecting them, and you will finish with a production-quality RAG system and a deep understanding of how every component works.

### Core Value Proposition

| Property | Description |
|---|---|
| 🔒 100% local | No API keys, no data leaves your machine, works offline |
| 🔍 Advanced RAG | Hybrid search, reranking, parent-child chunking, RRF fusion |
| 🤖 Agentic pipeline | LangGraph orchestration with query planning, self-critique, and re-retrieval |
| 🌐 Multilingual OCR | Sinhala, Tamil, and English across all document types |
| 📄 Universal documents | PDF, PPTX, DOCX, images, CSV, TXT, HTML and more |
| 🎓 Learning-first | Each layer is modular, observable, and independently testable |

### Why DocMind?

| Feature | DocMind | Typical RAG demo |
|---|---|---|
| Runs 100% offline | ✅ | ❌ (needs OpenAI API) |
| Sinhala + Tamil OCR | ✅ | ❌ |
| Hybrid search (dense + BM25) | ✅ | ❌ (dense only) |
| Cross-encoder reranking | ✅ | ❌ |
| Self-correcting agent loop | ✅ | ❌ |
| Works on 12 GB RAM laptop | ✅ | N/A |
| Source citations in UI | ✅ | ❌ |

---

## Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| LLM inference | Ollama | Local model serving, OpenAI-compatible API |
| Primary LLM | qwen3:8b | Best multilingual model under 6 GB; ~5.5 GB Q4_K_M |
| Fallback LLM | gemma3:4b | Fast planner/critic; only 3 GB; 2× faster than qwen3:8b |
| Embeddings | nomic-embed-text v2 | 100+ language MoE model, 274 MB |
| Vector DB | ChromaDB 0.5+ | Local persistent, zero config |
| Sparse search | rank_bm25 | Pure Python BM25; language-agnostic whitespace tokeniser |
| Reranker | BGE-reranker-v2-m3 | Multilingual cross-encoder; ~300ms per 20 chunks |
| OCR engine | Tesseract 5 | sin + tam + eng language packs |
| RAG framework | LlamaIndex 0.10+ | Document parsing and indexing |
| Agent framework | LangGraph 0.2+ | Stateful agent graphs with conditional edges |
| Image processing | OpenCV + Pillow | OCR pre-processing (grayscale, threshold, denoise) |
| PDF parsing | pdfplumber 0.10+ | Table-aware text extraction |
| Office docs | python-pptx / python-docx | Full PPTX/DOCX support with notes extraction |
| File watching | watchdog 3.0+ (Python) / fsnotify (Go) | Cross-platform file system events |
| OCR microservice | FastAPI | Thin Python service at :8765; isolates Tesseract from core |
| Frontend | Streamlit 1.35+ | Python-native chat UI |
| Language detect | langdetect | Script/language identification for OCR routing |
| Tokeniser | tiktoken cl100k_base | Consistent token counting across chunker and embedder |

> **Architecture note:** The file watcher (Layer 1) is implemented in Go using `fsnotify` for performance and portability. All other layers (L2–L6) are Python.

---

## User Stories

| ID | As a developer, I want to... | So that... |
|---|---|---|
| US-01 | Drop any file into a folder and have it indexed automatically | I never think about ingestion |
| US-02 | Query documents in Sinhala | I can search my native-language documents |
| US-03 | Ask multi-step questions | The system decomposes and answers complex queries |
| US-04 | See which documents and chunks sourced each answer | I can verify factual accuracy |
| US-05 | Watch the agent critique and retry retrieval | I can learn how self-correction works |
| US-06 | Query scanned image documents | My printed materials are also searchable |
| US-07 | Select which LLM model to use from the UI | I can compare qwen3:8b vs gemma3:4b responses |
| US-08 | See retrieval scores and chunk content in debug mode | I can debug and tune my pipeline |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Go 1.23+
- [Ollama](https://ollama.ai) installed
- Ubuntu 22+ / macOS 13+ / Windows 11
- 12 GB RAM minimum (16 GB recommended)

### 1. Clone and install

```bash
git clone <your-repo-url> docmind
cd docmind
pip install -r requirements.txt
```

### 2. Install Tesseract with multilingual packs

```bash
# Ubuntu / Debian
sudo apt-get install -y tesseract-ocr tesseract-ocr-sin tesseract-ocr-tam tesseract-ocr-eng

# macOS
brew install tesseract tesseract-lang

# Verify
tesseract --list-langs   # should include: sin, tam, eng
```

### 3. Pull Ollama models

Total download: approximately **10 GB**. Run in order:

```bash
ollama pull qwen3:8b          # Primary LLM   — ~5.5 GB
ollama pull gemma3:4b         # Fallback LLM  — ~3.0 GB
ollama pull nomic-embed-text  # Embeddings    — ~274 MB

# Verify
ollama list
```

### 4. Pre-cache the reranker

```bash
python -c "from FlagEmbedding import FlagReranker; FlagReranker('BAAI/bge-reranker-v2-m3')"
# Downloads ~1.1 GB from Hugging Face — cached after first run
```

### 5. Start Ollama and run DocMind

```bash
# Terminal 1 — keep Ollama running (optional: keep models resident)
export OLLAMA_KEEP_ALIVE=-1
ollama serve

# Terminal 2 — launch the app
streamlit run app/main.py
```

**Open [http://localhost:8501](http://localhost:8501) in your browser.**

Drop files into `watched_docs/` and start asking questions.

---

## System Architecture

```
watched_docs/          ← drop any file here
      │
      ▼  fsnotify (Go)
┌─────────────────────────────────────────────────────────────┐
│  L1  Document Watcher    debounce · dispatch · hot-reload   │  Go
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│  L2  OCR + Parser    Tesseract sin+tam+eng · PDF/PPTX/DOCX  │  Python
│                      OpenCV preprocessing · table extract   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│  L3  Chunker + Embedder    parent-child chunking (1024/256) │  Python
│                            nomic-embed-text v2 · ChromaDB   │
└─────────────────────────────┬───────────────────────────────┘
                              │ (ingestion complete)
         ╔════════════════════╩════════════════════╗
         ║           Query pipeline                ║
         ╚════════════════════╦════════════════════╝
                              │
┌─────────────────────────────▼───────────────────────────────┐
│  L4  Hybrid Retrieval    dense (ChromaDB) + sparse (BM25)   │  Python
│                          RRF fusion → top-20 candidates     │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│  L5  Reranker + Agent    BGE cross-encoder → top-10         │  Python
│                          LangGraph: plan→retrieve→gen→critic│
│                          Self-correcting loop (max 3×)      │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│  L6  Streamlit UI        chat · citations · debug mode      │  Python
│                          model selector · language filter   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User drops file → watched_docs/
    ↓  watchdog detects change
L1: Dispatcher routes by file extension
    ↓
L2: Parser extracts text  (+OCR if scanned)
    ↓
L3: Semantic chunker → parent + child chunks
    ↓  nomic-embed-text v2
    ChromaDB upsert  +  BM25 index rebuild
    ─────────── ingestion complete ───────────

User submits query in Streamlit
    ↓
L5: LangGraph planner decomposes query  (gemma3:4b /no_think)
    ↓
L4: Dense search (ChromaDB) ──┐
L4: Sparse BM25 search        ──┴→ RRF fusion → top-20
    ↓
L5: BGE reranker → top-10 chunks
    ↓
L5: Generator node → cited answer  (qwen3:8b /think)
    ↓
L5: Critic node → grounding check  (gemma3:4b /no_think)
    ↓  if not grounded → retry (max 3×)
L6: Streamlit displays answer + source citations
```

---

## Layer Details

### L1 — Document Watcher
**Language:** Go | **Key lib:** fsnotify

Monitors `watched_docs/` for CREATE, MODIFY, and DELETE events. A 2-second debounce window prevents duplicate dispatches from editors that trigger multiple rapid writes. Each event dispatches to a parser in an isolated goroutine with panic recovery — a crash in one parse job never affects the watcher loop.

- Configurable file type map (13 extensions supported)
- Unknown types are logged and skipped without crashing
- DELETE events trigger index cleanup in ChromaDB and BM25

> Full guide: [L1 — Document Watcher](./L1_Document_Watcher.md)

---

### L2 — OCR + Parser
**Language:** Python | **Key libs:** Tesseract, pdfplumber, FastAPI, OpenCV

A thin FastAPI microservice at `:8765` wraps Tesseract and langdetect, keeping OCR dependencies isolated from the core pipeline. The PDF parser auto-detects scanned pages by checking text density and falls back to page-level OCR.

**OCR pre-processing pipeline:**
1. Convert to grayscale
2. Otsu thresholding (automatic black/white separation)
3. Non-local means denoising (removes scanner grain)
4. Tesseract LSTM engine (`--oem 3 --psm 6`)

| Format | Parser strategy |
|---|---|
| PDF (digital) | pdfplumber text layer + table extraction |
| PDF (scanned) | pdftoppm render → Tesseract OCR per page |
| PPTX | ZIP+XML: slide text + speaker notes |
| DOCX | docconv: headings, paragraphs, table cells |
| Images | Direct OCR via microservice |
| CSV/XLSX | Convert to markdown table format |
| TXT/MD/HTML | Direct read + language detection |

> Full guide: [L2 — OCR + Parser](./L2_OCR_Parser.md)

---

### L3 — Chunker + Embedder
**Language:** Python | **Key libs:** tiktoken, nomic-embed-text, ChromaDB

**Parent-child chunking:** small child chunks (256 tokens) are stored with embeddings for precise vector retrieval; their larger parent (1024 tokens) is fetched at query time to give the LLM rich context. A 50-token overlap between adjacent chunks preserves cross-boundary context.

- Sentence-boundary splitter handles English (`. ! ?`), Sinhala (`। ෴`), and Tamil (`।`) scripts
- Embeddings batched in groups of 32 to avoid OOM on 12 GB RAM
- ChromaDB configured with **cosine similarity** (not L2 distance)
- `DeleteBySource()` removes all chunks for a deleted file atomically

> Full guide: [L3 — Chunker + Embedder](./L3_Chunker_Embedder.md)

---

### L4 — Hybrid Retrieval Engine
**Language:** Python | **Key libs:** rank_bm25, ChromaDB

Dense retrieval captures semantic meaning ("automobile" ↔ "car"); sparse BM25 catches rare exact terms and low-resource language keywords. Reciprocal Rank Fusion (RRF, k=60) merges both ranked lists:

```
RRF_score = Σ 1 / (rank_in_list + k)
```

- BM25 index uses whitespace tokenisation — language-agnostic across Sinhala, Tamil, English
- RRF deduplicates by `chunk_id` and returns top-20 to the reranker
- Language metadata filter restricts dense search to a specific script when set
- Parent chunk is fetched after fusion — smaller child chunks rank, richer parents are read

> Full guide: [L4 — Hybrid Retrieval](./L4_Hybrid_Retrieval.md)

---

### L5 — Reranker + Agentic Orchestrator
**Language:** Python | **Key libs:** FlagEmbedding, LangGraph

BGE-reranker-v2-m3 is a **cross-encoder**: it reads query and chunk together, giving much higher precision than bi-encoder retrieval. Applied to the top-20 RRF candidates, it outputs the top-10 for the generator.

**LangGraph 4-node agent:**

| Node | Model | Mode | Responsibility |
|---|---|---|---|
| Planner | gemma3:4b | `/no_think` | Decompose query into ≤3 sub-questions (JSON output) |
| Retriever | — | — | Run full L4+reranker pipeline per sub-question, dedup top-15 |
| Generator | qwen3:8b | `/think` | Synthesize cited answer from retrieved context |
| Critic | gemma3:4b | `/no_think` | Check grounding; trigger re-retrieval if not grounded |

The critic outputs `{"grounded": true/false, "reason": "...", "missing": "..."}`. A conditional LangGraph edge loops back to the Retriever up to 3 times before accepting the best available answer.

> Full guide: [L5 — Reranker + Agent](./L5_Reranker_Agent.md)

---

### L6 — Streamlit Frontend
**Language:** Python | **Key lib:** Streamlit

Single-page chat UI. Streamlit reruns the entire script on every interaction — `st.session_state` is the only persistence layer.

- **Model selector:** qwen3:8b (better quality) vs gemma3:4b (2× faster)
- **Language filter:** All / English / Sinhala / Tamil — narrows dense retrieval to a script
- **Debug mode:** shows full parent text, child chunk preview, and all rerank/RRF scores per chunk
- **Source citations:** expandable sections below each answer showing filename, chunk number, and score
- **Re-index button:** enumerates `watched_docs/`, re-embeds all files, rebuilds BM25 index
- Watcher thread is guarded by a session state flag — starts exactly once across all Streamlit reruns

> Full guide: [L6 — Streamlit Frontend](./L6_Streamlit_Frontend.md)

---

## Models (Optimised for 12 GB RAM)

> `gemma3:27b` requires ~18–20 GB RAM and is **not compatible** with 12 GB systems — it causes constant disk swapping. See [Model Selection Guide](./00b_Model_Selection_12GB.md) for full reasoning.

### Model Decision

| Model | RAM (Q4_K_M) | Speed | Multilingual | Role |
|---|---|---|---|---|
| **qwen3:8b** ✅ PRIMARY | ~5.5 GB | 35–45 tok/s | ★★★★★ | Generation + complex planning |
| **gemma3:4b** ✅ FALLBACK | ~3.0 GB | 55–70 tok/s | ★★★★☆ | Fast critic + planner JSON output |
| nomic-embed-text v2 | ~0.3 GB | — | ★★★★★ | All embeddings (100+ languages) |
| bge-reranker-v2-m3 | ~1.1 GB | ~300ms/20 chunks | ★★★★★ | Cross-encoder reranking |
| ~~gemma3:27b~~ ❌ | ~18 GB | Too slow | ★★★★★ | **Exceeds 12 GB RAM limit** |

### qwen3 Thinking Modes

`qwen3:8b` has two modes controlled by a prefix in the user message:

| Prefix | Behaviour | Use for |
|---|---|---|
| `/think` | Shows reasoning chain before answering — slower, more accurate | Generator node |
| `/no_think` | Answers directly, no chain — faster, structured JSON | Planner and Critic nodes |

### Full RAM Budget

| Component | Memory | Notes |
|---|---|---|
| qwen3:8b (Q4_K_M) | ~5.5 GB | Loaded during chat queries |
| gemma3:4b (Q4_K_M) | ~3.0 GB | Swap in for critic/planner to save RAM |
| nomic-embed-text v2 | ~0.3 GB | Runs during ingestion; unloads after |
| bge-reranker-v2-m3 | ~1.1 GB | Loaded on first query; stays resident |
| ChromaDB vector index | ~0.5–1.5 GB | Scales with corpus size |
| BM25 index (in-memory) | ~0.1–0.3 GB | Resident in Python process RAM |
| Streamlit + Python overhead | ~0.4 GB | Always resident |
| OS + other processes | ~2.0 GB | Reserve — do not fill entirely |
| **TOTAL (primary LLM active)** | **~9.9–11.1 GB** | **Fits within 12 GB** ✅ |

> **Memory tip:** To keep `qwen3:8b` resident between queries, set `OLLAMA_KEEP_ALIVE=-1` before starting Ollama.

---

## Supported Document Types

| Format | Method | Notes |
|---|---|---|
| `.pdf` | pdfplumber + Tesseract OCR | Auto-detects scanned vs digital pages |
| `.pptx` | python-pptx | Extracts slides + speaker notes |
| `.docx` | python-docx | Extracts headings, paragraphs, tables |
| `.xlsx` / `.csv` | openpyxl / csv | Converted to markdown table format |
| `.png` `.jpg` `.jpeg` `.tiff` `.bmp` | Tesseract OCR | Full OpenCV pre-processing pipeline |
| `.txt` `.md` `.html` | Direct read | No OCR needed |

---

## Multilingual Support

DocMind supports **Sinhala (සිංහල), Tamil (தமிழ்), and English** throughout the full pipeline:

| Layer | Multilingual handling |
|---|---|
| OCR | Tesseract `sin+tam+eng` combined mode with langdetect auto-selection |
| Embedding | nomic-embed-text v2 covers 100+ languages in a shared vector space |
| BM25 | Whitespace tokeniser works across all three scripts |
| Reranker | BGE-reranker-v2-m3 supports multilingual relevance scoring |
| LLM | qwen3:8b responds in whichever language the user writes in |
| UI | Language filter restricts retrieval to chunks in the selected language |

---

## Non-Functional Requirements

| ID | Category | Requirement | Target |
|---|---|---|---|
| NFR-01 | Performance | First response latency (qwen3:8b, 10 chunks) | < 45 seconds |
| NFR-02 | Performance | Embedding throughput (nomic-embed-text v2) | > 200 chunks/min |
| NFR-03 | Reliability | Ingestion failure must not crash the watcher | 100% isolation |
| NFR-04 | Privacy | Zero network calls during query/response cycle | Fully offline |
| NFR-05 | Usability | New document indexed and queryable after drop | < 60 seconds |
| NFR-06 | Observability | All retrieval scores logged per query | Structured JSON log |
| NFR-07 | Portability | Runs on Ubuntu 22+, macOS 13+, Windows 11 | Cross-platform |
| NFR-08 | Storage | Vector DB storage per 10K chunks | < 2 GB |

---

## Success Metrics

### Retrieval Quality

| Metric | Target |
|---|---|
| Retrieval precision @10 | > 0.75 |
| Answer groundedness (no re-retrieval needed) | > 0.80 |
| Multi-hop question accuracy | > 0.65 |

### System Performance

| Metric | Target |
|---|---|
| End-to-end query latency (qwen3:8b) | < 45 seconds |
| Ingestion time per 10-page PDF | < 20 seconds |
| OCR throughput (A4 @ 300 DPI) | < 5 seconds/page |

### Multilingual

| Metric | Target |
|---|---|
| Sinhala OCR character accuracy (clean scan, 300 DPI) | > 90% |
| Cross-language retrieval precision @5 | > 0.60 |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| qwen3:8b too slow on laptop CPU | Medium | High | Use `/no_think` mode; swap to gemma3:4b for simple queries |
| Tesseract Sinhala accuracy low on poor scans | High | Medium | OpenCV denoise pre-processing; require 300 DPI minimum |
| ChromaDB index corruption on crash | Low | High | Periodic backup; rebuild-from-source command |
| BM25 memory growth on large corpora | Medium | Medium | Persist index to disk; incremental update |
| LangGraph critic loop never terminates | Low | High | Hard cap at 3 retries |
| Multilingual chunk splitting at script boundary | Medium | Medium | Sentence-boundary tokeniser; test with mixed-language docs |

---

## Project Structure

```
docmind/
├── app/
│   └── main.py                 # Streamlit entry point (Layer 6)
├── ingestion/
│   ├── watcher.py              # File system watcher (Layer 1)
│   ├── dispatcher.py           # File → parser router (Layer 1)
│   ├── chunker.py              # Parent-child chunking (Layer 3)
│   ├── ocr.py                  # Tesseract OCR utility (Layer 2)
│   └── parsers/
│       ├── __init__.py         # Parser registry
│       ├── pdf_parser.py       # PDF + scanned PDF
│       ├── pptx_parser.py      # PowerPoint slides
│       ├── docx_parser.py      # Word documents
│       ├── image_parser.py     # Images (OCR)
│       ├── csv_parser.py       # CSV / Excel
│       └── text_parser.py      # TXT / MD / HTML
├── retrieval/
│   ├── embedder.py             # nomic-embed-text via Ollama (Layer 3)
│   ├── vector_store.py         # ChromaDB upsert/delete (Layer 3)
│   ├── bm25_store.py           # BM25 index (Layer 4)
│   ├── fusion.py               # RRF algorithm (Layer 4)
│   ├── retriever.py            # Unified retrieve() interface (Layer 4)
│   └── reranker.py             # BGE cross-encoder (Layer 5)
├── agents/
│   ├── state.py                # LangGraph AgentState TypedDict (Layer 5)
│   ├── nodes.py                # Planner/Retriever/Generator/Critic (Layer 5)
│   └── graph.py                # LangGraph assembly + run_agent() (Layer 5)
├── ocr_service/
│   └── main.py                 # FastAPI OCR microservice at :8765 (Layer 2)
├── docs/                       # All documentation (this folder)
│   ├── README.md               # ← you are here
│   ├── 00_PRD.md               # Product Requirements Document
│   ├── 00b_Model_Selection_12GB.md
│   ├── L1_Document_Watcher.md
│   ├── L2_OCR_Parser.md
│   ├── L3_Chunker_Embedder.md
│   ├── L4_Hybrid_Retrieval.md
│   ├── L5_Reranker_Agent.md
│   └── L6_Streamlit_Frontend.md
├── watched_docs/               # Drop documents here (auto-created)
├── chroma_db/                  # Vector database (auto-created)
├── bm25_index.pkl              # BM25 index (auto-created)
├── config.py                   # Central configuration
└── requirements.txt
```

---

## Documentation

| Document | Description |
|---|---|
| [PRD](./00_PRD.md) | Full Product Requirements — goals, user stories, functional requirements, success metrics |
| [Model Selection](./00b_Model_Selection_12GB.md) | Why qwen3:8b was chosen, RAM budget breakdown, performance benchmarks |
| [L1 — Document Watcher](./L1_Document_Watcher.md) | fsnotify setup, debouncing, dispatcher, hot-reload |
| [L2 — OCR + Parser](./L2_OCR_Parser.md) | Tesseract OCR, OpenCV pre-processing, PDF/PPTX/DOCX/image parsers |
| [L3 — Chunker + Embedder](./L3_Chunker_Embedder.md) | Parent-child chunking, nomic embeddings, ChromaDB |
| [L4 — Hybrid Retrieval](./L4_Hybrid_Retrieval.md) | BM25, RRF fusion, parent-child lookup, unified retriever |
| [L5 — Reranker + Agent](./L5_Reranker_Agent.md) | BGE reranker, LangGraph 4-node graph, system prompts, critic loop |
| [L6 — Streamlit Frontend](./L6_Streamlit_Frontend.md) | Chat UI, citation display, debug mode, sidebar controls |

---
<!-- 
## Learning Roadmap

DocMind is designed to be built in phases. Complete each phase before moving to the next:

### Phase 1 — Foundation
> Build the core pipeline end-to-end. Get one document queryable.

- [ ] Set up `config.py` with all paths and model names
- [ ] Implement `L1` watcher and dispatcher (text files only first)
- [ ] Implement `L2` text and PDF parsers
- [ ] Implement `L3` chunker, embedder, and ChromaDB store
- [ ] Implement `L6` basic Streamlit chat with direct ChromaDB query
- **Milestone:** Ask a question about a PDF and get an answer

### Phase 2 — Advanced Retrieval
> Add hybrid search. Compare retrieval quality before and after.

- [ ] Implement `L4` BM25 index and bm25_search()
- [ ] Implement `L4` RRF fusion
- [ ] Implement `L4` unified retrieve() with parent-child lookup
- [ ] Implement `L5` BGE reranker
- **Milestone:** Run the comparison experiment from L4 guide. See the difference.

### Phase 3 — Agentic Loop
> Add LangGraph. Watch the agent plan, retrieve, generate, and self-correct.

- [ ] Implement `L5` AgentState and all four nodes
- [ ] Implement `L5` LangGraph with conditional critic edge
- [ ] Connect `run_agent()` to Streamlit frontend
- **Milestone:** Trigger the critic loop with an unanswerable question. Watch it retry.

### Phase 4 — Multilingual
> Validate Sinhala and Tamil OCR. Test cross-language retrieval.

- [ ] Verify Tesseract `sin` and `tam` packs are installed
- [ ] Test with a scanned Sinhala PDF
- [ ] Test cross-language retrieval (Tamil query → English document)
- [ ] Tune OpenCV pre-processing for your specific document quality
- **Milestone:** Ask a question in Sinhala, get a cited answer.

### Phase 5 — Observability
> Add structured logging and evaluation to understand failure modes.

- [ ] Enable debug mode and inspect chunk scores for 10 test queries
- [ ] Log all retrieval scores to SQLite
- [ ] Build a small eval set (5–10 question/answer pairs) and score your system
- **Milestone:** Identify one retrieval failure and trace it to a specific layer. -->

---

## Configuration Reference

All settings live in `config.py`. No other file should hardcode paths or model names.

```python
# config.py — all configurable parameters
PRIMARY_LLM       = 'qwen3:8b'       # Generator node
FALLBACK_LLM      = 'gemma3:4b'      # Planner + critic nodes
EMBED_MODEL       = 'nomic-embed-text'
THINK_PREFIX      = '/think '         # qwen3 deep reasoning
NO_THINK_PREFIX   = '/no_think '      # qwen3 fast output

PARENT_CHUNK_SIZE = 1024              # tokens per parent chunk
CHILD_CHUNK_SIZE  = 256               # tokens per child chunk
CHUNK_OVERLAP     = 50                # overlap between adjacent chunks

DENSE_TOP_K       = 50               # dense candidates before RRF
RRF_K             = 60               # RRF damping constant
RERANK_TOP_N      = 10               # reranker output size
```

---

## Requirements

```
# requirements.txt
watchdog>=3.0
pdfplumber>=0.10
python-pptx
python-docx
openpyxl
pytesseract
pillow
opencv-python
langdetect
chromadb>=0.5
tiktoken
rank-bm25
FlagEmbedding
langgraph>=0.2
langchain
langchain-ollama
llama-index>=0.10
llama-index-embeddings-ollama
streamlit>=1.35
fastapi
uvicorn
requests
```

Install everything:

```bash
pip install -r requirements.txt
```

---

## Troubleshooting

### Tesseract not found
```bash
# Check installation
which tesseract
tesseract --version

# If missing on Ubuntu:
sudo apt-get install tesseract-ocr tesseract-ocr-sin tesseract-ocr-tam
```

### Ollama connection refused
```bash
# Make sure Ollama is running
ollama serve

# Test the connection
curl http://localhost:11434/api/tags
```

### ChromaDB collection not found
```bash
# The collection is created on first ingestion
# Drop a file into watched_docs/ or click Re-index in the sidebar
```

### qwen3:8b too slow
```bash
# Switch to gemma3:4b in the sidebar model selector
# Or use /no_think prefix for simpler queries
# Check if GPU is being used:
ollama run qwen3:8b "" 2>&1 | grep "gpu layers"
```

### BM25 index is stale
```python
# Manually rebuild from Python:
from retrieval.bm25_store import rebuild_bm25
rebuild_bm25()
```

### Sinhala OCR accuracy is poor
- Ensure scan DPI ≥ 300 (check with `pytesseract.image_to_data()`)
- Try `preprocess_aggressive()` from the L2 guide
- Verify Tesseract `sin` pack: `tesseract --list-langs | grep sin`

### OCR microservice not responding
```bash
# Start the FastAPI service manually
uvicorn ocr_service.main:app --port 8765
# Verify
curl http://localhost:8765/health
```

<!-- ---

## Performance on 12 GB RAM

> Benchmarks are for **CPU-only inference**. A discrete GPU with 4+ GB VRAM gives 3–5× speedup automatically via Ollama.

| Operation | Expected Time | Model Used | Notes |
|---|---|---|---|
| Ingest 1-page PDF (digital) | 3–8 sec | nomic-embed-text | Mostly embedding time |
| Ingest 1-page scanned PDF | 8–20 sec | Tesseract + nomic | OCR adds ~5–12 sec/page |
| Ingest digital PDF (10 pages) | 15–40 sec | nomic-embed-text | Embedding is the bottleneck |
| Ingest scanned PDF (10 pages) | 60–180 sec | Tesseract + nomic | OCR adds ~5–15 sec per page |
| Query planning | 2–8 sec | gemma3:4b /no_think | Fast JSON output |
| Dense + BM25 retrieval | 0.5–2 sec | nomic-embed-text | Fast after index built |
| BGE reranking (20 chunks) | 1–3 sec | bge-reranker-v2-m3 | CPU cross-encoder scoring |
| Answer generation (short) | 15–25 sec | qwen3:8b /think | ~200–300 token response |
| Answer generation (long) | 30–60 sec | qwen3:8b /think | ~500–800 token response |
| Critic grounding check | 5–12 sec | gemma3:4b /no_think | JSON verdict |
| **Full pipeline (warm cache)** | **20–45 sec** | **All models** | **Models already in RAM** |
| First query after startup | 30–70 sec | All models | Model loading adds ~10–15 sec |

--- -->

<div align="center">

**DocMind** · Built for learning · Runs locally · Respects your privacy

*Sinhala · Tamil · English*

</div>
