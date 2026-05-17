package parsers

import "fmt"

// ParsedDoc is the uniform output of every parser.
type ParsedDoc struct {
	Text     string
	Source   string
	Page     int
	Type     string // "digital_pdf" | "scanned_pdf" | "pptx" | "docx" | "image" | "csv" | "text"
	Language string // "sin" | "tam" | "eng" | "sin+tam+eng"
}

// Parser is implemented by every format-specific parser.
type Parser interface {
	Parse(path string) ([]ParsedDoc, error)
}

var registry = map[string]Parser{}

func init() {
	registry["pdf"]   = &PDFParser{}
	registry["pptx"]  = &PPTXParser{}
	registry["docx"]  = &DOCXParser{}
	registry["image"] = &ImageParser{}
	registry["csv"]   = &CSVParser{}
	registry["text"]  = &TextParser{}
}

// Get returns the parser for the given key.
func Get(key string) (Parser, error) {
	p, ok := registry[key]
	if !ok {
		return nil, fmt.Errorf("no parser for: %s", key)
	}
	return p, nil
}
