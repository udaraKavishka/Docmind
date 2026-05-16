package ingestion

import (
	"log"
	"path/filepath"
	"strings"

	"docmind/internal/config"
)

// Ingest routes a file event to the correct parser based on its extension.
// This is the IngestFn passed to watcher.Start().
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

	// Parser lookup and downstream pipeline added in Layers 2, 3, 4.
	log.Printf("[INGEST] dispatching %s as %s", filepath.Base(path), parserKey)
}

func handleDelete(path string) {
	// Wired to ChromaDB delete in Layer 4.
	log.Printf("[INGEST] DELETE queued for %s", filepath.Base(path))
}