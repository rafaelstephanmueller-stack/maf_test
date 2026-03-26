"""
Hello World Agent Harness — Semantic Kernel

Demonstrates loading Agent Skills from a skills/ directory tree using
Semantic Kernel's native plugin system and ChatCompletionAgent.

Requirements:
    pip install -r requirements.txt

Environment variables (copy .env.example to .env and fill in):
    OPENAI_API_KEY  — your OpenAI API key
    OPENAI_MODEL    — model to use (default: gpt-5)

Usage:
    python agent.py                  # interactive REPL
    python agent.py "Hello, world!"  # single-turn from CLI arg
"""

import asyncio
import importlib.metadata
import os
import sys
from pathlib import Path
from textwrap import dedent

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

from skills_loader import SkillsPlugin, load_skills_from_dir, make_inline_skill

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SKILLS_DIR = Path(__file__).parent / "skills"

AGENT_NAME = "HelloWorldAgent"
AGENT_INSTRUCTIONS = dedent("""\
    You are a friendly, concise assistant demonstrating Semantic Kernel with Agent Skills.
    You have a `skills` plugin with two functions:
    - Call `list_skills` when the user asks what you can do or what skills are loaded.
    - Call `load_skill(name)` when a request matches a skill's domain, then answer
      using the loaded instructions.
    Be warm, clear, and brief.
""")

# ---------------------------------------------------------------------------
# Inline skill: harness metadata
# ---------------------------------------------------------------------------

def _harness_info_skill():
    try:
        sk_version = importlib.metadata.version("semantic-kernel")
    except importlib.metadata.PackageNotFoundError:
        sk_version = "unknown"

    content = dedent(f"""\
        ## Harness Info

        - **Python**: {sys.version.split()[0]}
        - **semantic-kernel**: {sk_version}
        - **Skills directory**: `{SKILLS_DIR}`

        ### FAQ

        **Q: How do I add a skill?**
        A: Create `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`)
           followed by a markdown body containing the skill's instructions.

        **Q: What is progressive disclosure?**
        A: Only skill names and descriptions enter the system prompt (low token cost).
           Full instructions are fetched on demand via `load_skill(name)`.

        **Q: What powers this harness?**
        A: Microsoft Semantic Kernel (Python, GA v1.x) — `ChatCompletionAgent` with
           a native `SkillsPlugin` that scans `skills/` for SKILL.md files at startup.
    """)

    return make_inline_skill(
        name="harness-info",
        description=(
            "Report technical details: Semantic Kernel version, Python version, "
            "skills directory, and FAQ. Use when the user asks about the system, "
            "environment, or how this harness works."
        ),
        content=content,
    )

# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def build_agent_and_skills(api_key: str, model: str):
    """Build a ChatCompletionAgent with all loaded skills attached as a plugin."""
    all_skills = [_harness_info_skill()] + load_skills_from_dir(SKILLS_DIR)
    plugin = SkillsPlugin(all_skills)

    agent = ChatCompletionAgent(
        service=OpenAIChatCompletion(ai_model_id=model, api_key=api_key),
        name=AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        plugins=[plugin],
    )
    return agent, all_skills

# ---------------------------------------------------------------------------
# Chat helpers
# ---------------------------------------------------------------------------

async def chat_turn(
    agent: ChatCompletionAgent,
    thread: ChatHistoryAgentThread | None,
    user_input: str,
) -> tuple[str, ChatHistoryAgentThread]:
    """Send one user message, collect the full reply, and return updated thread."""
    parts = []
    async for response in agent.invoke(messages=user_input, thread=thread):
        parts.append(str(response.content))
        thread = response.thread
    return "".join(parts), thread

# ---------------------------------------------------------------------------
# Run modes
# ---------------------------------------------------------------------------

async def run_single_turn(agent, message: str) -> None:
    reply, _ = await chat_turn(agent, None, message)
    print(f"\nUser : {message}")
    print(f"Agent: {reply}\n")


async def run_interactive(agent) -> None:
    print("Semantic Kernel Agent Skills Harness — type 'quit' to exit\n")
    thread: ChatHistoryAgentThread | None = None

    while True:
        try:
            user_input = input("You  : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            print("Bye!")
            break

        reply, thread = await chat_turn(agent, thread, user_input)
        print(f"Agent: {reply}\n")

    if thread:
        await thread.delete()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-5")

    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    agent, _ = build_agent_and_skills(api_key, model)

    if len(sys.argv) > 1:
        await run_single_turn(agent, " ".join(sys.argv[1:]))
    else:
        await run_interactive(agent)


if __name__ == "__main__":
    asyncio.run(main())
