"""
MAF Hello World — Streamlit Chat UI (Semantic Kernel edition)

Run with:
    streamlit run streamlit_app.py
"""

import asyncio
import os
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SK Agent Skills Playground",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Hide default Streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* Sidebar gradient header */
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 14px;
        padding: 1.25rem 1rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .sidebar-header h2 { margin: 0; font-size: 1.1rem; font-weight: 700; }
    .sidebar-header p  { margin: 0.25rem 0 0; font-size: 0.75rem; opacity: 0.88; }

    /* Skill cards */
    .skill-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #eef0fb 100%);
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.6rem;
        border-left: 3px solid #667eea;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .skill-name { font-size: 0.82rem; font-weight: 600; color: #4a4a8a; margin-bottom: 0.2rem; }
    .skill-desc { font-size: 0.72rem; color: #666; line-height: 1.4; }
    .skill-badge {
        display: inline-block;
        background: #667eea1a;
        color: #667eea;
        border-radius: 99px;
        padding: 1px 8px;
        font-size: 0.67rem;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }

    /* Page title */
    .chat-title {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .chat-subtitle {
        color: #999;
        font-size: 0.88rem;
        margin-top: 0.1rem;
        margin-bottom: 1.2rem;
    }

    /* Suggestion chips */
    div[data-testid="column"] button {
        border-radius: 99px !important;
        font-size: 0.78rem !important;
        padding: 0.3rem 0.85rem !important;
        border: 1.5px solid #667eea !important;
        color: #667eea !important;
        background: white !important;
        transition: all 0.18s ease !important;
    }
    div[data-testid="column"] button:hover {
        background: #667eea !important;
        color: white !important;
    }

    /* Chat input */
    .stChatInput textarea {
        border-radius: 12px !important;
        border: 1.5px solid #d0d5f5 !important;
        font-size: 0.9rem !important;
    }
    .stChatInput textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.12) !important;
    }

    /* Config warning banner */
    .config-warning {
        background: #fff8e1;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        border-left: 3px solid #ffc107;
        font-size: 0.83rem;
        color: #5d4e37;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# .env loading
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Agent construction — cached per (api_key, model) pair
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _get_agent_and_skills(api_key: str, model: str):
    from agent import build_agent_and_skills
    return build_agent_and_skills(api_key, model)


# ---------------------------------------------------------------------------
# Async runner
# ---------------------------------------------------------------------------
def run_async(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-header">
            <h2>🤖 SK Agent Skills Playground</h2>
            <p>Semantic Kernel · Hello World Harness</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        value=os.environ.get("OPENAI_API_KEY", ""),
        type="password",
        placeholder="sk-...",
        help="Your OpenAI API key. Set OPENAI_API_KEY in .env to pre-fill.",
    )
    model_input = st.text_input(
        "Model",
        value=os.environ.get("OPENAI_MODEL", "gpt-5"),
        help="OpenAI model name (e.g. gpt-5, gpt-4o)",
    )

    st.divider()

    # Loaded skills panel
    st.markdown("#### Loaded Skills")
    if api_key_input and model_input:
        try:
            _, skills_meta = _get_agent_and_skills(api_key_input, model_input)
            for s in skills_meta:
                badge = "📄 file" if s.source == "file" else "🐍 code"
                desc_preview = s.description[:115] + ("…" if len(s.description) > 115 else "")
                st.markdown(
                    f"""
                    <div class="skill-card">
                        <div class="skill-badge">{badge}</div>
                        <div class="skill-name">{s.name}</div>
                        <div class="skill-desc">{desc_preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except Exception as exc:
            st.caption(f"Skills unavailable: {exc}")
    else:
        st.caption("Add your API key above to see loaded skills.")

    st.divider()

    if st.button("🗑  Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.sk_thread = None
        st.rerun()

    st.markdown(
        "<p style='font-size:0.7rem;color:#bbb;text-align:center;margin-top:0.5rem'>"
        "semantic-kernel · GA v1.x</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
st.markdown('<p class="chat-title">Agent Skills Playground</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="chat-subtitle">Powered by <strong>Semantic Kernel</strong> · '
    'Skills loaded from <code>skills/</code></p>',
    unsafe_allow_html=True,
)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sk_thread" not in st.session_state:
    st.session_state.sk_thread = None

# Config gate
if not api_key_input:
    st.markdown(
        '<div class="config-warning">⚠️ Enter your <strong>OpenAI API Key</strong> '
        "in the sidebar to start chatting.</div>",
        unsafe_allow_html=True,
    )

# Suggestion chips — only when conversation is empty
if not st.session_state.messages:
    suggestions = [
        ("👋", "Say hello"),
        ("🔧", "What skills are loaded?"),
        ("📋", "How does this harness work?"),
        ("🌍", "What's your environment?"),
    ]
    cols = st.columns(len(suggestions))
    for col, (icon, label) in zip(cols, suggestions):
        with col:
            if st.button(f"{icon} {label}", use_container_width=True):
                st.session_state._pending_input = label
                st.rerun()

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# Consume pending suggestion or chat input
pending = st.session_state.pop("_pending_input", None)
user_input = st.chat_input("Ask anything…", disabled=not api_key_input) or pending

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking…"):
            try:
                agent, _ = _get_agent_and_skills(api_key_input, model_input)

                async def _chat():
                    from agent import chat_turn
                    return await chat_turn(agent, st.session_state.sk_thread, user_input)

                reply, new_thread = run_async(_chat())
                st.session_state.sk_thread = new_thread

            except EnvironmentError as e:
                reply = f"⚠️ Configuration error: {e}"
            except Exception as e:
                reply = f"❌ {type(e).__name__}: {e}"

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
