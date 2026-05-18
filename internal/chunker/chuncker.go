package chunker

import (
	"docmind/internal/config"
	"docmind/internal/ingestion/parsers"

	"github.com/google/uuid"
)

// Chunk is the central data model shared by all downstream layers.
type Chunk struct {
	ChunkID   string
	ParentID  string // empty string for parent chunks
	Text      string
	Source    string
	Page      int
	Language  string
	ChunkType string // "parent" or "child"
	DocType   string
}

// makeChunks greedily packs sentences into chunks up to maxTokens.
// Maintains an overlap window to preserve cross-boundary context.
func makeChunks(text string, maxTokens int) []string {
	sentences := splitSentences(text)
	var chunks []string
	var current []string
	currentTokens := 0

	for _, sent := range sentences {
		sentTokens := countTokens(sent)
		if currentTokens+sentTokens > maxTokens && len(current) > 0 {
			chunks = append(chunks, joinSentences(current))
			current, currentTokens = buildOverlap(current)
		}
		current = append(current, sent)
		currentTokens += sentTokens
	}
	if len(current) > 0 {
		chunks = append(chunks, joinSentences(current))
	}
	return chunks
}

// buildOverlap keeps the last N tokens worth of sentences as the overlap window.
func buildOverlap(sentences []string) ([]string, int) {
	var overlap []string
	total := 0
	for i := len(sentences) - 1; i >= 0; i-- {
		t := countTokens(sentences[i])
		if total+t > config.ChunkOverlap {
			break
		}
		overlap = append([]string{sentences[i]}, overlap...)
		total += t
	}
	return overlap, total
}

func joinSentences(sentences []string) string {
	result := ""
	for i, s := range sentences {
		if i > 0 {
			result += " "
		}
		result += s
	}
	return result
}

// ChunkDocument creates parent + child chunks from a single ParsedDoc.
func ChunkDocument(doc parsers.ParsedDoc) []Chunk {
	var all []Chunk
	parents := makeChunks(doc.Text, config.ParentChunkSize)

	for _, parentText := range parents {
		parentID := uuid.New().String()
		all = append(all, Chunk{
			ChunkID:   parentID,
			ParentID:  "",
			Text:      parentText,
			Source:    doc.Source,
			Page:      doc.Page,
			Language:  doc.Language,
			ChunkType: "parent",
			DocType:   doc.Type,
		})

		children := makeChunks(parentText, config.ChildChunkSize)
		for _, childText := range children {
			all = append(all, Chunk{
				ChunkID:   uuid.New().String(),
				ParentID:  parentID,
				Text:      childText,
				Source:    doc.Source,
				Page:      doc.Page,
				Language:  doc.Language,
				ChunkType: "child",
				DocType:   doc.Type,
			})
		}
	}
	return all
}