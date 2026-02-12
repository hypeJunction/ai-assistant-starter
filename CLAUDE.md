# AI Assistant Starter

Reusable AI coding assistant skills following the [Agent Skills specification](https://agentskills.io/specification), distributed via [skills.sh](https://skills.sh).

## Project Structure

```
skills/                          # All skills live here
├── <name>/
│   ├── SKILL.md                 # Skill definition (frontmatter + instructions)
│   ├── references/              # Optional support docs (templates, detection rules)
│   └── assets/                  # Optional scaffolding templates (rare; mainly init)
assets/                          # Presentation materials
CLAUDE.md                        # This file (project instructions)
CHANGELOG.md                     # Version history
README.md                        # User-facing documentation
presentation.md                  # Marp slide deck source
```

## Skill Format

Each skill is a `skills/<name>/SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name              # Must match directory name
description: One-line summary  # Used in skill discovery
user-invocable: false          # Only for background skills (omit for workflow skills)
---

# Skill Title

Instructions follow...
```

- **Workflow skills** (user-invocable): Triggered via `/name` commands
- **Background skills**: Add `user-invocable: false` — auto-loaded when relevant, no slash command
- `references/` directory: Support docs that guide execution (templates, detection rules)
- `assets/` directory: Scaffolding templates with `{{PLACEHOLDER}}` variables (only used by `/init`)

## Installation

```bash
# Install all skills
npx skills add hypefi/ai-assistant-starter

# Install specific skills
npx skills add hypefi/ai-assistant-starter -s commit
```

## Available Skills

### Workflow Skills (23 total)

**Development Workflows**

| Skill | Purpose |
|-------|---------|
| `/explore` | Understand code (read-only) |
| `/plan` | Design approach before coding |
| `/implement` | Full workflow: explore → plan → code → test → commit |
| `/debug` | Find and fix bugs |
| `/refactor` | Multi-file changes with tracking |

**Quality & Testing**

| Skill | Purpose |
|-------|---------|
| `/validate` | Run type check, lint, tests |
| `/cover` | Ensure test coverage for changes |
| `/review` | Review current branch against base |
| `/security-review` | Systematic security audit with confidence-based reporting |

**Git & Release**

| Skill | Purpose |
|-------|---------|
| `/commit` | Review and commit with confirmation |
| `/iterate-pr` | Iterate on PR until CI passes and feedback addressed |
| `/pr` | Create pull request |
| `/wrap` | End-of-session: test → validate → review → commit |
| `/hotfix` | Emergency bug fix with abbreviated validation |
| `/release` | Version bump, changelog, and tagging |

**Utilities**

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

### Background Skills (19 total)

Auto-loaded when relevant — no slash command needed:

| Skill | Domain |
|-------|--------|
| `ai-assistant-protocol` | Core execution protocol, code quality, testing requirements |
| `git-conventions` | Branch naming, commit messages, workflow patterns |
| `communication-guidelines` | Response formatting and status indicators |
| `code-review-guidelines` | Review checklist and feedback patterns |
| `typescript-guidelines` | TypeScript best practices and patterns |
| `vitest-guidelines` | Testing with Vitest |
| `security-guidelines` | OWASP top 10, input validation, XSS prevention |
| `documentation-guidelines` | When and how to comment code |
| `naming-guidelines` | Naming conventions for variables, functions, files |
| `error-handling-guidelines` | Custom error classes, try-catch, error boundaries |
| `logging-guidelines` | Structured logging, log levels, correlation IDs |
| `performance-guidelines` | Frontend/backend optimization, caching, profiling |
| `rest-api-guidelines` | URL structure, HTTP methods, status codes |
| `zod-guidelines` | Schema validation, API/form validation |
| `prisma-guidelines` | Schema design, queries, migrations |
| `docker-node-guidelines` | Dockerfile best practices, multi-stage builds |
| `github-actions-guidelines` | CI/CD pipelines, caching, secrets, deployment |
| `storybook-react-guidelines` | Story structure, interaction tests, play functions |
| `env-config-guidelines` | Environment variables, type-safe config, feature flags |

## Contributing a Skill

### Adding a new skill

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`)
2. Name must be lowercase, hyphen-separated, and match the directory name
3. For background skills, add `user-invocable: false` to frontmatter
4. Add `references/` directory if the skill needs support docs (templates, rules)
5. Update the skill tables in both `README.md` and this file
6. Update `CHANGELOG.md` under `[Unreleased]`

### Modifying an existing skill

1. Edit the `SKILL.md` directly — the frontmatter `description` is what users see in discovery
2. If changing the skill's purpose or name, update `README.md`, `CLAUDE.md`, and `CHANGELOG.md`
3. Keep instructions concise — use `references/` for lengthy support material

### Conventions

- Skill instructions use progressive disclosure: frontmatter is loaded at startup, full body on activation
- Workflow skills should define clear phases with approval gates where user confirmation is needed
- Background skills should state when they auto-load (e.g., "Auto-loaded when working with TypeScript files")
- Descriptions are single-line and start with an action or noun (not "This skill...")

## Project Setup (for consumers)

After installing skills, run `/init` to scaffold project-specific configuration:

```
your-project/
├── .claude/skills/          # Installed skills (managed by skills.sh)
├── CLAUDE.md                # Project context (tech stack, conventions)
└── .ai-project/             # Project state (created by /init)
    ├── .memory.md           # Architecture overview
    ├── .context.md          # Patterns and imports
    ├── config.md            # Framework settings
    ├── project/             # Detected project config (commands, structure, stack)
    ├── domains/             # Stack-specific domain rules (*.instructions.md)
    ├── todos/               # Technical debt tracking
    ├── decisions/           # Architecture decision records
    └── history/             # Work history
```
