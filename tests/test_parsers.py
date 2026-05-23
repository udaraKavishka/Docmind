"""Tests for ingestion/parsers/* — each parser module."""
import csv
import tempfile
from pathlib import Path

import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _patch_detect_lang(monkeypatch):
    """Prevent real HTTP calls to the OCR service during tests."""
    import ingestion.ocr as ocr_mod
    monkeypatch.setattr(ocr_mod, 'detect_language', lambda text: 'eng')


# ── Text parser ───────────────────────────────────────────────────────────────

class TestTextParser:
    def test_basic_text(self, monkeypatch, tmp_path):
        _patch_detect_lang(monkeypatch)
        from ingestion.parsers.text_parser import parse

        f = tmp_path / 'sample.txt'
        f.write_text('Hello world. DocMind is great.')
        docs = parse(f)

        assert len(docs) == 1
        assert 'DocMind' in docs[0]['text']
        assert docs[0]['doc_type'] == 'text'
        assert docs[0]['source'] == str(f)

    def test_empty_file_returns_empty(self, monkeypatch, tmp_path):
        _patch_detect_lang(monkeypatch)
        from ingestion.parsers.text_parser import parse

        f = tmp_path / 'empty.txt'
        f.write_text('')
        assert parse(f) == []

    def test_markdown_file(self, monkeypatch, tmp_path):
        _patch_detect_lang(monkeypatch)
        from ingestion.parsers.text_parser import parse

        f = tmp_path / 'readme.md'
        f.write_text('# Title\n\nSome content here.')
        docs = parse(f)
        assert len(docs) == 1
        assert 'Title' in docs[0]['text']


# ── CSV parser ────────────────────────────────────────────────────────────────

class TestCSVParser:
    def _make_csv(self, tmp_path, rows):
        f = tmp_path / 'data.csv'
        with open(f, 'w', newline='') as fp:
            csv.writer(fp).writerows(rows)
        return f

    def test_basic_csv(self, tmp_path):
        from ingestion.parsers.csv_parser import parse

        f = self._make_csv(tmp_path, [
            ['Name', 'Score'],
            ['Alice', '95'],
            ['Bob', '72'],
        ])
        docs = parse(f)
        assert len(docs) == 1
        text = docs[0]['text']
        assert 'Name' in text
        assert 'Alice' in text
        assert '|' in text  # markdown table

    def test_empty_csv_returns_empty(self, tmp_path):
        from ingestion.parsers.csv_parser import parse

        f = tmp_path / 'empty.csv'
        f.write_text('')
        assert parse(f) == []

    def test_csv_doc_type(self, tmp_path):
        from ingestion.parsers.csv_parser import parse

        f = self._make_csv(tmp_path, [['H1', 'H2'], ['v1', 'v2']])
        docs = parse(f)
        assert docs[0]['doc_type'] == 'csv'

    def test_csv_markdown_table_has_separator(self, tmp_path):
        from ingestion.parsers.csv_parser import parse

        f = self._make_csv(tmp_path, [['A', 'B'], ['1', '2']])
        text = parse(f)[0]['text']
        lines = text.splitlines()
        assert '---' in lines[1]  # second line is separator row


# ── Fusion ────────────────────────────────────────────────────────────────────

class TestRRFFusion:
    def test_basic_fusion(self):
        from retrieval.fusion import reciprocal_rank_fusion

        # 'a' is rank-1 in list1 and rank-2 in list2
        # 'b' is rank-2 in list1 and rank-1 in list2  → identical scores by symmetry
        # 'd' appears in only one list → lowest score
        lists = [['a', 'b', 'c'], ['b', 'a', 'd']]
        result = reciprocal_rank_fusion(lists)
        ids    = [r[0] for r in result]
        scores = [r[1] for r in result]

        # 'a' and 'b' must both outscore 'c' and 'd'
        a_score = next(s for i, s in result if i == 'a')
        b_score = next(s for i, s in result if i == 'b')
        d_score = next(s for i, s in result if i == 'd')
        assert a_score > d_score
        assert b_score > d_score
        # Scores must be non-ascending
        assert scores == sorted(scores, reverse=True)

    def test_single_list(self):
        from retrieval.fusion import reciprocal_rank_fusion

        result = reciprocal_rank_fusion([['x', 'y', 'z']])
        ids = [r[0] for r in result]
        assert ids == ['x', 'y', 'z']

    def test_empty_lists(self):
        from retrieval.fusion import reciprocal_rank_fusion

        assert reciprocal_rank_fusion([]) == []
        assert reciprocal_rank_fusion([[]]) == []

    def test_all_scores_positive(self):
        from retrieval.fusion import reciprocal_rank_fusion

        result = reciprocal_rank_fusion([['a', 'b'], ['c']])
        for _, score in result:
            assert score > 0


# ── BM25 tokenizer ────────────────────────────────────────────────────────────

class TestBM25Tokenizer:
    def test_lowercase(self):
        from retrieval.bm25_store import _tokenize

        tokens = _tokenize('Hello WORLD')
        assert tokens == ['hello', 'world']

    def test_splits_on_whitespace(self):
        from retrieval.bm25_store import _tokenize

        tokens = _tokenize('a b c')
        assert tokens == ['a', 'b', 'c']

    def test_empty_string(self):
        from retrieval.bm25_store import _tokenize

        assert _tokenize('') == []
