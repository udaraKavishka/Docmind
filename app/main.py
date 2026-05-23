import sys
import threading
import streamlit as st
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.graph import run_agent
from ingestion.watcher import start_watcher
from ingestion.dispatcher import ingest
from retrieval.bm25_store import rebuild_bm25
import config as _cfg
from config import PRIMARY_LLM, FALLBACK_LLM, CHROMA_DIR

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='DocMind — Local RAG',
    page_icon='🧠',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Session state defaults ──────────────────────────────────────────────────
_defaults = {
    'messages':         [],
    'model':            PRIMARY_LLM,
    'language':         'all',
    'debug_mode':       False,
    'watched_dir':      str(_cfg.WATCHED_DIR),
    'watcher_started':  False,
    'watcher_dir':      str(_cfg.WATCHED_DIR),   # dir the current watcher watches
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _start_watcher_thread(watch_path: str | None) -> None:
    """Spawn a daemon watcher thread for *watch_path*."""
    if not watch_path:
        return
    import config as c
    c.WATCHED_DIR = Path(watch_path)
    c.WATCHED_DIR.mkdir(parents=True, exist_ok=True)
    threading.Thread(
        target=start_watcher, args=(ingest,),
        daemon=True, name='FileWatcher',
    ).start()


# ── Start (or restart) the watcher when the watched dir changes ─────────────
_desired_dir = st.session_state.watched_dir
if not st.session_state.watcher_started or st.session_state.watcher_dir != _desired_dir:
    _start_watcher_thread(_desired_dir)
    st.session_state.watcher_started = True
    st.session_state.watcher_dir     = _desired_dir

_WATCHED_DIR = Path(st.session_state.watched_dir)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('## 🧠 DocMind')
    st.caption('Local · Private · Multilingual')
    st.divider()

    # ── Watched directory (editable) ─────────────────────────────────────────
    st.markdown('**📂 Watched Directory**')
    _new_dir = st.text_input(
        'watched_dir',
        value=st.session_state.watched_dir,
        label_visibility='collapsed',
        help='Drop documents here. Change path to index a different folder.',
    )
    if _new_dir and _new_dir != st.session_state.watched_dir:
        _p = Path(str(_new_dir)).expanduser().resolve()
        if _p.exists() and _p.is_dir():
            st.session_state.watched_dir = str(_p)
            st.rerun()
        elif not _p.exists():
            if st.button('Create this folder'):
                _p.mkdir(parents=True, exist_ok=True)
                st.session_state.watched_dir = str(_p)
                st.rerun()
        else:
            st.warning('Path is not a directory.')

    st.divider()

    # ── Model selector ────────────────────────────────────────────────────────
    st.markdown('**LLM Model**')
    st.session_state.model = st.selectbox(
        'model', [PRIMARY_LLM, FALLBACK_LLM], label_visibility='collapsed'
    )

    # ── Language filter ───────────────────────────────────────────────────────
    st.markdown('**Language Filter**')
    _LANGS     = {'All Languages': 'all', 'English': 'eng', 'Sinhala': 'sin', 'Tamil': 'tam'}
    _lang_label = st.selectbox('lang', list(_LANGS.keys()), label_visibility='collapsed')
    st.session_state.language = _LANGS[_lang_label]

    st.divider()
    st.session_state.debug_mode = st.toggle('🔍 Debug mode', st.session_state.debug_mode)
    st.divider()

    # ── Knowledge base stats ──────────────────────────────────────────────────
    st.markdown('**Knowledge Base**')
    try:
        import chromadb
        from chromadb.config import Settings
        _c   = chromadb.PersistentClient(str(CHROMA_DIR), Settings(anonymized_telemetry=False))
        _col = _c.get_collection('rag_chunks')
        st.metric('Indexed chunks', f'{_col.count():,}')
    except Exception:
        st.metric('Indexed chunks', '—')

    _watched_files = len(list(_WATCHED_DIR.rglob('*'))) if _WATCHED_DIR.exists() else 0
    st.metric('Watched files', _watched_files)
    st.caption(f'`{_WATCHED_DIR}`')
    st.divider()

    # ── Actions ───────────────────────────────────────────────────────────────
    if st.button('♻️ Re-index all', use_container_width=True):
        with st.spinner('Re-indexing…'):
            for f in (_WATCHED_DIR.rglob('*') if _WATCHED_DIR.exists() else []):
                if f.is_file():
                    try:
                        ingest(f, 'CREATE')
                    except Exception:
                        pass
            rebuild_bm25()
        st.success('Done!')
        st.rerun()

    if st.button('🗑️ Clear chat', use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── Source display function ──────────────────────────────────────────────────
def display_sources(chunks: list, meta: dict) -> None:
    if not chunks:
        return
    with st.expander(f'📎 {len(chunks)} sources retrieved'):
        sub_qs = meta.get('sub_questions', [])
        if len(sub_qs) > 1:
            st.markdown('**Planner sub-questions:** ' + ' · '.join(f'*{q}*' for q in sub_qs))
        c1, c2, c3 = st.columns(3)
        c1.metric('Grounded', '✅' if meta.get('grounded') else '❌')
        c2.metric('Retries', meta.get('retry_count', 0))
        c3.metric('Chunks', len(chunks))
        if meta.get('critique'):
            st.caption(f'Critic: {meta["critique"]}')
        st.divider()
        for i, chunk in enumerate(chunks, 1):
            name = Path(chunk.get('source', '?')).name
            rs   = chunk.get('rerank_score', 0)
            rrf  = chunk.get('rrf_score', 0)
            lang = chunk.get('meta', {}).get('language', '?')
            icon = '🟢' if rs > 0.7 else '🟡' if rs > 0.4 else '🔴'
            st.markdown(f'{icon} **[{i}] {name}** `rerank={rs:.3f}` `rrf={rrf:.5f}` `{lang}`')
            if st.session_state.debug_mode:
                st.text_area(
                    '', chunk.get('text', ''), height=130,
                    key=f'c{i}{hash(chunk.get("chunk_id",""))}', disabled=True,
                )
            else:
                st.caption((chunk.get('text', '')[:200] + '…'))
            if i < len(chunks):
                st.markdown('---')


# ── Main chat ────────────────────────────────────────────────────────────────
st.title('🧠 DocMind')
st.caption(
    f'`{st.session_state.model}` · `{_lang_label}` · '
    f'debug: `{"on" if st.session_state.debug_mode else "off"}`'
)

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        if msg['role'] == 'assistant' and msg.get('chunks'):
            display_sources(msg['chunks'], msg.get('meta', {}))

if prompt := st.chat_input('Ask anything about your documents…'):
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.markdown(prompt)

    with st.chat_message('assistant'):
        with st.status('Thinking…', expanded=True) as status:
            st.write('🔍 Planning query…')
            result = run_agent(prompt, language=st.session_state.language)
            st.write(f'📦 {len(result["retrieved_chunks"])} chunks retrieved')
            if result.get('retry_count', 0) > 0:
                st.write(f'🔄 {result["retry_count"]} retrieval retries')
            status.update(label='✅ Done', state='complete', expanded=False)
        st.markdown(result['answer'])
        display_sources(result['retrieved_chunks'], result)

    st.session_state.messages.append({
        'role':   'assistant',
        'content': result['answer'],
        'chunks':  result['retrieved_chunks'],
        'meta':    result,
    })
