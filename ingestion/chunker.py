"""
Parent-child chunker with multilingual sentence splitting (Layer 3).
Matches the Go implementation in internal/chunker/.
"""
import re
import uuid
import logging
import tiktoken
from config import PARENT_CHUNK_SIZE, CHILD_CHUNK_SIZE, CHUNK_OVERLAP

log = logging.getLogger(__name__)

# ── Tokenizer (lazy singleton) ───────────────────────────────────────────────
_enc = None  # tiktoken.Encoding — lazy-loaded


def _get_enc():
    global _enc
    if _enc is None:
        _enc = tiktoken.get_encoding('cl100k_base')
    return _enc


def count_tokens(text: str) -> int:
    """Return the token count for *text* using cl100k_base."""
    return len(_get_enc().encode(text))


# ── Sentence splitter ────────────────────────────────────────────────────────
# Terminators: English  .!?
#              Sinhala  ። U+0964  ෴ U+0DF4
#              Tamil    ।  U+0964  (shared with Sinhala)
_TERM_RE = re.compile(r'(?<=[.!?।෴])\s+')


def split_sentences(text: str) -> list[str]:
    """Split *text* into sentences at Unicode-aware terminators."""
    parts = _TERM_RE.split(text)
    return [s.strip() for s in parts if s.strip()]


# ── Chunk builder ─────────────────────────────────────────────────────────────

def _make_chunks(sentences: list[str], max_tokens: int) -> list[str]:
    """
    Greedily pack sentences into chunks of at most *max_tokens* tokens.
    Maintains a CHUNK_OVERLAP-token overlap between consecutive chunks.
    """
    chunks: list[str] = []
    current: list[str] = []
    current_tok = 0

    for sentence in sentences:
        s_tok = count_tokens(sentence)
        if current_tok + s_tok > max_tokens and current:
            chunks.append(' '.join(current))
            # Build overlap: keep trailing sentences that fit in CHUNK_OVERLAP
            overlap: list[str] = []
            overlap_tok = 0
            for s in reversed(current):
                t = count_tokens(s)
                if overlap_tok + t <= CHUNK_OVERLAP:
                    overlap.insert(0, s)
                    overlap_tok += t
                else:
                    break
            current     = overlap
            current_tok = overlap_tok
        current.append(sentence)
        current_tok += s_tok

    if current:
        chunks.append(' '.join(current))

    return chunks


# ── Public API ────────────────────────────────────────────────────────────────

def chunk_document(doc: dict) -> list[dict]:
    """
    Convert a parsed document dict into parent + child chunk dicts.

    *doc* must have:
        text, source, page, language, doc_type

    Returns a list of chunk dicts with:
        chunk_id, parent_id, text, source, page, language, chunk_type, doc_type
    """
    text = (doc.get('text') or '').strip()
    if not text:
        return []

    sentences = split_sentences(text)
    if not sentences:
        return []

    parent_texts = _make_chunks(sentences, PARENT_CHUNK_SIZE)
    all_chunks: list[dict] = []

    for parent_text in parent_texts:
        parent_id = str(uuid.uuid4())
        all_chunks.append({
            'chunk_id':   parent_id,
            'parent_id':  '',
            'text':       parent_text,
            'source':     doc.get('source', ''),
            'page':       doc.get('page', 0),
            'language':   doc.get('language', ''),
            'chunk_type': 'parent',
            'doc_type':   doc.get('doc_type', ''),
        })

        # Child chunks from this parent
        child_sentences = split_sentences(parent_text)
        child_texts     = _make_chunks(child_sentences, CHILD_CHUNK_SIZE)
        for child_text in child_texts:
            all_chunks.append({
                'chunk_id':   str(uuid.uuid4()),
                'parent_id':  parent_id,
                'text':       child_text,
                'source':     doc.get('source', ''),
                'page':       doc.get('page', 0),
                'language':   doc.get('language', ''),
                'chunk_type': 'child',
                'doc_type':   doc.get('doc_type', ''),
            })

    log.debug(f'Chunked {doc.get("source","?")} p{doc.get("page",0)}: '
              f'{len(all_chunks)} chunks ({len(parent_texts)} parents)')
    return all_chunks
