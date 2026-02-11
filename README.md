# AI Assistant Starter

Reusable skills for AI coding assistants, following the [Agent Skills specification](https://agentskills.io/specification) and distributed via [skills.sh](https://skills.sh).

## Overview

[Watch Presentation (11 min)](assets/presentation-video.mp4) | [Slides](assets/slides/presentation.html) | [Slide deck source](presentation.md)

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

## Specification Compatibility

Skills in this repository follow the [Agent Skills specification](https://agentskills.io/specification):

- Each skill is a directory containing a `SKILL.md` file with YAML frontmatter
- Required fields: `name` (matches directory name), `description`
- Progressive disclosure: metadata loaded at startup, full instructions on activation
- Optional `references/` and `assets/` directories for supplementary content

**Extension:** Background skills use `user-invocable: false` in frontmatter — a [skills.sh](https://skills.sh) runtime extension not part of the base spec. Skills without this field (or with it omitted) are user-invocable by default.

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

## Project Setup & Context Layering

After installing skills, run `/init` to scaffold project-specific configuration:

```
your-project/
├── .claude/skills/          # Installed skills (managed by skills.sh)
├── CLAUDE.md                # Project context (tech stack, conventions)
└── .ai-project/             # Project state (created by /init)
    ├── .memory.md           # Architecture overview
    ├── .context.md          # Patterns and imports
    ├── config.md            # Framework settings
    ├── project/             # Project configuration
    │   ├── commands.md      # Build/test/lint commands
    │   ├── structure.md     # Directory layout
    │   ├── patterns.md      # Code patterns and conventions
    │   └── stack.md         # Technology stack
    ├── domains/             # Stack-specific domain rules
    │   └── *.instructions.md
    ├── todos/               # Technical debt tracking
    ├── decisions/           # Architecture decision records
    └── history/             # Work history
```

### Context Layers

The system uses two layers, with project-specific context taking precedence:

| Layer | Source | Purpose |
|-------|--------|---------|
| **Base skills** | `skills/<name>/SKILL.md` | Reusable workflows and domain guidelines |
| **Project context** | `.ai-project/` | Project-specific overrides, patterns, and state |

**How `/init` connects them:**
1. Detects your tech stack from `package.json` / config files
2. Generates project-specific context in `.ai-project/project/`
3. Copies relevant domain instruction files to `.ai-project/domains/`
4. Creates `CLAUDE.md` with project-level instructions

### Local Domain Customization

To add project-specific domain rules, create files in `.ai-project/domains/`:

```markdown
<!-- .ai-project/domains/my-api.instructions.md -->
# My API Conventions

- All endpoints return `{ data, error, meta }` envelope
- Use `zod` for request validation
- Rate limiting: 100 req/min per API key
```

These supplement (and can override) the base domain guideline skills.

## Updating

```bash
# Update all installed skills
npx skills update hypefi/ai-assistant-starter

# Then refresh project config
/init --update
```

## License

MIT
