package vectorstore

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"docmind/internal/chunker"
	"docmind/internal/embedder"
)

const (
	// ChromaDB v2 API — tenant/database routing replaces the flat v1 namespace.
	chromaHost     = "http://localhost:8000"
	chromaTenant   = "default_tenant"
	chromaDatabase = "default_database"
	collectionName = "rag_chunks"
)

// chromaBase is the path prefix for all collection-level endpoints.
// e.g. chromaBase + "/collections"
var chromaBase = fmt.Sprintf(
	"%s/api/v2/tenants/%s/databases/%s",
	chromaHost, chromaTenant, chromaDatabase,
)

// collectionID caches the UUID assigned by ChromaDB to the rag_chunks collection.
// All data operations (upsert, get, delete, query, count) use this UUID — not the name.
var collectionID string

var client = &http.Client{Timeout: 30 * time.Second}

func init() {
	ensureCollection()
}

func post(endpoint string, body any) (*http.Response, error) {
	data, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	return client.Post(chromaBase+endpoint, "application/json", bytes.NewReader(data))
}

// collPath returns the path to a specific endpoint on the cached collection UUID.
// e.g. collPath("/upsert") → "/collections/<uuid>/upsert"
func collPath(op string) string {
	return "/collections/" + collectionID + op
}

func ensureCollection() {
	payload := map[string]any{
		"name":           collectionName,
		"get_or_create":  true,
		"metadata":       map[string]string{"hnsw:space": "cosine"},
	}
	resp, err := post("/collections", payload)
	if err != nil {
		log.Printf("[CHROMA] could not create collection: %v", err)
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var result struct {
		ID string `json:"id"`
	}
	if err := json.Unmarshal(body, &result); err != nil || result.ID == "" {
		log.Printf("[CHROMA] could not parse collection ID (status %d): %s", resp.StatusCode, body)
		return
	}
	collectionID = result.ID
	log.Printf("[CHROMA] collection ready: %s (id=%s)", collectionName, collectionID)
}

type upsertPayload struct {
	IDs        []string            `json:"ids"`
	Embeddings [][]float32         `json:"embeddings,omitempty"`
	Documents  []string            `json:"documents"`
	Metadatas  []map[string]any    `json:"metadatas"`
}

// UpsertChunks embeds child chunks and stores all chunks in ChromaDB.
func UpsertChunks(chunks []chunker.Chunk) error {
	var children, parents []chunker.Chunk
	for _, c := range chunks {
		if c.ChunkType == "child" {
			children = append(children, c)
		} else {
			parents = append(parents, c)
		}
	}

	if err := upsertRaw(parents, false); err != nil {
		return fmt.Errorf("upsert parents: %w", err)
	}
	if err := upsertRaw(children, true); err != nil {
		return fmt.Errorf("upsert children: %w", err)
	}

	log.Printf("[CHROMA] upserted %d child + %d parent chunks", len(children), len(parents))
	return nil
}

func upsertRaw(chunks []chunker.Chunk, withEmbeddings bool) error {
	if len(chunks) == 0 {
		return nil
	}

	ids := make([]string, len(chunks))
	docs := make([]string, len(chunks))
	metas := make([]map[string]any, len(chunks))

	for i, c := range chunks {
		id := c.ChunkID
		if c.ChunkType == "parent" {
			id = "parent_" + c.ChunkID
		}
		ids[i] = id
		docs[i] = c.Text
		metas[i] = map[string]any{
			"source":    c.Source,
			"page":      c.Page,
			"language":  c.Language,
			"type":      c.ChunkType,
			"doc_type":  c.DocType,
			"parent_id": c.ParentID,
		}
	}

	payload := upsertPayload{IDs: ids, Documents: docs, Metadatas: metas}

	if withEmbeddings {
		texts := make([]string, len(chunks))
		for i, c := range chunks {
			texts[i] = c.Text
		}
		embs, err := embedder.EmbedBatch(texts)
		if err != nil {
			return err
		}
		payload.Embeddings = embs
	}

	resp, err := post(collPath("/upsert"), payload)
	if err != nil {
		return err
	}
	resp.Body.Close()
	return nil
}

// DeleteBySource removes all chunks for a source file.
func DeleteBySource(sourcePath string) error {
	// First get all IDs for this source.
	getPayload := map[string]any{
		"where": map[string]string{"source": sourcePath},
	}
	data, _ := json.Marshal(getPayload)
	resp, err := client.Post(chromaBase+collPath("/get"), "application/json", bytes.NewReader(data))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	var getResult struct {
		IDs []string `json:"ids"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&getResult); err != nil {
		return err
	}
	if len(getResult.IDs) == 0 {
		return nil
	}

	deletePayload := map[string]any{"ids": getResult.IDs}
	delResp, err := post(collPath("/delete"), deletePayload)
	if err != nil {
		return err
	}
	delResp.Body.Close()

	log.Printf("[CHROMA] deleted %d chunks for %s", len(getResult.IDs), sourcePath)
	return nil
}

// GetChunkCount returns the total number of chunks in the collection.
func GetChunkCount() (int, error) {
	resp, err := client.Get(chromaBase + collPath("/count"))
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()

	var count int
	if err := json.NewDecoder(resp.Body).Decode(&count); err != nil {
		return 0, err
	}
	return count, nil
}

// QueryResult is returned by the vector similarity search.
type QueryResult struct {
	IDs       []string
	Documents []string
	Distances []float32
	Metadatas []map[string]any
}

// Query runs a vector similarity search against child chunks.
func Query(embedding []float32, nResults int, where map[string]any) ([]QueryResult, error) {
	payload := map[string]any{
		"query_embeddings": [][]float32{embedding},
		"n_results":        nResults,
		"include":          []string{"documents", "distances", "metadatas"},
	}
	if len(where) > 0 {
		payload["where"] = where
	}

	resp, err := post(collPath("/query"), payload)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var raw struct {
		IDs       [][]string            `json:"ids"`
		Documents [][]string            `json:"documents"`
		Distances [][]float32           `json:"distances"`
		Metadatas [][]map[string]any    `json:"metadatas"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return nil, err
	}
	if len(raw.IDs) == 0 {
		return nil, nil
	}

	var results []QueryResult
	for i := range raw.IDs[0] {
		results = append(results, QueryResult{
			IDs:       []string{raw.IDs[0][i]},
			Documents: []string{raw.Documents[0][i]},
			Distances: []float32{raw.Distances[0][i]},
			Metadatas: []map[string]any{raw.Metadatas[0][i]},
		})
	}
	return results, nil
}

// GetByIDs fetches specific chunks by their IDs.
func GetByIDs(ids []string) ([]QueryResult, error) {
	payload := map[string]any{
		"ids":     ids,
		"include": []string{"documents", "metadatas"},
	}
	resp, err := post(collPath("/get"), payload)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var raw struct {
		IDs       []string            `json:"ids"`
		Documents []string            `json:"documents"`
		Metadatas []map[string]any    `json:"metadatas"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return nil, err
	}

	var results []QueryResult
	for i := range raw.IDs {
		results = append(results, QueryResult{
			IDs:       []string{raw.IDs[i]},
			Documents: []string{raw.Documents[i]},
			Metadatas: []map[string]any{raw.Metadatas[i]},
		})
	}
	return results, nil
}