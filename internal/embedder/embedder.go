package embedder

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"docmind/internal/config"
)

var client = &http.Client{Timeout: 60 * time.Second}

type embedRequest struct {
	Model  string `json:"model"`
	Prompt string `json:"prompt"`
}

type embedResponse struct {
	Embedding []float32 `json:"embedding"`
}

// EmbedText embeds a single text string via Ollama.
func EmbedText(text string) ([]float32, error) {
	body, _ := json.Marshal(embedRequest{Model: config.EmbedModel, Prompt: text})
	resp, err := client.Post(config.OllamaBaseURL+"/api/embeddings", "application/json", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("ollama embed: %w", err)
	}
	defer resp.Body.Close()

	var result embedResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode embed response: %w", err)
	}
	return result.Embedding, nil
}

// EmbedBatch embeds texts in batches of config.EmbedBatch to prevent OOM.
func EmbedBatch(texts []string) ([][]float32, error) {
	total := len(texts)
	batchSize := config.EmbedBatch
	totalBatches := (total + batchSize - 1) / batchSize
	all := make([][]float32, 0, total)

	for i := 0; i < total; i += batchSize {
		end := i + batchSize
		if end > total {
			end = total
		}
		batch := texts[i:end]
		batchNum := i/batchSize + 1
		log.Printf("[EMBEDDER] batch %d/%d (%d texts)", batchNum, totalBatches, len(batch))

		for _, text := range batch {
			emb, err := EmbedText(text)
			if err != nil {
				return nil, err
			}
			all = append(all, emb)
		}
	}
	return all, nil
}