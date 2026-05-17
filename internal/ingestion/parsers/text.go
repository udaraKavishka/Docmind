package parsers

import (
	"fmt"
	"os"
	"strings"

	"docmind/internal/ocr"
)

type TextParser struct{}

func (p *TextParser) Parse(path string) ([]ParsedDoc, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read text %s: %w", path, err)
	}
	text := strings.TrimSpace(string(data))
	if text == "" {
		return nil, nil
	}
	lang, _ := ocr.DetectLanguage(text[:min(300, len(text))])
	return []ParsedDoc{{
		Text:     text,
		Source:   path,
		Page:     1,
		Type:     "text",
		Language: lang,
	}}, nil
}
