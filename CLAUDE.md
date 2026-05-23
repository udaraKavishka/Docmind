# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DocMind** is a fully local, privacy-first, agentic RAG (Retrieval-Augmented Generation) system. No data leaves the machine — all inference runs via Ollama. The system supports Sinhala, Tamil, and English documents.

The codebase is a **layered learning project**: each of the 6 architectural layers is independent and buildable in sequence. Layers 2–6 are not yet implemented; stubs exist for Layer 2 parsers.

## Architecture

The system has two runtimes:

**Go binary (`cmd/docmind/`)** — the main process:
- `internal/watcher` — `fsnotify`-based folder watcher with debouncing (2 s). Calls `ingestion.Ingest` for every file event.
- `internal/ingestion` — dispatcher that routes file events to the correct parser by extension. DELETE events queue ChromaDB removal (not yet wired).
- `internal/ingestion/parsers` — `Parser` interface + registry (`pdf`, `pptx`, `docx`, `image`, `csv`, `text`). Parser structs are registered in `init()` but implementations are stubs pending Layer 2.
- `internal/ocr` — HTTP client for the OCR microservice (`/ocr/image`, `/ocr/detect-lang`). Sends base64-encoded images, receives extracted text and language tag.
- `internal/config` — all constants and paths in one place. `projectRoot()` uses `runtime.Caller` to find the repo root from the binary's source location.

**Python microservice (`ocr_service/`)** — FastAPI on port 8765:
- Tesseract OCR with OpenCV preprocessing (grayscale → Otsu threshold → denoise).
- `langdetect` for language identification, mapped to `sin`/`tam`/`eng`.

**Planned layers (docs only, not yet implemented):**
- L3: Chunking + embedding → ChromaDB (`chroma_db/`)
- L4: Hybrid retrieval (dense + BM25 sparse, RRF fusion, `bm25_index.json`)
- L5: LangGraph reranker/agent (Ollama: `qwen3:8b` primary, `gemma3:4b` fallback, `nomic-embed-text` embeddings)
- L6: Streamlit frontend

## Commands

### Go service

```sh
# Run the watcher (from repo root)
go run ./cmd/docmind/

# Build
go build ./cmd/docmind/

# Run all Go tests
go test ./...

# Run tests for a specific package
go test ./internal/watcher/...
```

### OCR microservice

```sh
# Install Python dependencies (one-time)
pip install -r ocr_service/requirements.txt

# Start the OCR service (required before running the Go binary if OCR is needed)
uvicorn ocr_service.main:app --port 8765 --reload

# Health check
curl http://localhost:8765/health
```

### Tesseract language packs (required for multilingual OCR)

```sh
sudo apt install tesseract-ocr-sin tesseract-ocr-tam tesseract-ocr-eng
```

## Key Configuration (`internal/config/config.go`)

| Constant | Value | Purpose |
|---|---|---|
| `OCRServiceURL` | `http://localhost:8765` | Python OCR microservice |
| `OllamaBaseURL` | `http://localhost:11434` | Local Ollama instance |
| `EmbedModel` | `nomic-embed-text` | Embedding model |
| `PrimaryLLM` | `qwen3:8b` | Main reasoning model |
| `FallbackLLM` | `gemma3:4b` | Fallback when primary is slow |
| `WatchedDir` | `<root>/watched_docs/` | Drop files here to trigger ingestion |
| `ChromaDir` | `<root>/chroma_db/` | Vector store (Layer 3+) |

All paths are resolved relative to the repo root using `runtime.Caller` — config works regardless of where the binary is invoked from.

## Layer Implementation Order

The `docs/` folder contains a guide for each layer. Implement them in order: L1 (done) → L2 → L3 → L4 → L5 → L6. Each layer's guide specifies exactly which files to create/modify.

## Go Module

Module name: `docmind` (import paths: `docmind/internal/...`).
