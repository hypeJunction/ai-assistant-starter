# AI Assistant Starter

Reusable skills for AI coding assistants, following the [Agent Skills specification](https://agentskills.io/specification).

## Why This Exists

AI coding assistants work better with structured guidance. This collection provides:

- **Workflow skills** for common tasks (implement, debug, refactor, commit)
- **Domain guidelines** for consistent code style across your team
- **Approval gates** to prevent unintended changes
- **Background knowledge** auto-loaded when relevant

## Installation

```bash
# Clone the repo
git clone https://github.com/hypefi/ai-assistant-starter.git

# Install all skills into your project
npx skills add ./ai-assistant-starter

# Or install specific skills
npx skills add ./ai-assistant-starter -s commit
npx skills add ./ai-assistant-starter -s implement
npx skills add ./ai-assistant-starter -s validate
```

Skills are installed to `.claude/skills/<name>/SKILL.md` and become available as `/name` commands.

## Skills

### Development Workflows

| Skill | Purpose |
|-------|---------|
| `/explore` | Understand code (read-only) |
| `/plan` | Design approach before coding |
| `/implement` | Full workflow: explore → plan → code → test → commit |
| `/debug` | Find and fix bugs |
| `/refactor` | Multi-file changes with tracking |
| `/migrate` | Database/schema migrations with rollback planning |

### Quality & Testing

| Skill | Purpose |
|-------|---------|
| `/validate` | Run type check, lint, tests |
| `/test-coverage` | Ensure test coverage for changes |
| `/tdd` | Test-driven development (RED → GREEN → REFACTOR) |
| `/api-test` | Discover, test, and report on API endpoints |
| `/e2e` | End-to-end testing with Playwright/Cypress |
| `/review` | Review current branch against base |
| `/security-review` | Systematic security audit with confidence-based reporting |
| `/accessibility-review` | WCAG 2.1 AA audit with automated + manual checks |

### Git & Release

| Skill | Purpose |
|-------|---------|
| `/commit` | Review and commit with confirmation |
| `/iterate-pr` | Iterate on PR until CI passes and feedback addressed |
| `/pr` | Create pull request |
| `/finish` | End-of-session: test → validate → review → commit |
| `/hotfix` | Emergency bug fix with abbreviated validation |
| `/release` | Version bump, changelog, and tagging |

### Utilities

| Skill | Purpose |
|-------|---------|
| `/deps` | Audit, update, and manage dependencies |
| `/docs` | Add or improve documentation |
| `/revert` | Safely rollback changes |
| `/sync` | Align documentation with codebase |
| `/adr` | Capture an Architecture Decision Record |
| `/add-story` | Create Storybook stories |
| `/add-todo` | Document deferred work |
| `/track-files` | Track files for batch operations |
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
- **interaction-boundaries** — Human-AI interaction boundaries, non-anthropomorphic communication
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
├── .claude/skills/          # Installed skills
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

The system uses two layers, with project-specific context taking precedence:

| Layer | Source | Purpose |
|-------|--------|---------|
| **Base skills** | `skills/<name>/SKILL.md` | Reusable workflows and domain guidelines |
| **Project context** | `.ai-project/` | Project-specific overrides, patterns, and state |

`/init` detects your tech stack from `package.json` and config files, generates project-specific context, copies relevant domain instruction files, and creates a `CLAUDE.md` with project-level instructions.

To add project-specific domain rules, create files in `.ai-project/domains/`:

```markdown
<!-- .ai-project/domains/my-api.instructions.md -->
# My API Conventions

- All endpoints return `{ data, error, meta }` envelope
- Use `zod` for request validation
- Rate limiting: 100 req/min per API key
```

## Specification Compatibility

Skills follow the [Agent Skills specification](https://agentskills.io/specification):

- Each skill is a directory containing a `SKILL.md` file with YAML frontmatter
- Required fields: `name` (matches directory name), `description`
- Progressive disclosure: metadata loaded at startup, full instructions on activation
- Optional `references/` and `assets/` directories for supplementary content

Background skills use `user-invocable: false` in frontmatter — a runtime extension not part of the base spec.

## Updating

```bash
# Pull the latest changes
cd ai-assistant-starter
git pull

# Re-install into your project
cd /path/to/your-project
npx skills add ./ai-assistant-starter

# Then refresh project config
/init --update
```

## License

MIT
