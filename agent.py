"""
Hello World Agent Harness — Microsoft Agent Framework (MAF)

Demonstrates loading Agent Skills from a skills/ directory tree and running
an interactive chat loop. Skills are discovered automatically from SKILL.md
files via SkillsProvider.

Requirements:
    pip install agent-framework --pre

Environment variables (copy .env.example to .env and fill in):
    OPENAI_API_KEY   — your OpenAI API key
    OPENAI_MODEL     — model to use (default: gpt-5)

Usage:
    python agent.py                  # interactive chat loop
    python agent.py "Hello, world!"  # single-turn from CLI arg
"""

import asyncio
import os
import sys
from pathlib import Path
from textwrap import dedent

# ---------------------------------------------------------------------------
# Optional: load .env file if python-dotenv is installed
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on real environment variables

# ---------------------------------------------------------------------------
# MAF imports
# ---------------------------------------------------------------------------
from agent_framework import OpenAIChatClient, Skill, SkillResource, SkillsProvider

# ---------------------------------------------------------------------------
# Build a supplementary code-defined skill alongside the file-based ones.
# This shows how inline skills and SKILL.md-based skills coexist.
# ---------------------------------------------------------------------------
harness_info = Skill(
    name="harness-info",
    description=(
        "Provide technical details about this agent harness: the MAF version, "
        "Python version, and loaded skills. Use when the user asks about the "
        "system, environment, or what skills are available."
    ),
    content=dedent("""\
        # Harness Info Skill

        When this skill is activated, report the following facts:
        1. The Python version currently running.
        2. The installed version of the `agent-framework` package.
        3. The names and descriptions of all skills that are loaded.

        Use the `environment` resource to get live values. Keep the output
        concise — a short bullet list is ideal.
    """),
    resources=[
        SkillResource(
            name="faq",
            content=dedent("""\
                Q: Can I add my own skills?
                A: Yes — create a new sub-directory under skills/ with a SKILL.md
                   file following the frontmatter + body format.

                Q: Do skills share state?
                A: No. Each skill is stateless; state lives in the conversation
                   session managed by the agent.

                Q: What is progressive disclosure?
                A: Only the skill name + description (~100 tokens) is injected
                   into the system prompt. The full SKILL.md body is fetched
                   lazily via load_skill when the agent decides the task matches.
            """),
        )
    ],
)


@harness_info.resource
def environment() -> str:
    """Return live environment details injected when the agent reads this resource."""
    import importlib.metadata

    try:
        maf_version = importlib.metadata.version("agent-framework")
    except importlib.metadata.PackageNotFoundError:
        maf_version = "unknown"

    return dedent(f"""\
        Python version : {sys.version.split()[0]}
        agent-framework: {maf_version}
        Skills root    : {SKILLS_DIR}
    """)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SKILLS_DIR = Path(__file__).parent / "skills"

AGENT_NAME = "HelloWorldAgent"
AGENT_INSTRUCTIONS = dedent("""\
    You are a friendly, concise assistant demonstrating the Microsoft Agent
    Framework Agent Skills system. You have access to skills that give you
    domain expertise. Always use the appropriate skill when the user's request
    matches its description — load it first before answering.
    Be warm, clear, and brief.
""")


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------
def build_skills_provider() -> SkillsProvider:
    """Create a SkillsProvider that combines file-based and code-defined skills."""
    return SkillsProvider(
        skill_paths=SKILLS_DIR,   # scans recursively for SKILL.md files
        skills=[harness_info],    # inline code-defined skills
    )


def build_agent(skills_provider: SkillsProvider):
    """Instantiate the agent using OpenAI chat completions."""
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-5")

    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your OpenAI API key."
        )

    client = OpenAIChatClient(
        api_key=api_key,
        model=model,
    )

    return client.as_agent(
        name=AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        context_providers=[skills_provider],
    )


# ---------------------------------------------------------------------------
# Run modes
# ---------------------------------------------------------------------------
async def run_single_turn(agent, message: str) -> None:
    """Send one message and print the response."""
    print(f"\nUser : {message}")
    result = await agent.run(message)
    print(f"Agent: {result.text}\n")


async def run_interactive(agent) -> None:
    """Simple REPL — type 'quit' or press Ctrl-C to exit."""
    print("MAF Hello World Harness — type 'quit' to exit\n")
    session = None  # reuse session across turns for conversation history

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

        if session is None:
            result = await agent.run(user_input)
        else:
            result = await agent.run(user_input, session=session)

        session = result.session  # carry conversation context forward
        print(f"Agent: {result.text}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main() -> None:
    skills_provider = build_skills_provider()
    agent = build_agent(skills_provider)

    if len(sys.argv) > 1:
        # Single-turn mode: python agent.py "your message here"
        message = " ".join(sys.argv[1:])
        await run_single_turn(agent, message)
    else:
        # Interactive REPL
        await run_interactive(agent)


if __name__ == "__main__":
    asyncio.run(main())
