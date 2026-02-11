# AI Assistant Starter

This repository provides reusable AI coding assistant skills following the [Agent Skills specification](https://agentskills.io/specification), distributed via [skills.sh](https://skills.sh).

## Installation

```bash
# Install all skills
npx skills add hypefi/ai-assistant-starter

# Install a specific skill
npx skills add hypefi/ai-assistant-starter -s commit
```

## Skill Format

Each skill is a `skills/<name>/SKILL.md` file with YAML frontmatter (`name`, `description`) per the [Agent Skills spec](https://agentskills.io/specification). Background skills add `user-invocable: false` (a skills.sh extension).

## Project Setup

After installing skills, run `/init` to scaffold project-specific configuration:
- `CLAUDE.md` — Project context (tech stack, architecture, conventions)
- `.ai-project/` — Todos, decisions, history, file lists
- `.ai-project/domains/` — Stack-specific domain rules (auto-detected by `/init`)

## Available Skills

### Workflow Skills (user-invocable via `/name`)

| Skill | Purpose |
|-------|---------|
| `/explore` | Understand code (read-only) |
| `/plan` | Design approach before coding |
| `/implement` | Full workflow: explore → plan → code → test → commit |
| `/debug` | Find and fix bugs |
| `/refactor` | Multi-file changes with tracking |
| `/validate` | Run type check, lint, tests |
| `/cover` | Ensure test coverage for changes |
| `/review` | Review current branch against base |
| `/commit` | Review and commit with confirmation |
| `/pr` | Create pull request |
| `/wrap` | End-of-session cleanup |
| `/hotfix` | Emergency bug fix |
| `/release` | Version bump and changelog |
| `/deps` | Audit and update dependencies |
| `/docs` | Add or improve documentation |
| `/revert` | Safely rollback changes |
| `/sync` | Align documentation with codebase |
| `/add-story` | Create Storybook stories |
| `/create-todo` | Document deferred work |
| `/file-list` | Track files for batch operations |
| `/init` | Bootstrap project configuration |

### Background Skills (auto-loaded)

Domain guidelines, coding standards, and the core execution protocol are loaded automatically when relevant.
