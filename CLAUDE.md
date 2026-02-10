# AI Assistant Starter

This repository provides reusable AI coding assistant skills distributed via [skills.sh](https://skills.sh).

## Installation

```bash
# Install all skills
npx skills add hypefi/ai-assistant-starter

# Install a specific skill
npx skills add hypefi/ai-assistant-starter -s commit
```

## Project Setup

After installing skills, run `/init` to scaffold project-specific configuration:
- `CLAUDE.md` — Project context (tech stack, architecture, conventions)
- `.ai-project/` — Todos, decisions, history, file lists

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
