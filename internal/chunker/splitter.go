package chunker

import (
	"strings"
	"unicode"
)

// sentenceTerminators covers English (. ! ?), Sinhala (। ෴ U+0964 U+0DF4), and Tamil (। U+0964).
func isSentenceEnd(r rune) bool {
	return r == '.' || r == '!' || r == '?' || r == '।' || r == '෴'
}

// splitSentences splits text on sentence boundaries for English, Sinhala, and Tamil.
func splitSentences(text string) []string {
	runes := []rune(text)
	var sentences []string
	start := 0

	for i := 0; i < len(runes); i++ {
		if !isSentenceEnd(runes[i]) {
			continue
		}
		// Include trailing whitespace in the boundary check.
		end := i + 1
		for end < len(runes) && unicode.IsSpace(runes[end]) {
			end++
		}
		if end > i+1 { // there was whitespace after the terminator
			sentence := strings.TrimSpace(string(runes[start : i+1]))
			if sentence != "" {
				sentences = append(sentences, sentence)
			}
			start = end
			i = end - 1
		}
	}

	if tail := strings.TrimSpace(string(runes[start:])); tail != "" {
		sentences = append(sentences, tail)
	}
	return sentences
}
