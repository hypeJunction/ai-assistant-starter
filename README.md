# AI Assistant Starter

Reusable skills for AI coding assistants, distributed via [skills.sh](https://skills.sh).

## Overview

[▶️ **Watch Presentation** (11 min)](assets/presentation-video.mp4) | [📄 Slides](assets/slides/presentation.html) | [📝 Slide deck source](presentation.md)

*An honest conversation about LLMs in software engineering — pragmatism over hype.*

## Why This Exists

AI coding assistants work better with structured guidance. This collection provides:

- **Workflow skills** for common tasks (implement, debug, refactor, commit)
- **Domain guidelines** for consistent code style across your team
- **Approval gates** to prevent unintended changes
- **Background knowledge** auto-loaded when relevant

## Installation

```bash
# Install all skills
npx skills add hypefi/ai-assistant-starter

# Install specific skills
npx skills add hypefi/ai-assistant-starter -s commit
npx skills add hypefi/ai-assistant-starter -s implement
npx skills add hypefi/ai-assistant-starter -s validate
```

Skills are installed to `.claude/skills/<name>/SKILL.md` and become available as `/name` commands.

## Key Skills

### Development Workflows

| Skill | Purpose |
|-------|---------|
| `/explore` | Understand code (read-only) |
| `/plan` | Design approach before coding |
| `/implement` | Full workflow: explore → plan → code → test → commit |
| `/debug` | Find and fix bugs |
| `/refactor` | Multi-file changes with tracking |

### Quality & Testing

| Skill | Purpose |
|-------|---------|
| `/validate` | Run type check, lint, tests |
| `/cover` | Ensure test coverage for changes |
| `/review` | Review current branch against base |

### Git & Release

| Skill | Purpose |
|-------|---------|
| `/commit` | Review and commit with confirmation |
| `/pr` | Create pull request |
| `/wrap` | End-of-session: test → validate → review → commit |
| `/hotfix` | Emergency bug fix with abbreviated validation |
| `/release` | Version bump, changelog, and tagging |

### Utilities

| Skill | Purpose |
|-------|---------|
| `/deps` | Audit, update, and manage dependencies |
| `/docs` | Add or improve documentation |
| `/revert` | Safely rollback changes |
| `/sync` | Align documentation with codebase |
| `/add-story` | Create Storybook stories |
| `/create-todo` | Document deferred work |
| `/file-list` | Track files for batch operations |
| `/init` | Bootstrap project configuration |

### Background Skills (auto-loaded)

These are loaded automatically when relevant — no slash command needed:

- **ai-assistant-protocol** — Core execution protocol, code quality, testing requirements
- **git-conventions** — Branch naming, commit messages, workflow patterns
- **typescript-guidelines** — TypeScript best practices and patterns
- **vitest-guidelines** — Testing with Vitest
- **security-guidelines** — OWASP top 10, input validation, XSS prevention
- **documentation-guidelines** — When and how to comment code
- **communication-guidelines** — Response formatting and status indicators
- **code-review-guidelines** — Review checklist and feedback patterns
- And more: REST API, Zod, Prisma, Docker, GitHub Actions, logging, naming, performance, error handling, Storybook, environment config

## How It Works

```
Explore → Plan → [Approval] → Code → Test → Validate → Review → [Confirm] → Commit
```

The skills enforce a disciplined workflow:
- **Explore before coding** — understand the codebase first
- **Plan before implementing** — design the approach
- **Test coverage required** — all code changes need tests
- **Validate before commit** — type check, lint, tests must pass
- **Review before merge** — self-review catches issues
- **Confirm before commit** — explicit user approval required

## Project Setup

After installing skills, run `/init` to scaffold project-specific configuration:

```
your-project/
├── .claude/skills/          # Installed skills (managed by skills.sh)
├── CLAUDE.md                # Project context (tech stack, conventions)
└── .ai-project/             # Project state (created by /init)
    ├── .memory.md           # Architecture overview
    ├── .context.md          # Patterns and imports
    ├── config.md            # Framework settings
    ├── todos/               # Technical debt tracking
    ├── decisions/           # Architecture decision records
    └── history/             # Work history
```

## Updating

```bash
# Update all installed skills
npx skills update hypefi/ai-assistant-starter

# Then refresh project config
/init --update
```

## License

MIT
