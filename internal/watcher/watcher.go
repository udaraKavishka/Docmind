package watcher

import (
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"docmind/internal/config"

	"github.com/fsnotify/fsnotify"
)

// IngestFn is the callback called after the debounce window for each file event.
type IngestFn func(path string, action string)

type debouncer struct {
	pending  sync.Map // map[string]*time.Timer
	window   time.Duration
	ingestFn IngestFn
}

func newDebouncer(ingestFn IngestFn) *debouncer {
	return &debouncer{
		window:   time.Duration(config.DebounceMs) * time.Millisecond,
		ingestFn: ingestFn,
	}
}

func (d *debouncer) schedule(path, action string) {
	if existing, loaded := d.pending.LoadAndDelete(path); loaded {
		existing.(*time.Timer).Stop()
	}
	t := time.AfterFunc(d.window, func() {
		d.pending.Delete(path)
		d.dispatch(path, action)
	})
	d.pending.Store(path, t)
}

func (d *debouncer) dispatch(path, action string) {
	ext := strings.ToLower(filepath.Ext(path))
	if _, ok := config.FileTypeMap[ext]; !ok {
		log.Printf("[WATCHER] unsupported type: %s — skipping", filepath.Base(path))
		return
	}
	log.Printf("[WATCHER] %s: %s", action, filepath.Base(path))

	// Isolate the ingest call — panic here must not kill the watcher goroutine.
	defer func() {
		if r := recover(); r != nil {
			log.Printf("[WATCHER] panic ingesting %s: %v", filepath.Base(path), r)
		}
	}()
	d.ingestFn(path, action)
}

// Start monitors watchedDir and calls ingestFn for each debounced file event.
// Blocks until the watcher is closed. Run in a goroutine from main.
func Start(watchedDir string, ingestFn IngestFn) error {
	if err := os.MkdirAll(watchedDir, 0755); err != nil {
		return err
	}

	fw, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}
	defer fw.Close()

	if err := fw.Add(watchedDir); err != nil {
		return err
	}
	log.Printf("[WATCHER] watching: %s", watchedDir)

	d := newDebouncer(ingestFn)

	for {
		select {
		case event, ok := <-fw.Events:
			if !ok {
				return nil
			}
			switch {
			case event.Has(fsnotify.Create):
				d.schedule(event.Name, "CREATE")
			case event.Has(fsnotify.Write):
				// Write == MODIFY for already-existing files
				d.schedule(event.Name, "MODIFY")
			case event.Has(fsnotify.Remove), event.Has(fsnotify.Rename):
				d.schedule(event.Name, "DELETE")
			// Chmod events are ignored — they fire on metadata-only changes
			}

		case err, ok := <-fw.Errors:
			if !ok {
				return nil
			}
			log.Printf("[WATCHER] error: %v", err)
		}
	}
}