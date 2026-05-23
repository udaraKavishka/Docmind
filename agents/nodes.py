from __future__ import annotations

import json
import logging
import requests
from config import OLLAMA_BASE_URL, PRIMARY_LLM, FALLBACK_LLM
from config import THINK_PREFIX, NO_THINK_PREFIX
from retrieval.retriever import retrieve
from retrieval.reranker  import rerank
from agents.state import AgentState

log      = logging.getLogger(__name__)
CHAT_URL = f'{OLLAMA_BASE_URL}/api/chat'
MAX_RETRIES = 3


# ── Shared LLM call ────────────────────────────────────────────────────────

def _chat(system: str, user: str, model: str = PRIMARY_LLM) -> str:
    """Single-shot non-streaming chat call to Ollama."""
    resp = requests.post(CHAT_URL, json={
        'model':    model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user',   'content': user},
        ],
        'stream': False,
    }, timeout=120)
    resp.raise_for_status()
    return resp.json()['message']['content']


def _safe_json(raw: str, fallback):
    """Parse JSON from LLM output, stripping markdown code fences if present."""
    cleaned = raw.strip()
    # Strip ```json ... ``` fences that LLMs sometimes add
    if cleaned.startswith('```'):
        cleaned = cleaned.split('```')[1]
        if cleaned.startswith('json'):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.warning(f'JSON parse failed: {e} — raw: {raw[:200]}')
        return fallback


# ── PLANNER NODE ────────────────────────────────────────────────────────────

PLANNER_SYSTEM = """You are a RAG query planner.
Decompose the user question into at most 3 focused sub-questions.
Each sub-question should target a distinct piece of information needed to answer the original question.
If the question is simple and atomic, return it unchanged as a single sub-question.
Output format: JSON array of strings. Example: ["What is X?", "How does Y affect X?"]
Never add sub-questions that are not needed. Fewer is better."""


def planner_node(state: AgentState) -> dict:
    """
    Decompose the user query into sub-questions.
    Uses gemma3:4b with /no_think for fast, structured JSON output.
    """
    query = state['query']

    # /no_think for fast, direct JSON output — no reasoning chain needed
    user_msg = f'{NO_THINK_PREFIX}{query}'

    try:
        raw      = _chat(PLANNER_SYSTEM, user_msg, model=FALLBACK_LLM)
        sub_qs   = _safe_json(raw, fallback=[query])
        if not isinstance(sub_qs, list) or not sub_qs:
            sub_qs = [query]
    except Exception as e:
        log.warning(f'Planner error: {e} — using original query')
        sub_qs = [query]

    log.info(f'Planner → {len(sub_qs)} sub-question(s): {sub_qs}')
    return {'sub_questions': sub_qs}


# ── RETRIEVER NODE ──────────────────────────────────────────────────────────

def retriever_node(state: AgentState) -> dict:
    """
    Run the full retrieval pipeline for each sub-question.
    Deduplicates by chunk_id across all sub-questions.
    """
    all_chunks = []
    seen_ids   = set()
    language   = state.get('language', 'all')
    retry      = state.get('retry_count', 0)

    for sub_q in state['sub_questions']:
        log.info(f'Retrieving for: "{sub_q}"')
        candidates = retrieve(sub_q, top_n=20, language=language)
        reranked   = rerank(sub_q, candidates, top_n=10)

        for chunk in reranked:
            cid = chunk['chunk_id']
            if cid not in seen_ids:
                all_chunks.append(chunk)
                seen_ids.add(cid)

    # Cap at 15 to keep LLM context manageable
    final_chunks = all_chunks[:15]
    log.info(
        f'Retriever → {len(final_chunks)} unique chunks '
        f'(retry {retry})'
    )
    return {'retrieved_chunks': final_chunks}


# ── GENERATOR NODE ──────────────────────────────────────────────────────────

