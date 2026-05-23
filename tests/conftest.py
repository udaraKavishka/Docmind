"""Pytest configuration — adds the project root to sys.path."""
import sys
from pathlib import Path

# Project root must be on sys.path so all packages resolve correctly
sys.path.insert(0, str(Path(__file__).parent.parent))
