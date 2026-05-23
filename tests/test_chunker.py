"""Tests for ingestion/chunker.py — sentence splitting, token counting, and chunking."""
import pytest
from ingestion.chunker import (
    count_tokens,
    split_sentences,
    chunk_document,
)


# ── count_tokens ─────────────────────────────────────────────────────────────

def test_count_tokens_basic():
    assert count_tokens('hello world') > 0


def test_count_tokens_empty():
    assert count_tokens('') == 0


def test_count_tokens_longer_text_is_more():
    short = count_tokens('hi')
    long  = count_tokens('hi ' * 100)
    assert long > short


# ── split_sentences ───────────────────────────────────────────────────────────

def test_split_sentences_english():
    sents = split_sentences('Hello world. How are you? I am fine!')
    assert len(sents) == 3


def test_split_sentences_single():
    sents = split_sentences('No terminator here')
    assert len(sents) == 1
    assert sents[0] == 'No terminator here'


def test_split_sentences_empty():
    sents = split_sentences('')
    assert sents == []


def test_split_sentences_sinhala_terminator():
    # U+0964 is a shared Sinhala/Tamil terminator
    sents = split_sentences('ආයුබෝවන්। ඔබ කෙසේ ද?')
    assert len(sents) >= 2


def test_split_sentences_strips_whitespace():
    sents = split_sentences('  Hello.  World!  ')
    for s in sents:
        assert s == s.strip()


# ── chunk_document ────────────────────────────────────────────────────────────

_SAMPLE_DOC = {
    'text':     'Hello world. ' * 30,
    'source':   '/tmp/test.txt',
    'page':     0,
    'language': 'eng',
    'doc_type': 'text',
}


def test_chunk_document_returns_chunks():
    chunks = chunk_document(_SAMPLE_DOC)
    assert len(chunks) > 0


def test_chunk_document_has_parents_and_children():
    chunks = chunk_document(_SAMPLE_DOC)
    types = {c['chunk_type'] for c in chunks}
    assert 'parent' in types
    assert 'child' in types


def test_chunk_document_parent_has_no_parent_id():
    chunks = chunk_document(_SAMPLE_DOC)
    for c in chunks:
        if c['chunk_type'] == 'parent':
            assert c['parent_id'] == ''


def test_chunk_document_child_has_parent_id():
    chunks = chunk_document(_SAMPLE_DOC)
    for c in chunks:
        if c['chunk_type'] == 'child':
            assert c['parent_id'] != ''


def test_chunk_document_child_parent_id_matches_a_parent():
    chunks = chunk_document(_SAMPLE_DOC)
    parent_ids = {c['chunk_id'] for c in chunks if c['chunk_type'] == 'parent'}
    for c in chunks:
        if c['chunk_type'] == 'child':
            assert c['parent_id'] in parent_ids, (
                f'child parent_id {c["parent_id"]!r} not found in parent IDs'
            )


def test_chunk_document_preserves_source():
    chunks = chunk_document(_SAMPLE_DOC)
    for c in chunks:
        assert c['source'] == '/tmp/test.txt'


def test_chunk_document_empty_text():
    doc = dict(_SAMPLE_DOC, text='')
    assert chunk_document(doc) == []


def test_chunk_document_whitespace_only():
    doc = dict(_SAMPLE_DOC, text='   \n  \t  ')
    assert chunk_document(doc) == []


def test_chunk_document_short_text():
    doc = dict(_SAMPLE_DOC, text='Short.')
    chunks = chunk_document(doc)
    assert len(chunks) > 0


def test_chunk_document_long_text_produces_multiple_parents():
    long_text = ('This is sentence number one. ' * 200)
    doc = dict(_SAMPLE_DOC, text=long_text)
    chunks = chunk_document(doc)
    parents = [c for c in chunks if c['chunk_type'] == 'parent']
    assert len(parents) > 1, 'Long text should produce multiple parent chunks'