GENERATOR_SYSTEM = """You are a precise, citation-focused AI assistant.
Answer questions ONLY from the provided context chunks.
Rules:
1. Cite every factual claim with [Source: filename, chunk N]
2. If the context does not contain the answer, say exactly: "I could not find this in the indexed documents."
3. Never hallucinate or use prior knowledge not present in the context.
4. Respond in the same language as the user question.
5. Keep answers concise — prefer bullet points for multi-part answers."""


def generator_node(state: AgentState) -> dict:
    """
    Synthesise a cited answer from retrieved chunks.
    Uses qwen3:8b with /think for deep reasoning on complex questions.
    """
    chunks = state['retrieved_chunks']

    if not chunks:
        return {'answer': 'I could not find this in the indexed documents.'}

    # Build the context block with clear source labels
    context_parts = []
    for i, c in enumerate(chunks, 1):
        source_name = c['source'].split('/')[-1] if c.get('source') else 'unknown'
        context_parts.append(
            f'[Source: {source_name}, chunk {i}]\n{c["text"]}'
        )
    context = '\n\n---\n\n'.join(context_parts)

    # /think enables qwen3's reasoning chain for better answer quality
    user_msg = (
        f'{THINK_PREFIX}'
        f'Context:\n{context}\n\n'
        f'Question: {state["query"]}'
    )

    try:
        answer = _chat(GENERATOR_SYSTEM, user_msg, model=PRIMARY_LLM)
    except Exception as e:
        log.error(f'Generator error: {e}')
        answer = 'I encountered an error generating the answer. Please try again.'

    log.info(f'Generator → answer ({len(answer)} chars)')
    return {'answer': answer}


# ── CRITIC NODE ─────────────────────────────────────────────────────────────

CRITIC_SYSTEM = """You are a factual grounding critic.
You will receive: (1) a user question, (2) retrieved context chunks, (3) a generated answer.
Your task: determine if every factual claim in the answer is supported by the context chunks.
Output ONLY valid JSON (no other text):
{
  "grounded": true or false,
  "reason": "brief explanation of your verdict",
  "missing": "what information is missing or hallucinated, if anything"
}
Be strict: if ANY factual claim in the answer is not traceable to a context chunk, set grounded to false."""


def critic_node(state: AgentState) -> dict:
    """
    Check whether the generated answer is grounded in the retrieved context.
    Uses gemma3:4b with /no_think for fast structured JSON output.
    If not grounded, the graph will loop back to retriever_node.
    """
    retry = state.get('retry_count', 0)

    # Hard cap — always accept after MAX_RETRIES
    if retry >= MAX_RETRIES:
        log.warning(f'Max retries ({MAX_RETRIES}) reached — accepting answer')
        return {
            'grounded':    True,
            'critique':    f'Accepted after {MAX_RETRIES} retries',
            'missing':     '',
            'retry_count': retry,
        }

    chunks = state['retrieved_chunks']
    context = '\n\n'.join(
        f'Chunk {i+1}: {c["text"][:300]}'
        for i, c in enumerate(chunks)
    )

    # /no_think for fast JSON verdict — no reasoning chain needed
    user_msg = (
        f'{NO_THINK_PREFIX}'
        f'Question: {state["query"]}\n\n'
        f'Context chunks:\n{context}\n\n'
        f'Generated answer:\n{state["answer"]}'
    )

    try:
        raw     = _chat(CRITIC_SYSTEM, user_msg, model=FALLBACK_LLM)
        verdict = _safe_json(raw, fallback={'grounded': True, 'reason': 'parse error', 'missing': ''})
        grounded = bool(verdict.get('grounded', True))
        critique = str(verdict.get('reason', ''))
        missing  = str(verdict.get('missing', ''))
    except Exception as e:
        log.warning(f'Critic error: {e} — assuming grounded')
        grounded, critique, missing = True, str(e), ''

    log.info(f'Critic → grounded={grounded} | {critique}')
    return {
        'grounded':    grounded,
        'critique':    critique,
        'missing':     missing,
        'retry_count': retry + 1,
    }
