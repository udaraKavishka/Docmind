package config

import (
	"os"
	"path/filepath"
	"runtime"
)

func projectRoot() string {
	_, file, _, _ := runtime.Caller(0)
	// internal/config/config.go → go up 3 levels to project root
	return filepath.Join(filepath.Dir(file), "..", "..")
}

var (
	BaseDir    = projectRoot()
	WatchedDir = filepath.Join(projectRoot(), "watched_docs")
	ChromaDir  = filepath.Join(projectRoot(), "chroma_db")
	BM25Path   = filepath.Join(projectRoot(), "bm25_index.json")
	LogDir     = filepath.Join(projectRoot(), "logs")
)

const (
	OllamaBaseURL = "http://localhost:11434"
	EmbedModel    = "nomic-embed-text"
	PrimaryLLM    = "qwen3:8b"
	FallbackLLM   = "gemma3:4b"
	OCRServiceURL = "http://localhost:8765"

	ThinkPrefix   = "/think "
	NoThinkPrefix = "/no_think "

	ParentChunkSize = 1024
	ChildChunkSize  = 256
	ChunkOverlap    = 50

	DenseTopK    = 50
	RRFK         = 60
	RerankTopN   = 10
	EmbedBatch   = 32
	DebounceMs   = 2000
	MaxRetries   = 3
	MinTextChars = 50
)

// FileTypeMap maps lowercase file extensions to parser keys.
var FileTypeMap = map[string]string{
	".pdf":  "pdf",
	".pptx": "pptx",
	".docx": "docx",
	".xlsx": "csv",
	".csv":  "csv",
	".txt":  "text",
	".md":   "text",
	".html": "text",
	".png":  "image",
	".jpg":  "image",
	".jpeg": "image",
	".tiff": "image",
	".bmp":  "image",
}

// Ensure watched_docs exists at startup.
func init() {
	os.MkdirAll(WatchedDir, 0755)
	os.MkdirAll(LogDir, 0755)
}