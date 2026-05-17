package ingestion

import (
	"log"
	"path/filepath"
	"strings"

	"docmind/internal/config"
	"docmind/internal/ingestion/parsers"
)

// Ingest routes a file event to the correct parser based on its extension.
func Ingest(path string, action string) {
	if action == "DELETE" {
		handleDelete(path)
		return
	}

	ext := strings.ToLower(filepath.Ext(path))
	parserKey, ok := config.FileTypeMap[ext]
	if !ok {
		return
	}

	parser, err := parsers.Get(parserKey)
	if err != nil {
		log.Printf("[INGEST] unknown parser %s: %v", parserKey, err)
		return
	}

	docs, err := parser.Parse(path)
	if err != nil {
		log.Printf("[INGEST] parse failed %s: %v", filepath.Base(path), err)
		return
	}

	log.Printf("[INGEST] parsed %d docs from %s", len(docs), filepath.Base(path))

	// Downstream: chunker → embedder → vector store
	// Implemented in Layer 3.
	_ = docs
}

func handleDelete(path string) {
	// Wired to ChromaDB delete in Layer 4.
	log.Printf("[INGEST] DELETE queued for %s", filepath.Base(path))
}