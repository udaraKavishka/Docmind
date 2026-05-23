package watcher

import (
	"sync/atomic"
	"testing"
	"time"
)

// TestDebouncerFiresOnce verifies that rapid identical-path schedules collapse to one call.
func TestDebouncerFiresOnce(t *testing.T) {
	var count atomic.Int32

	// Use a supported extension so dispatch does not short-circuit on FileTypeMap lookup.
	const path = "/tmp/test.txt"

	d := newDebouncer(func(p, action string) {
		count.Add(1)
	})

	// Fire 5 rapid schedules on the same path — only the last should survive.
	for i := 0; i < 5; i++ {
		d.schedule(path, "CREATE")
		time.Sleep(5 * time.Millisecond)
	}

	// Wait well beyond the config debounce window (2000 ms default).
	// To keep the test fast we override via the config-less path: we rely on
	// the fact that the last schedule resets the timer and dispatch is async.
	// Wait 2200 ms so the debounce window definitely expires.
	time.Sleep(2200 * time.Millisecond)

	if count.Load() != 1 {
		t.Errorf("debouncer fired %d times; want exactly 1", count.Load())
	}
}

// TestDebouncerIndependentFiles verifies that two distinct paths each fire once.
func TestDebouncerIndependentFiles(t *testing.T) {
	var count atomic.Int32

	d := newDebouncer(func(p, action string) {
		count.Add(1)
	})

	d.schedule("/tmp/a.txt", "CREATE")
	d.schedule("/tmp/b.txt", "CREATE")

	time.Sleep(2200 * time.Millisecond)

	if count.Load() != 2 {
		t.Errorf("debouncer fired %d times for 2 distinct files; want 2", count.Load())
	}
}
