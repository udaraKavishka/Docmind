import sys
import threading
import streamlit as st
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.graph import run_agent
from ingestion.watcher import start_watcher
from ingestion.dispatcher import ingest
from retrieval.bm25_store import rebuild_bm25
from config import PRIMARY_LLM, FALLBACK_LLM, WATCHED_DIR, CHROMA_DIR

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='DocMind — Local RAG',
    page_icon='🧠',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Start watcher thread once ───────────────────────────────────────────────
if 'watcher_started' not in st.session_state:
    st.session_state.watcher_started = False
if not st.session_state.watcher_started:
    threading.Thread(
        target=start_watcher, args=(ingest,),
        daemon=True, name='FileWatcher'
    ).start()
    st.session_state.watcher_started = True

# ── Session state defaults ──────────────────────────────────────────────────
for k, v in {
    'messages': [], 'model': PRIMARY_LLM,
    'language': 'all', 'debug_mode': False
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('## 🧠 DocMind')
    st.caption('Local · Private · Multilingual')
    st.divider()

    st.markdown('**LLM Model**')
    st.session_state.model = st.selectbox(
        'model', [PRIMARY_LLM, FALLBACK_LLM], label_visibility='collapsed'
    )

    st.markdown('**Language Filter**')
    _LANGS = {'All Languages': 'all', 'English': 'eng', 'Sinhala': 'sin', 'Tamil': 'tam'}
    _lang_label = st.selectbox('lang', list(_LANGS.keys()), label_visibility='collapsed')
    st.session_state.language = _LANGS[_lang_label]

    st.divider()
    st.session_state.debug_mode = st.toggle('🔍 Debug mode', st.session_state.debug_mode)
    st.divider()

    st.markdown('**Knowledge Base**')
    try:
        import chromadb; from chromadb.config import Settings
        _c = chromadb.PersistentClient(str(CHROMA_DIR), Settings(anonymized_telemetry=False))
        st.metric('Indexed chunks', f'{_c.get_collection("rag_chunks").count():,}')
    except Exception:
        st.metric('Indexed chunks', '—')

    st.metric('Watched files', len(list(WATCHED_DIR.rglob('*'))) if WATCHED_DIR.exists() else 0)
    st.divider()

    if st.button('♻️ Re-index all', use_container_width=True):
        with st.spinner('Re-indexing...'):
            for f in WATCHED_DIR.rglob('*') if WATCHED_DIR.exists() else []:
                if f.is_file():
                    try: ingest(f, 'CREATE')
                    except Exception: pass
            rebuild_bm25()
        st.success('Done!'); st.rerun()

    if st.button('🗑️ Clear chat', use_container_width=True):
        st.session_state.messages = []; st.rerun()


# ── Source display function ──────────────────────────────────────────────────
def display_sources(chunks, meta):
    if not chunks: return
    with st.expander(f'📎 {len(chunks)} sources retrieved'):
        sub_qs = meta.get('sub_questions', [])
        if len(sub_qs) > 1:
            st.markdown('**Planner sub-questions:** ' + ' · '.join(f'*{q}*' for q in sub_qs))
        c1, c2, c3 = st.columns(3)
        c1.metric('Grounded', '✅' if meta.get('grounded') else '❌')
        c2.metric('Retries', meta.get('retry_count', 0))
        c3.metric('Chunks', len(chunks))
        if meta.get('critique'): st.caption(f'Critic: {meta["critique"]}')
        st.divider()
        for i, chunk in enumerate(chunks, 1):
            name  = Path(chunk.get('source', '?')).name
            rs    = chunk.get('rerank_score', 0)
            rrf   = chunk.get('rrf_score', 0)
            lang  = chunk.get('meta', {}).get('language', '?')
            icon  = '🟢' if rs > 0.7 else '🟡' if rs > 0.4 else '🔴'
            st.markdown(f'{icon} **[{i}] {name}** `rerank={rs:.3f}` `rrf={rrf:.5f}` `{lang}`')
            if st.session_state.debug_mode:
                st.text_area('', chunk.get('text',''), height=130,
                             key=f'c{i}{hash(chunk.get("chunk_id",""))}', disabled=True)
            else:
                st.caption((chunk.get('text','')[:200] + '...'))
            if i < len(chunks): st.markdown('---')


# ── Main chat ────────────────────────────────────────────────────────────────
st.title('🧠 DocMind')
st.caption(f'`{st.session_state.model}` · `{_lang_label}` · debug: `{"on" if st.session_state.debug_mode else "off"}`')

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        if msg['role'] == 'assistant' and msg.get('chunks'):
            display_sources(msg['chunks'], msg.get('meta', {}))

if prompt := st.chat_input('Ask anything about your documents...'):
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    with st.chat_message('user'): st.markdown(prompt)

    with st.chat_message('assistant'):
        with st.status('Thinking...', expanded=True) as status:
            st.write('🔍 Planning query...')
            result = run_agent(prompt, language=st.session_state.language)
            st.write(f'📦 {len(result["retrieved_chunks"])} chunks retrieved')
            if result.get('retry_count', 0) > 0:
                st.write(f'🔄 {result["retry_count"]} retrieval retries')
            status.update(label='✅ Done', state='complete', expanded=False)
        st.markdown(result['answer'])
        display_sources(result['retrieved_chunks'], result)

    st.session_state.messages.append({
        'role': 'assistant', 'content': result['answer'],
        'chunks': result['retrieved_chunks'], 'meta': result,
    })