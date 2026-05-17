package ocr

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	"docmind/internal/config"
)

var httpClient = &http.Client{Timeout: 30 * time.Second}

type ocrRequest struct {
	ImageB64 string `json:"image_b64"`
	Lang     string `json:"lang"`
}

type ocrResponse struct {
	Text     string `json:"text"`
	Language string `json:"language"`
}

type langRequest struct {
	Text string `json:"text"`
}

type langResponse struct {
	Language string `json:"language"`
}

// OCRImage sends a PNG/JPEG file to the OCR microservice and returns extracted text and language.
func OCRImage(imagePath string, lang string) (text, language string, err error) {
	data, err := os.ReadFile(imagePath)
	if err != nil {
		return "", "", fmt.Errorf("read image: %w", err)
	}
	return OCRBytes(data, lang)
}

// OCRBytes sends raw image bytes to the OCR microservice.
func OCRBytes(imageBytes []byte, lang string) (text, language string, err error) {
	if lang == "" {
		lang = "sin+tam+eng"
	}
	req := ocrRequest{
		ImageB64: base64.StdEncoding.EncodeToString(imageBytes),
		Lang:     lang,
	}
	body, err := json.Marshal(req)
	if err != nil {
		return "", "", err
	}
	resp, err := httpClient.Post(config.OCRServiceURL+"/ocr/image", "application/json", bytes.NewReader(body))
	if err != nil {
		return "", "", fmt.Errorf("OCR service unavailable: %w", err)
	}
	defer resp.Body.Close()

	var result ocrResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", "", err
	}
	return result.Text, result.Language, nil
}

// DetectLanguage calls the OCR service to detect language from a text sample.
func DetectLanguage(text string) (string, error) {
	req := langRequest{Text: text}
	body, err := json.Marshal(req)
	if err != nil {
		return "sin+tam+eng", err
	}
	resp, err := httpClient.Post(config.OCRServiceURL+"/ocr/detect-lang", "application/json", bytes.NewReader(body))
	if err != nil {
		return "sin+tam+eng", err
	}
	defer resp.Body.Close()

	var result langResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "sin+tam+eng", err
	}
	return result.Language, nil
}