# AI Assistant Starter

Reusable AI coding assistant skills following the [Agent Skills specification](https://agentskills.io/specification).

## Project Structure

```
skills/                          # All skills live here
├── <name>/
│   ├── SKILL.md                 # Skill definition (frontmatter + instructions)
│   ├── references/              # Optional support docs (templates, detection rules)
│   └── assets/                  # Optional scaffolding templates (rare; mainly init)
CLAUDE.md                        # This file (project instructions)
CHANGELOG.md                     # Version history
README.md                        # User-facing documentation
```

## Skill Format

Each skill is a `skills/<name>/SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name              # Must match directory name
description: One-line summary  # Used in skill discovery
category: process             # process | meta | guideline | protocol | enforcement
triggers:                      # Intent keywords for auto-routing (workflow skills only)
  - keyword phrase
  - another phrase
user-invocable: false          # Only for background skills (omit for workflow skills)
---

# Skill Title

Instructions follow...
```

- **Workflow skills** (user-invocable): Triggered via `/name` commands or matched by intent triggers
- **Background skills**: Add `user-invocable: false` — auto-loaded when relevant, no slash command
- `references/` directory: Support docs that guide execution (templates, detection rules)
- `assets/` directory: Scaffolding templates with `{{PLACEHOLDER}}` variables (only used by `/init`)

## Installation

```bash
# Clone the repo
git clone https://github.com/hypefi/ai-assistant-starter.git

# Install all skills into your project
npx skills add ./ai-assistant-starter

# Install specific skills
npx skills add ./ai-assistant-starter -s commit
```

## Available Skills

### Workflow Skills (36 total, categories: process + meta)

**Development Workflows**

| Skill | Purpose |
|-------|---------|
| `/start` | Scope a new work session to a ticket, worktree, and goal, auto-triggering on session start |
| `/explore` | Understand code (read-only) |
| `/plan` | Design approach before coding |
| `/implement` | Full workflow: explore → plan → code → test → commit |
| `/debug` | Find and fix bugs |
| `/refactor` | Multi-file changes with tracking |
| `/migrate` | Database/schema migrations with rollback planning |
| `/stack` | Split a large branch into a resumable series of stacked PRs |

**Quality & Testing**

| Skill | Purpose |
|-------|---------|
| `/validate` | Run type check, lint, tests |
| `/test-coverage` | Ensure test coverage for changes |
| `/tdd` | Test-driven development (RED → GREEN → REFACTOR) |
| `/spec-loop` | Scope-locked implementation with an approved file-scope contract |
| `/api-test` | Discover, test, and report on API endpoints |
| `/e2e` | End-to-end testing with Playwright/Cypress |
| `/review` | Review current branch against base |
| `/security-review` | Systematic security audit with confidence-based reporting |
| `/accessibility-review` | WCAG 2.1 AA audit with automated + manual checks |

**Git & Release**

| Skill | Purpose |
|-------|---------|
| `/commit` | Review and commit with confirmation |
| `/iterate-pr` | Iterate on PR until CI passes and feedback addressed |
| `/pr` | Create pull request |
| `/finish` | End-of-session: test → validate → review → commit |
| `/done` | Close out a session opened by /start — commit, create or update the PR, record the session outcome, and nudge context compaction |
| `/hotfix` | Emergency bug fix with abbreviated validation |
| `/release` | Version bump, changelog, and tagging |

**Utilities**

| Skill | Purpose |
|-------|---------|
| `/deps` | Audit, update, and manage dependencies |
| `/docs` | Add or improve documentation |
| `/revert` | Safely rollback changes |
| `/sync` | Align documentation with codebase |
| `/adr` | Capture an Architecture Decision Record |
| `/add-story` | Create Storybook stories |
| `/add-todo` | Document deferred work |
| `/research` | Ethical web research with attribution and license compliance |
| `/track-files` | Track files for batch operations |
| `/cost-audit` | Audit Langfuse traces for token-cost waste and propose evidence-backed fixes |
| `/session-retro` | Analyze the current session for behavioral issues and propose fixes plus prompt tips |
| `/tooling-audit` | Audit installed plugins, MCP servers, skills, and permissions against usage evidence |
| `/init` | Bootstrap project configuration |
| `/apply-template` | Apply the standardized CLAUDE.md template (task classification, search-relevance, process hygiene) to an existing installation, with opt-in companion READMEs, circuit-breaker/cost-guardrail/prompt-context-router hooks, and cost-saving settings.json env vars |

### Background Skills (26 total)

Auto-loaded when relevant — no slash command needed:

**Protocol Skills** (category: protocol)

| Skill | Domain |
|-------|--------|
| `ai-assistant-protocol` | Core execution protocol, code quality, testing requirements |
| `context-disambiguation` | When to ask clarifying questions vs. explore, to keep initial context small |
| `communication-guidelines` | Response formatting and status indicators |
| `code-review-guidelines` | Review checklist and feedback patterns |
| `interaction-boundaries` | Human-AI interaction boundaries, non-anthropomorphic communication |

**Enforcement Skills** (category: enforcement)

| Skill | Domain |
|-------|--------|
| `branch-protection` | Runtime hook: blocks force-push, hard reset on protected branches |
| `destructive-command-protection` | Runtime hook: blocks rm -rf, DROP DATABASE, and other destructive commands |
| `context-circuit-breaker` | Runtime hook: warns (never blocks) on subagent fan-out and expensive-call loops |
| `cost-guardrail` | Runtime hook: warns/blocks Agent spawns and Bash calls whose historical cost is disproportionate, using cost-audit-derived baselines |
| `prompt-context-router` | Runtime hook: classifies each prompt by task class and topic-pivot, advising standalone treatment (and subagent delegation for cheap asides) instead of re-deriving from full session history |

**Guideline Skills** (category: guideline)

| Skill | Domain |
|-------|--------|
| `git-conventions` | Branch naming, commit messages, workflow patterns |
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

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`, `category`)
2. Name must be lowercase, hyphen-separated, and match the directory name
3. Add `category:` — one of: `process`, `meta`, `guideline`, `protocol`, `enforcement`
4. For workflow skills, add `triggers` with 4-8 short keyword phrases (developer perspective, distinct across skills)
5. For background skills, add `user-invocable: false` to frontmatter
6. Add `references/` directory if the skill needs support docs (templates, rules)
7. Update the skill tables in both `README.md` and this file
8. Update `CHANGELOG.md` under `[Unreleased]`

### Modifying an existing skill

1. Edit the `SKILL.md` directly — the frontmatter `description` is what users see in discovery
2. If changing the skill's purpose or name, update `README.md`, `CLAUDE.md`, and `CHANGELOG.md`
3. Keep instructions concise — use `references/` for lengthy support material

### Conventions

- Skill instructions use progressive disclosure: frontmatter is loaded at startup, full body on activation
- Workflow skills should define clear phases with approval gates where user confirmation is needed
- Background skills should state when they auto-load (e.g., "Auto-loaded when working with TypeScript files")
- Descriptions are single-line and start with an action or noun (not "This skill...")
- Triggers are short (1-4 words), written from the developer's perspective, and distinct across skills

## Project Setup (for consumers)

After installing skills, run `/init` to scaffold project-specific configuration:

```
your-project/
├── .claude/skills/          # Installed skills
├── CLAUDE.md                # Project context (tech stack, conventions)
└── .ai-project/             # Project state (created by /init)
    ├── .memory.md           # Architecture overview
    ├── .context.md          # Patterns and imports
    ├── config.yaml          # Structured settings with defaults
    ├── project/             # Detected project config (commands, structure, stack)
    ├── domains/             # Stack-specific domain rules (*.instructions.md)
    ├── todos/               # Technical debt tracking
    ├── decisions/           # Architecture decision records
    └── history/             # Work history
```
