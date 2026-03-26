# About This Harness

This is a **hello-world** demonstration of the Microsoft Agent Framework (MAF)
Agent Skills system.

## Key Concepts

| Concept | Description |
|---|---|
| `SKILL.md` | Markdown file with YAML frontmatter that defines a skill's name, description, and instructions |
| `SkillsProvider` | Context provider that scans directories for `SKILL.md` files and serves them to agents |
| Progressive disclosure | Skills are advertised cheaply (~100 tokens); full content only loaded when needed |
| `@skill.resource` | Decorator to attach dynamic content fetched at read time |
| `@skill.script` | Decorator to attach executable functions the agent can invoke |

## Project Layout

```
maf_test/
├── agent.py            # Main entry point
├── requirements.txt    # Python dependencies
├── .env.example        # Required environment variables
└── skills/
    └── hello-world/
        ├── SKILL.md    # This skill's instructions (frontmatter + body)
        └── references/
            └── ABOUT.md   # This file — loaded on demand via read_skill_resource
```

## Further Reading

- GitHub: https://github.com/microsoft/agent-framework
- Docs: https://learn.microsoft.com/en-us/agent-framework/agents/skills
- Spec: https://agentskills.io/specification
