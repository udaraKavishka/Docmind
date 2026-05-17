package parsers

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"docmind/internal/config"
	"docmind/internal/ocr"

	"github.com/dslipak/pdf"
)

type PDFParser struct{}

func (p *PDFParser) Parse(path string) ([]ParsedDoc, error) {
	r, err := pdf.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open pdf %s: %w", filepath.Base(path), err)
	}

	var docs []ParsedDoc
	numPages := r.NumPage()

	for pageNum := 1; pageNum <= numPages; pageNum++ {
		pg := r.Page(pageNum)
		if pg.V.IsNull() {
			continue
		}

		text := strings.TrimSpace(pg.Content().Text())

		if len(text) >= config.MinTextChars {
			lang, _ := ocr.DetectLanguage(text[:min(500, len(text))])
			docs = append(docs, ParsedDoc{
				Text:     text,
				Source:   path,
				Page:     pageNum,
				Type:     "digital_pdf",
				Language: lang,
			})
			continue
		}

		// Scanned page — render to PNG via pdftoppm, then OCR.
		log.Printf("[PDF] scanned page %d in %s — applying OCR", pageNum, filepath.Base(path))
		ocrText, lang, err := renderAndOCR(path, pageNum)
		if err != nil {
			log.Printf("[PDF] OCR failed page %d: %v", pageNum, err)
			continue
		}
		if ocrText == "" {
			continue
		}
		docs = append(docs, ParsedDoc{
			Text:     ocrText,
			Source:   path,
			Page:     pageNum,
			Type:     "scanned_pdf",
			Language: lang,
		})
	}
	return docs, nil
}

// renderAndOCR uses pdftoppm (from poppler-utils) to render one PDF page to PNG,
// then calls the OCR microservice.
func renderAndOCR(pdfPath string, pageNum int) (text, language string, err error) {
	tmpDir, err := os.MkdirTemp("", "docmind-pdf-*")
	if err != nil {
		return "", "", err
	}
	defer os.RemoveAll(tmpDir)

	prefix := filepath.Join(tmpDir, "page")
	cmd := exec.Command(
		"pdftoppm",
		"-r", "300",
		"-png",
		"-f", fmt.Sprintf("%d", pageNum),
		"-l", fmt.Sprintf("%d", pageNum),
		pdfPath,
		prefix,
	)
	if out, err := cmd.CombinedOutput(); err != nil {
		return "", "", fmt.Errorf("pdftoppm: %s: %w", string(out), err)
	}

	// pdftoppm names the output file with a page-number suffix.
	pngPath := fmt.Sprintf("%s-%d.png", prefix, pageNum)
	if _, err := os.Stat(pngPath); os.IsNotExist(err) {
		// Some versions zero-pad the page number.
		pngPath = fmt.Sprintf("%s-%06d.png", prefix, pageNum)
	}

	imgBytes, err := os.ReadFile(pngPath)
	if err != nil {
		return "", "", fmt.Errorf("read rendered page: %w", err)
	}
	return ocr.OCRBytes(imgBytes, "sin+tam+eng")
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}