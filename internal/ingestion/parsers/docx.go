package parsers

import (
	"archive/zip"
	"encoding/xml"
	"fmt"
	"log"
	"path/filepath"
	"strings"

	"docmind/internal/config"
	"docmind/internal/ocr"
)

type DOCXParser struct{}

func (p *DOCXParser) Parse(path string) ([]ParsedDoc, error) {
	r, err := zip.OpenReader(path)
	if err != nil {
		return nil, fmt.Errorf("open docx %s: %w", filepath.Base(path), err)
	}
	defer r.Close()

	var docFile *zip.File
	for _, f := range r.File {
		if f.Name == "word/document.xml" {
			docFile = f
			break
		}
	}
	if docFile == nil {
		return nil, fmt.Errorf("docx %s: word/document.xml not found", filepath.Base(path))
	}

	text, err := extractDOCXText(docFile)
	if err != nil {
		return nil, fmt.Errorf("parse docx %s: %w", filepath.Base(path), err)
	}

	text = strings.TrimSpace(text)
	if len(text) < config.MinTextChars {
		log.Printf("[DOCX] extracted text too short (%d chars) in %s", len(text), filepath.Base(path))
		return nil, nil
	}

	sample := text[:min(500, len(text))]
	lang, _ := ocr.DetectLanguage(sample)

	return []ParsedDoc{{
		Text:     text,
		Source:   path,
		Page:     1,
		Type:     "docx",
		Language: lang,
	}}, nil
}

// extractDOCXText walks word/document.xml tokens and reconstructs text
// with newlines at paragraph (<w:p>) boundaries.
func extractDOCXText(f *zip.File) (string, error) {
	rc, err := f.Open()
	if err != nil {
		return "", err
	}
	defer rc.Close()

	var (
		sb          strings.Builder
		inParagraph bool
		paraHasText bool
		captureNext bool
	)

	decoder := xml.NewDecoder(rc)
	for {
		tok, err := decoder.Token()
		if err != nil {
			break
		}

		switch t := tok.(type) {
		case xml.StartElement:
			switch t.Name.Local {
			case "p":
				inParagraph = true
				paraHasText = false
			case "t":
				captureNext = true
			}
		case xml.CharData:
			if captureNext {
				if s := string(t); s != "" {
					sb.WriteString(s)
					paraHasText = true
				}
			}
		case xml.EndElement:
			switch t.Name.Local {
			case "t":
				captureNext = false
			case "p":
				if inParagraph && paraHasText {
					sb.WriteRune('\n')
				}
				inParagraph = false
				paraHasText = false
			}
		}
	}

	return sb.String(), nil
}
