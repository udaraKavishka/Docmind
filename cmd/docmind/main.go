package main

import (
	"log"

	"docmind/internal/config"
	"docmind/internal/ingestion"
	"docmind/internal/watcher"
)

func main() {
	log.SetFlags(log.Ldate | log.Ltime | log.Lmsgprefix)

	// Start the file watcher as a background goroutine.
	// It runs forever until the process exits.
	go func() {
		if err := watcher.Start(config.WatchedDir, ingestion.Ingest); err != nil {
			log.Fatalf("[MAIN] watcher failed: %v", err)
		}
	}()

	// HTTP server starts here in Layer 6.
	// For now, block forever so the watcher keeps running.
	log.Println("[MAIN] DocMind started. Drop files into", config.WatchedDir)
	select {} // block
}