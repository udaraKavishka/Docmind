package chunker

import (
	"strings"
	"testing"

	"docmind/internal/ingestion/parsers"
)

func TestSplitSentences(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  int // minimum expected sentence count
	}{
		{"english_basic", "Hello world. How are you? Fine!", 3},
		{"single_sentence", "No terminators here", 1},
		{"empty_string", "", 0},
		{"sinhala_terminator", "ආයුබෝවන්. ඔබ කෙසේ ද?", 2},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := splitSentences(tt.input)
			if len(got) < tt.want {
				t.Errorf("splitSentences(%q) = %d sentences; want >= %d", tt.input, len(got), tt.want)
			}
		})
	}
}

func TestCountTokens(t *testing.T) {
	text := "Hello, world!"
	count := countTokens(text)
	if count <= 0 {
		t.Errorf("countTokens(%q) = %d; want > 0", text, count)
	}
}

func TestMakeChunks_RespectsMaxTokens(t *testing.T) {
	// Build a text that's larger than 256 tokens
	longText := strings.Repeat("This is a sentence. ", 200)
	chunks := makeChunks(longText, 256)
	if len(chunks) == 0 {
		t.Fatal("makeChunks returned 0 chunks for long text")
	}
	for i, ch := range chunks {
		tok := countTokens(ch)
		if tok > 300 { // allow small overshoot due to overlap
			t.Errorf("chunk[%d] has %d tokens, exceeds limit of 256", i, tok)
		}
	}
}

func TestChunkDocument_ParentChild(t *testing.T) {
	doc := parsers.ParsedDoc{
		Text:     strings.Repeat("The quick brown fox jumps over the lazy dog. ", 50),
		Source:   "/tmp/test.txt",
		Page:     1,
		Language: "eng",
		Type:     "text",
	}
	chunks := ChunkDocument(doc)
	if len(chunks) == 0 {
		t.Fatal("ChunkDocument returned 0 chunks")
	}

	parents := 0
	children := 0
	for _, c := range chunks {
		switch c.ChunkType {
		case "parent":
			parents++
			if c.ParentID != "" {
				t.Errorf("parent chunk should have empty ParentID, got %q", c.ParentID)
			}
		case "child":
			children++
			if c.ParentID == "" {
				t.Errorf("child chunk should have non-empty ParentID")
			}
		default:
			t.Errorf("unknown ChunkType: %q", c.ChunkType)
		}
	}
	t.Logf("Produced %d parent + %d child chunks", parents, children)

	if parents == 0 {
		t.Error("expected at least 1 parent chunk")
	}
	if children == 0 {
		t.Error("expected at least 1 child chunk")
	}
}

func TestChunkDocument_EmptyText(t *testing.T) {
	doc := parsers.ParsedDoc{Text: "", Source: "/tmp/empty.txt"}
	chunks := ChunkDocument(doc)
	if len(chunks) != 0 {
		t.Errorf("ChunkDocument with empty text returned %d chunks; want 0", len(chunks))
	}
}

func TestChunkDocument_ShortText(t *testing.T) {
	doc := parsers.ParsedDoc{
		Text:   "Short document.",
		Source: "/tmp/short.txt",
		Type:   "text",
	}
	chunks := ChunkDocument(doc)
	if len(chunks) == 0 {
		t.Error("expected chunks for short but non-empty text")
	}
}
