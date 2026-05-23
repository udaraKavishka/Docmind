package config

import (
	"os"
	"testing"
)

func TestWatchedDirExists(t *testing.T) {
	if _, err := os.Stat(WatchedDir); os.IsNotExist(err) {
		t.Errorf("WatchedDir %q was not created by init()", WatchedDir)
	}
}

func TestLogDirExists(t *testing.T) {
	if _, err := os.Stat(LogDir); os.IsNotExist(err) {
		t.Errorf("LogDir %q was not created by init()", LogDir)
	}
}

func TestFileTypeMapNotEmpty(t *testing.T) {
	if len(FileTypeMap) == 0 {
		t.Error("FileTypeMap is empty")
	}
}

func TestFileTypeMapExpectedExtensions(t *testing.T) {
	required := []string{".pdf", ".docx", ".pptx", ".txt", ".png", ".jpg", ".csv"}
	for _, ext := range required {
		if _, ok := FileTypeMap[ext]; !ok {
			t.Errorf("FileTypeMap missing required extension: %q", ext)
		}
	}
}

func TestModelConstants(t *testing.T) {
	if PrimaryLLM == "" {
		t.Error("PrimaryLLM is empty")
	}
	if FallbackLLM == "" {
		t.Error("FallbackLLM is empty")
	}
	if EmbedModel == "" {
		t.Error("EmbedModel is empty")
	}
}

func TestChunkSizes(t *testing.T) {
	if ParentChunkSize <= 0 {
		t.Errorf("ParentChunkSize = %d; want > 0", ParentChunkSize)
	}
	if ChildChunkSize <= 0 {
		t.Errorf("ChildChunkSize = %d; want > 0", ChildChunkSize)
	}
	if ChildChunkSize >= ParentChunkSize {
		t.Errorf("ChildChunkSize (%d) must be < ParentChunkSize (%d)", ChildChunkSize, ParentChunkSize)
	}
}
