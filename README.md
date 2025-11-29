# AI Assistant Starter

A **provider-agnostic framework** for standardizing AI coding assistant instructions. Write workflows once, use them with Claude, Cursor, Copilot, Gemini, and others.

## Why This Exists

AI coding assistants work better with structured guidance. This framework provides:

- **Reusable workflows** for common tasks (implement, debug, refactor, commit)
- **Role-based chatmodes** that control what the AI can do at each phase
- **Domain guidelines** for consistent code style across your team
- **Approval gates** to prevent unintended changes

## Quick Start

```bash
# Clone once
git clone https://github.com/hypefi/ai-assistant-starter.git ~/ai-assistant-starter

# Symlink to your project
for f in .ai-assistant .claude CLAUDE.md .cursorrules; do
  [ -e "$HOME/ai-assistant-starter/$f" ] && ln -sfn "$HOME/ai-assistant-starter/$f" "$f"
done

# Initialize project-specific config
/init
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `/explore` | Understand code (read-only) |
| `/plan` | Design approach before coding |
| `/implement` | Full workflow: explore → plan → code → commit |
| `/debug` | Find and fix bugs |
| `/validate` | Run type check, lint, tests |
| `/commit` | Review and commit with confirmation |
| `/refactor` | Multi-file changes with tracking |

## How It Works

```
Explore → Plan → [User Approval] → Code → Validate → [User Confirm] → Commit
```

The framework enforces a disciplined workflow where the AI explores before coding, plans before implementing, and confirms before committing.

## Structure

```
.ai-assistant/           # Reusable framework (symlinked)
├── workflows/           # Task definitions (implement, debug, etc.)
├── chatmodes/           # Role permissions (explorer, developer, etc.)
└── domains/             # Tech guidelines (TypeScript, testing, git)

.ai-project/             # Project-specific config (created by /init)
├── .memory.md           # Your tech stack
└── .context.md          # Your patterns
```

## Supported Providers

- **Claude Code** - `.claude/`, `CLAUDE.md`
- **Cursor** - `.cursorrules`
- **GitHub Copilot** - `.github/copilot-instructions.md`
- **Gemini** - `AGENTS.md`, `GEMINI.md`
- **Windsurf** - `.windsurfrules`

## License

MIT
