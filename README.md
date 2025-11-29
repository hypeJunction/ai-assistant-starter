# AI Assistant Starter

A **provider-agnostic framework** for standardizing AI coding assistant instructions. Write workflows once, use them with Claude Code, Cursor, Copilot, Gemini, and others.

## Why This Exists

AI coding assistants work better with structured guidance. This framework provides:

- **Reusable workflows** for common tasks (implement, debug, refactor, commit)
- **Role-based chatmodes** that control what the AI can do at each phase
- **Domain guidelines** for consistent code style across your team
- **Approval gates** to prevent unintended changes

## Installation

### Option 1: Symlink (Recommended)

Clone once, symlink to all your projects. Updates propagate automatically.

```bash
# Clone to a central location
git clone https://github.com/hypefi/ai-assistant-starter.git ~/ai-assistant

# In your project directory:
cd ~/your-project

# Symlink the framework
ln -sfn ~/ai-assistant/.ai-assistant .ai-assistant

# Symlink Claude commands (keep .claude/ local for settings)
mkdir -p .claude
ln -sfn ~/ai-assistant/.claude/commands .claude/commands

# Symlink entry points for your providers
ln -sfn ~/ai-assistant/CLAUDE.md CLAUDE.md
ln -sfn ~/ai-assistant/.cursorrules .cursorrules      # Cursor
ln -sfn ~/ai-assistant/.windsurfrules .windsurfrules  # Windsurf
ln -sfn ~/ai-assistant/.clinerules .clinerules        # Cline/Roo

# Initialize project-specific config
# (Run this command in your AI assistant)
/init
```

**What gets symlinked (shared):**
- `.ai-assistant/` - The framework (workflows, chatmodes, domains)
- `.claude/commands/` - Slash commands that invoke workflows
- `CLAUDE.md`, `.cursorrules`, etc. - Provider entry points

**What stays local (project-specific):**
- `.ai-project/` - Project overrides (created by `/init`)
- `.claude/settings.json` - Your personal settings

### Option 2: Git Submodule

For version-locked dependencies:

```bash
git submodule add https://github.com/hypefi/ai-assistant-starter.git .ai-assistant-starter

# Symlink from the submodule
ln -sfn .ai-assistant-starter/.ai-assistant .ai-assistant
mkdir -p .claude
ln -sfn .ai-assistant-starter/.claude/commands .claude/commands
ln -sfn .ai-assistant-starter/CLAUDE.md CLAUDE.md
```

Update with: `git submodule update --remote`

### Option 3: Copy (No Updates)

Copy files directly if you want full control and don't need updates:

```bash
cp -r ~/ai-assistant/.ai-assistant .
cp -r ~/ai-assistant/.claude .
cp ~/ai-assistant/CLAUDE.md .
```

## Updating

```bash
# If using symlinks
cd ~/ai-assistant && git pull

# If using submodule
git submodule update --remote

# Then refresh project config
/init --update
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
| `/add-story` | Create Storybook stories |

See [INDEX.md](.ai-assistant/INDEX.md) for all commands.

## How It Works

```
Explore → Plan → [User Approval] → Code → Validate → [User Confirm] → Commit
```

The framework enforces a disciplined workflow where the AI explores before coding, plans before implementing, and confirms before committing.

## Structure

```
~/ai-assistant/              # Central clone (shared across projects)
├── .ai-assistant/           # Framework core
│   ├── workflows/           # Task definitions
│   ├── chatmodes/           # Role permissions
│   ├── domains/             # Tech guidelines
│   └── .ai-project/         # Templates for project config
├── .claude/commands/        # Slash commands
├── CLAUDE.md                # Claude Code entry point
├── .cursorrules             # Cursor entry point
└── ...                      # Other provider files

~/your-project/              # Your project
├── .ai-assistant -> ~/ai-assistant/.ai-assistant
├── .claude/
│   ├── commands -> ~/ai-assistant/.claude/commands
│   ├── settings.json        # Local (not symlinked)
│   └── settings.local.json  # Local (not symlinked)
├── .ai-project/             # Project-specific overrides
│   ├── .memory.md           # Your tech stack
│   └── .context.md          # Your patterns
├── CLAUDE.md -> ~/ai-assistant/CLAUDE.md
└── .cursorrules -> ~/ai-assistant/.cursorrules
```

## Project Overrides

After running `/init`, customize your project in `.ai-project/`:

- **`.memory.md`** - Document your tech stack, architecture
- **`.context.md`** - Common patterns, imports, conventions
- **`config.md`** - Framework settings (commit style, validation)

These override the framework defaults for your specific project.

## Supported Providers

| Provider | Entry Point | Commands |
|----------|-------------|----------|
| Claude Code | `CLAUDE.md` | `.claude/commands/` |
| Cursor | `.cursorrules` | Built-in |
| Windsurf | `.windsurfrules` | Built-in |
| Cline/Roo | `.clinerules` | Built-in |
| GitHub Copilot | `.github/copilot-instructions.md` | N/A |
| Gemini | `GEMINI.md` | N/A |

## License

MIT
