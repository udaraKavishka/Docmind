package ingestion

import (
	"log"
	"path/filepath"
	"strings"

	"docmind/internal/chunker"
	"docmind/internal/config"
	"docmind/internal/ingestion/parsers"
	"docmind/internal/vectorstore"
)

// Ingest routes a file event to the correct parser, chunks, embeds, and stores the result.
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

	var allChunks []chunker.Chunk
	for _, doc := range docs {
		allChunks = append(allChunks, chunker.ChunkDocument(doc)...)
	}

	if err := vectorstore.UpsertChunks(allChunks); err != nil {
		log.Printf("[INGEST] upsert failed %s: %v", filepath.Base(path), err)
		return
	}

	childCount := 0
	for _, c := range allChunks {
		if c.ChunkType == "child" {
			childCount++
		}
	}
	log.Printf("[INGEST] indexed %s: %d child chunks", filepath.Base(path), childCount)

	// BM25 rebuild added in Layer 4.
}

func handleDelete(path string) {
	if err := vectorstore.DeleteBySource(path); err != nil {
		log.Printf("[INGEST] delete failed %s: %v", filepath.Base(path), err)
	}
}
