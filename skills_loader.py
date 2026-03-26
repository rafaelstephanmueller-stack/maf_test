"""
skills_loader.py — parse SKILL.md files and expose them as a Semantic Kernel plugin.

Directory layout expected:
    skills/
    └── <skill-name>/
        └── SKILL.md        ← YAML frontmatter (name, description) + markdown body
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Optional

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

from semantic_kernel.functions import kernel_function

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SkillMeta:
    name: str
    description: str
    content: str          # full markdown body after frontmatter
    source: str           # "file" | "code"
    path: Optional[Path] = None


# ---------------------------------------------------------------------------
# SKILL.md parser
# ---------------------------------------------------------------------------

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    fm_text, body = m.group(1), m.group(2).strip()
    if _HAS_YAML:
        fm = yaml.safe_load(fm_text) or {}
    else:
        # Minimal fallback: single-level key: value only
        fm: dict = {}
        current_key: str | None = None
        for line in fm_text.splitlines():
            if line and not line.startswith(" ") and ":" in line:
                k, _, v = line.partition(":")
                current_key = k.strip()
                fm[current_key] = v.strip().strip("\"'>-")
            elif current_key and line.startswith(" "):
                fm[current_key] = (fm.get(current_key, "") + " " + line.strip()).strip()
    return fm, body


def parse_skill_md(path: Path) -> SkillMeta:
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    description = str(fm.get("description", "")).strip().replace("\n", " ")
    return SkillMeta(
        name=fm.get("name", path.parent.name),
        description=description,
        content=body,
        source="file",
        path=path,
    )


def load_skills_from_dir(skills_dir: Path) -> list[SkillMeta]:
    """Recursively find all SKILL.md files under skills_dir and parse them."""
    skills = []
    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        try:
            skills.append(parse_skill_md(skill_md))
        except Exception as e:
            print(f"Warning: could not load {skill_md}: {e}", file=sys.stderr)
    return skills


def make_inline_skill(name: str, description: str, content: str) -> SkillMeta:
    """Create a code-defined skill without a backing file."""
    return SkillMeta(name=name, description=description, content=content, source="code")


# ---------------------------------------------------------------------------
# Semantic Kernel plugin
# ---------------------------------------------------------------------------

class SkillsPlugin:
    """
    Native SK plugin that exposes loaded skills to the agent.

    The agent can call:
      - list_skills()         → discover what skills exist
      - load_skill(name)      → fetch full instructions for a named skill
    """

    def __init__(self, skills: list[SkillMeta]):
        self._skills = {s.name: s for s in skills}

    @kernel_function(
        name="list_skills",
        description=(
            "List all available domain skills with their names and descriptions. "
            "Call this when the user asks what you can do or which skills are loaded."
        ),
    )
    def list_skills(self) -> Annotated[str, "Formatted list of available skills."]:
        if not self._skills:
            return "No skills are currently loaded."
        lines = ["**Available skills:**\n"]
        for s in self._skills.values():
            icon = "📄" if s.source == "file" else "🐍"
            lines.append(f"- {icon} **{s.name}**: {s.description}")
        return "\n".join(lines)

    @kernel_function(
        name="load_skill",
        description=(
            "Load the full instructions for a named skill. "
            "Call this when the user's request matches a skill's domain, "
            "before composing your answer."
        ),
    )
    def load_skill(
        self,
        name: Annotated[str, "Skill name exactly as returned by list_skills."],
    ) -> Annotated[str, "Full skill instructions in markdown."]:
        skill = self._skills.get(name)
        if not skill:
            available = ", ".join(self._skills.keys()) or "none"
            return f"Skill '{name}' not found. Available: {available}"
        return f"# Skill: {skill.name}\n\n{skill.content}"
