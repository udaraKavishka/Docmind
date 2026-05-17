package parsers

import (
	"fmt"
	"os"

	"docmind/internal/ocr"
)

type ImageParser struct{}

func (p *ImageParser) Parse(path string) ([]ParsedDoc, error) {
	imgBytes, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read image %s: %w", path, err)
	}
	text, lang, err := ocr.OCRBytes(imgBytes, "sin+tam+eng")
	if err != nil {
		return nil, fmt.Errorf("ocr image %s: %w", path, err)
	}
	if text == "" {
		return nil, nil
	}
	return []ParsedDoc{{
		Text:     text,
		Source:   path,
		Page:     1,
		Type:     "image",
		Language: lang,
	}}, nil
}