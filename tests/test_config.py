"""Tests for config.py — paths, constants, and set_watched_dir()."""
import os
import tempfile
from pathlib import Path

import pytest
import config as _cfg


def test_primary_llm_not_empty():
    assert _cfg.PRIMARY_LLM, 'PRIMARY_LLM must not be empty'


def test_fallback_llm_not_empty():
    assert _cfg.FALLBACK_LLM, 'FALLBACK_LLM must not be empty'


def test_embed_model_not_empty():
    assert _cfg.EMBED_MODEL, 'EMBED_MODEL must not be empty'


def test_chunk_sizes_positive():
    assert _cfg.PARENT_CHUNK_SIZE > 0
    assert _cfg.CHILD_CHUNK_SIZE > 0


def test_child_smaller_than_parent():
    assert _cfg.CHILD_CHUNK_SIZE < _cfg.PARENT_CHUNK_SIZE, (
        'CHILD_CHUNK_SIZE must be less than PARENT_CHUNK_SIZE'
    )


def test_file_type_map_has_required_extensions():
    required = ['.pdf', '.docx', '.pptx', '.txt', '.png', '.jpg', '.csv']
    for ext in required:
        assert ext in _cfg.FILE_TYPE_MAP, f'FILE_TYPE_MAP missing {ext!r}'


def test_watched_dir_auto_created():
    assert _cfg.WATCHED_DIR.exists(), 'WATCHED_DIR should be auto-created by config.py'


def test_set_watched_dir_changes_global():
    original = _cfg.WATCHED_DIR
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = Path(tmpdir) / 'test_watch'
        returned = _cfg.set_watched_dir(new_dir)
        assert returned == new_dir.resolve()
        assert _cfg.WATCHED_DIR == new_dir.resolve()
        assert _cfg.WATCHED_DIR.exists()
    # Restore original
    _cfg.WATCHED_DIR = original


def test_set_watched_dir_creates_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = Path(tmpdir) / 'nested' / 'path'
        assert not new_dir.exists()
        _cfg.set_watched_dir(new_dir)
        assert new_dir.exists()
        # Restore
        _cfg.WATCHED_DIR = Path(tmpdir).parent


def test_env_override_watched_dir(monkeypatch, tmp_path):
    """DOCMIND_WATCHED_DIR env var should override the default path."""
    watch = tmp_path / 'custom_watch'
    watch.mkdir()
    monkeypatch.setenv('DOCMIND_WATCHED_DIR', str(watch))
    # Re-import config to pick up env var
    import importlib
    importlib.reload(_cfg)
    assert _cfg.WATCHED_DIR == watch
    # Reload again without the env var to restore
    monkeypatch.delenv('DOCMIND_WATCHED_DIR')
    importlib.reload(_cfg)
