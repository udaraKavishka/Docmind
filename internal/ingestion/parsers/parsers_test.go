package parsers

import (
	"path/filepath"
	"runtime"
	"testing"
)

func TestTextParser(t *testing.T) {
	_, file, _, _ := runtime.Caller(0)
	root := filepath.Join(filepath.Dir(file), "..", "..", "..")

	p := &TextParser{}
	docs, err := p.Parse(filepath.Join(root, "watched_docs", "test.txt"))
	if err != nil {
		t.Fatalf("parse error: %v", err)
	}
	if len(docs) == 0 {
		t.Fatal("expected at least one doc")
	}
	t.Logf("parsed %d docs, first 100 chars: %s", len(docs), docs[0].Text[:min(100, len(docs[0].Text))])
}
