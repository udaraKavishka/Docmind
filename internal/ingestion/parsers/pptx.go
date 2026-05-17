package parsers

import (
	"archive/zip"
	"encoding/xml"
	"fmt"
	"io"
	"regexp"
	"sort"
	"strings"

	"docmind/internal/ocr"
)

type PPTXParser struct{}

// slideXML is a minimal struct for extracting text from a PowerPoint slide XML.
type slideXML struct {
	XMLName xml.Name `xml:"sld"`
	Texts   []string
}

// pptxTextNode extracts all <a:t> (text run) elements from slide XML.
type pptxDoc struct {
	TextRuns []struct {
		Text string `xml:",chardata"`
	} `xml:"body>sp>txBody>p>r>t"`
}

var slidePattern = regexp.MustCompile(`^ppt/slides/slide(\d+)\.xml$`)
var notesPattern = regexp.MustCompile(`^ppt/notesSlides/notesSlide(\d+)\.xml$`)

func (p *PPTXParser) Parse(path string) ([]ParsedDoc, error) {
	r, err := zip.OpenReader(path)
	if err != nil {
		return nil, fmt.Errorf("open pptx %s: %w", path, err)
	}
	defer r.Close()

	slideTexts := map[int]string{}
	notesTexts := map[int]string{}

	for _, f := range r.File {
		if m := slidePattern.FindStringSubmatch(f.Name); m != nil {
			text, err := extractPPTXText(f)
			if err != nil {
				continue
			}
			var num int
			fmt.Sscanf(m[1], "%d", &num)
			slideTexts[num] = text
		}
		if m := notesPattern.FindStringSubmatch(f.Name); m != nil {
			text, err := extractPPTXText(f)
			if err != nil {
				continue
			}
			var num int
			fmt.Sscanf(m[1], "%d", &num)
			notesTexts[num] = text
		}
	}

	// Sort slide numbers for deterministic output.
	slideNums := make([]int, 0, len(slideTexts))
	for n := range slideTexts {
		slideNums = append(slideNums, n)
	}
	sort.Ints(slideNums)

	var docs []ParsedDoc
	for _, num := range slideNums {
		parts := []string{slideTexts[num]}
		if notes, ok := notesTexts[num]; ok && strings.TrimSpace(notes) != "" {
			parts = append(parts, "[Speaker notes]: "+notes)
		}
		text := strings.TrimSpace(strings.Join(parts, "\n"))
		if text == "" {
			continue
		}
		lang, _ := ocr.DetectLanguage(text[:min(300, len(text))])
		docs = append(docs, ParsedDoc{
			Text:     text,
			Source:   path,
			Page:     num,
			Type:     "pptx",
			Language: lang,
		})
	}
	return docs, nil
}

func extractPPTXText(f *zip.File) (string, error) {
	rc, err := f.Open()
	if err != nil {
		return "", err
	}
	defer rc.Close()

	data, err := io.ReadAll(rc)
	if err != nil {
		return "", err
	}

	// Extract all <a:t> text runs from the XML.
	// We use a simple token-based approach to avoid registering namespaces.
	decoder := xml.NewDecoder(strings.NewReader(string(data)))
	var texts []string
	capture := false

	for {
		tok, err := decoder.Token()
		if err != nil {
			break
		}
		switch t := tok.(type) {
		case xml.StartElement:
			if t.Name.Local == "t" {
				capture = true
			}
		case xml.CharData:
			if capture {
				texts = append(texts, string(t))
			}
		case xml.EndElement:
			capture = false
		}
	}
	return strings.TrimSpace(strings.Join(texts, " ")), nil
}
