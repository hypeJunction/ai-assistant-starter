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
README.md                        # User-facing documentation
```

## Change Tracking

This repo does not maintain a `CHANGELOG.md`. Nobody reads it, and it goes
stale the moment a change lands without a matching entry. Git commit
history is the changelog: write clear, scoped commit messages, and let
`git log` be the record of what changed and why. Never create or
re-introduce a `CHANGELOG.md` file in this repo, and don't add
changelog-style entries embedded in code comments or other docs either.

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

All skills are distributed as a single Claude Code plugin, `ai-assistant-starter`, at `plugins/ai-assistant-starter/`. It's a manifest over the canonical skill files (symlinks into `skills/`), not a separate copy.

```bash
# Clone the repo
git clone https://github.com/hypefi/ai-assistant-starter.git

# Register this repo as a plugin marketplace, then install the plugin
claude plugin marketplace add ./ai-assistant-starter
claude plugin install ai-assistant-starter
```

There is no per-skill install — `claude plugin install` installs the whole plugin, including its runtime hooks (`branch-protection`, `destructive-command-protection`, `context-circuit-breaker`, `cost-guardrail`, `prompt-context-router`).


## Available Skills

### Workflow Skills (33 total, categories: process + meta)

**Development Workflows**

| Skill | Purpose |
|-------|---------|
| `/start` | Scope a new work session to a ticket, worktree, and goal, auto-triggering on session start |
| `/explore` | Understand code (read-only) |
| `/plan` | Design approach before coding |
| `/implement` | Execute an approved plan — code, self-review, test, validate, commit, close. Selectable modes (`--debug`, `--tdd`, `--scope-locked`, `--pr-iterate`) handle debugging, strict TDD, scope-locked autonomous work, and PR-feedback iteration. |
| `/refactor` | Multi-file changes with tracking |
| `/migrate` | Database/schema migrations with rollback planning |
| `/stack` | Split a large branch into a resumable series of stacked PRs |

**Quality & Testing**

| Skill | Purpose |
|-------|---------|
| `/validate` | Run type check, lint, tests |
| `/test-coverage` | Ensure test coverage for changes |
| `/api-test` | Discover, test, and report on API endpoints |
| `/e2e` | End-to-end testing with Playwright/Cypress |
| `/review` | Review current branch against base; `--quick` mode for use as a sub-step within `/implement` or `/done`
| `/security-review` | Systematic security audit with confidence-based reporting |
| `/accessibility-review` | WCAG 2.1 AA audit with automated + manual checks |

**Git & Release**

| Skill | Purpose |
|-------|---------|
| `/commit` | Review and commit with confirmation |
| `/pr` | Create pull request |
| `/done` | Close out a session — test coverage, review, validation gate, commit, create/update the PR, record the outcome. Works standalone or for a `/start`-opened session.
| `/trash` | Abandon a session — record why, score the outcome in Langfuse, report cost |
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
| `/pivot` | Explicitly pause the current thread and re-enter Plan Mode for a new direction |
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
| `prompt-context-router` | Runtime hook: classifies each prompt by task class and topic-pivot, advising standalone treatment (and subagent delegation for cheap asides) instead of re-deriving from full session history; with a companion PostToolUse hook, denies a pivot away from a just-implemented plan until EnterPlanMode is called again |

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

### Modifying an existing skill

1. Edit the `SKILL.md` directly — the frontmatter `description` is what users see in discovery
2. If changing the skill's purpose or name, update `README.md` and `CLAUDE.md`
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
