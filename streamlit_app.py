"""
MAF Hello World — Streamlit Chat UI

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
    page_title="MAF Agent Skills Playground",
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
    /* ── Global font ───────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Hide default Streamlit chrome ─────────────────────────── */
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* ── Sidebar gradient header ────────────────────────────────── */
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 14px;
        padding: 1.25rem 1rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .sidebar-header h2 { margin: 0; font-size: 1.15rem; font-weight: 700; }
    .sidebar-header p  { margin: 0.25rem 0 0; font-size: 0.78rem; opacity: 0.88; }

    /* ── Skill cards ────────────────────────────────────────────── */
    .skill-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #eef0fb 100%);
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.6rem;
        border-left: 3px solid #667eea;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    .skill-name {
        font-size: 0.82rem;
        font-weight: 600;
        color: #4a4a8a;
        margin-bottom: 0.25rem;
    }
    .skill-desc {
        font-size: 0.73rem;
        color: #666;
        line-height: 1.4;
    }
    .skill-badge {
        display: inline-block;
        background: #667eea22;
        color: #667eea;
        border-radius: 99px;
        padding: 1px 8px;
        font-size: 0.68rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }

    /* ── Chat area title ────────────────────────────────────────── */
    .chat-title {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .chat-subtitle {
        color: #888;
        font-size: 0.9rem;
        margin-top: 0.1rem;
        margin-bottom: 1.2rem;
    }

    /* ── Suggestion chips ───────────────────────────────────────── */
    div[data-testid="column"] button {
        border-radius: 99px !important;
        font-size: 0.8rem !important;
        padding: 0.3rem 0.9rem !important;
        border: 1.5px solid #667eea !important;
        color: #667eea !important;
        background: white !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="column"] button:hover {
        background: #667eea !important;
        color: white !important;
    }

    /* ── Chat input ─────────────────────────────────────────────── */
    .stChatInput textarea {
        border-radius: 12px !important;
        border: 1.5px solid #d0d5f5 !important;
        font-size: 0.9rem !important;
    }
    .stChatInput textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
    }

    /* ── Error / warning boxes ──────────────────────────────────── */
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
# MAF imports (deferred so we can show a nice error if not installed)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _import_maf():
    try:
        from agent_framework import OpenAIChatClient, Skill, SkillResource, SkillsProvider
        return OpenAIChatClient, Skill, SkillResource, SkillsProvider, None
    except ImportError as e:
        return None, None, None, None, str(e)


# ---------------------------------------------------------------------------
# Agent construction (cached — built once, reused across reruns)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _build_agent(api_key: str, model: str):
    """Build and cache the MAF agent. Re-runs only when api_key/model change."""
    from agent_framework import OpenAIChatClient, Skill, SkillResource, SkillsProvider
    from textwrap import dedent
    import sys

    SKILLS_DIR = Path(__file__).parent / "skills"

    harness_info = Skill(
        name="harness-info",
        description=(
            "Provide technical details about this agent harness: the MAF version, "
            "Python version, and loaded skills. Use when the user asks about the "
            "system, environment, or what skills are available."
        ),
        content=dedent("""\
            # Harness Info Skill
            Report the Python version, agent-framework version, and list of loaded
            skills. Use the `environment` resource for live values. Be concise.
        """),
        resources=[
            SkillResource(
                name="faq",
                content=dedent("""\
                    Q: Can I add my own skills?
                    A: Create a new sub-directory under skills/ with a SKILL.md file.

                    Q: What is progressive disclosure?
                    A: Only name + description (~100 tokens) enters the system prompt.
                       Full content is fetched lazily via load_skill.
                """),
            )
        ],
    )

    @harness_info.resource
    def environment() -> str:
        import importlib.metadata
        try:
            maf_version = importlib.metadata.version("agent-framework")
        except importlib.metadata.PackageNotFoundError:
            maf_version = "unknown"
        return dedent(f"""\
            Python version : {sys.version.split()[0]}
            agent-framework: {maf_version}
            Model          : {model}
            Skills root    : {SKILLS_DIR}
        """)

    provider = SkillsProvider(
        skill_paths=SKILLS_DIR,
        skills=[harness_info],
    )

    client = OpenAIChatClient(api_key=api_key, model=model)

    agent = client.as_agent(
        name="HelloWorldAgent",
        instructions=dedent("""\
            You are a friendly, concise assistant demonstrating the Microsoft Agent
            Framework Agent Skills system. Use the appropriate skill whenever the
            user's request matches its description — load it before answering.
            Be warm, clear, and brief.
        """),
        context_providers=[provider],
    )

    # Also expose loaded skills list for the sidebar
    skills_meta = []
    for skill in [harness_info]:
        skills_meta.append({"name": skill.name, "description": skill.description, "source": "code"})

    # File-based skills discovered from SKILL.md files
    for skill_dir in sorted(SKILLS_DIR.rglob("SKILL.md")):
        import re
        text = skill_dir.read_text()
        name_match = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
        desc_match = re.search(r"^description:\s*>-?\n((?:[ \t]+.+\n?)+)", text, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else skill_dir.parent.name
        desc = " ".join(desc_match.group(1).split()) if desc_match else ""
        skills_meta.append({"name": name, "description": desc, "source": "file"})

    return agent, skills_meta


# ---------------------------------------------------------------------------
# Async helper
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
            <h2>🤖 MAF Skills Playground</h2>
            <p>Microsoft Agent Framework · Hello World</p>
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

    # Skills panel
    st.markdown("#### Loaded Skills")
    if api_key_input and model_input:
        try:
            _, skills_meta = _build_agent(api_key_input, model_input)
            for s in skills_meta:
                badge = "📄 file" if s["source"] == "file" else "🐍 code"
                st.markdown(
                    f"""
                    <div class="skill-card">
                        <div class="skill-badge">{badge}</div>
                        <div class="skill-name">{s['name']}</div>
                        <div class="skill-desc">{s['description'][:120]}{'…' if len(s['description']) > 120 else ''}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except Exception:
            st.caption("Skills will appear once the agent is ready.")
    else:
        st.caption("Add your API key above to see loaded skills.")

    st.divider()

    if st.button("🗑  Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.maf_session = None
        st.rerun()

    st.markdown(
        "<p style='font-size:0.7rem;color:#aaa;text-align:center;margin-top:0.5rem'>"
        "agent-framework · pre-release</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
st.markdown('<p class="chat-title">Agent Skills Playground</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="chat-subtitle">Powered by Microsoft Agent Framework · '
    'Skills loaded from <code>skills/</code></p>',
    unsafe_allow_html=True,
)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "maf_session" not in st.session_state:
    st.session_state.maf_session = None

# Config check
if not api_key_input:
    st.markdown(
        '<div class="config-warning">⚠️ Enter your <strong>OpenAI API Key</strong> '
        "in the sidebar to start chatting.</div>",
        unsafe_allow_html=True,
    )

# Suggestion chips (only shown when chat is empty)
if not st.session_state.messages:
    suggestions = [
        "👋 Say hello",
        "🔧 What skills are loaded?",
        "📋 Tell me about this harness",
        "🌍 What's your environment?",
    ]
    cols = st.columns(len(suggestions))
    for col, suggestion in zip(cols, suggestions):
        with col:
            if st.button(suggestion, use_container_width=True):
                st.session_state._pending_input = suggestion.split(" ", 1)[1]
                st.rerun()

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# Handle pending suggestion click
pending = st.session_state.pop("_pending_input", None)

# Chat input
user_input = st.chat_input("Ask anything…", disabled=not api_key_input) or pending

if user_input:
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    # Build / fetch cached agent
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking…"):
            try:
                agent, _ = _build_agent(api_key_input, model_input)

                async def _chat():
                    if st.session_state.maf_session is None:
                        result = await agent.run(user_input)
                    else:
                        result = await agent.run(
                            user_input, session=st.session_state.maf_session
                        )
                    return result

                result = run_async(_chat())
                st.session_state.maf_session = result.session
                reply = result.text
            except EnvironmentError as e:
                reply = f"⚠️ Configuration error: {e}"
            except Exception as e:
                reply = f"❌ Error: {e}"

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
