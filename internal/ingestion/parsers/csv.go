package parsers

import (
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"strings"
)

type CSVParser struct{}

func (p *CSVParser) Parse(path string) ([]ParsedDoc, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open csv %s: %w", path, err)
	}
	defer f.Close()

	r := csv.NewReader(f)
	r.LazyQuotes = true

	var rows [][]string
	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue // skip malformed rows
		}
		rows = append(rows, row)
	}
	if len(rows) == 0 {
		return nil, nil
	}

	text := rowsToMarkdown(rows)
	return []ParsedDoc{{
		Text:     text,
		Source:   path,
		Page:     1,
		Type:     "csv",
		Language: "eng",
	}}, nil
}

func rowsToMarkdown(rows [][]string) string {
	if len(rows) == 0 {
		return ""
	}
	var sb strings.Builder
	header := rows[0]
	sb.WriteString("| " + strings.Join(header, " | ") + " |\n")
	sb.WriteString("|" + strings.Repeat("---|", len(header)) + "\n")
	for _, row := range rows[1:] {
		sb.WriteString("| " + strings.Join(row, " | ") + " |\n")
	}
	return sb.String()
}
