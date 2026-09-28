# AI Assistant Starter

Reusable AI coding assistant skills following the [Agent Skills specification](https://agentskills.io/specification).

## Project Structure

```
skills/                          # All skills live here
├── <name>/
│   ├── SKILL.md                 # Skill definition (frontmatter + instructions)
│   ├── references/              # Optional support docs (templates, detection rules)
│   └── assets/                  # Optional scaffolding templates
commands/                         # Slash commands (frontmatter + instructions, not skills)
agents/                           # Agent definitions (frontmatter: name, description, tools, model)
hooks/                            # Runtime hooks (not skills) — harness-invoked scripts
├── <name>/
│   ├── hook.js                  # Script the harness calls directly via hooks.json
│   └── README.md                # Trigger conditions, config, installation snippet
CLAUDE.md                        # This file (project instructions)
README.md                        # User-facing documentation
```

## What Belongs In This Repo

Before adding anything, check it against these criteria — this is what keeps the repo from re-growing:

1. If a current-generation agent already does it natively, it does not belong here. That is why `plan`, `implement`, `explore`, `review`, `security-review`, `e2e`, `test-coverage`, `validate`, `refactor`, `init`, `sync`, `deps`, and `release` are gone — the harness has native plan mode, `/code-review`, `/security-review`, and does the rest unaided.
2. If it is a rule that can be checked mechanically, it is a hook, not prose. Prose is paid for on every turn and obeyed probabilistically; a hook costs zero tokens and is obeyed always.
3. If it is work with its own context and a fixed output contract, it is an agent definition with an explicit model tier, not an instruction telling Claude to delegate.
4. If it is a procedure a human deliberately starts with options, it is a command with CLI flags — never a chatbot that interrogates the user mid-run.
5. If it is reference knowledge the model genuinely lacks, it is one line in CLAUDE.md or a file in `docs/` that a command points at. Never a background skill.
6. Otherwise it does not exist.

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
category: process             # process | meta
triggers:                      # Intent keywords for auto-routing
  - keyword phrase
  - another phrase
---

# Skill Title

Instructions follow...
```

All current skills are user-invocable — there are no background skills in
this repo (see "What Belongs In This Repo," point 5: reference knowledge
that isn't tied to a deliberate, human-started procedure goes in CLAUDE.md
or `docs/`, not a skill that auto-loads on every relevant turn).

- **Workflow skills**: Triggered via `/name` commands or matched by intent triggers
- `references/` directory: Support docs that guide execution (templates, detection rules)
- `assets/` directory: Scaffolding templates, where a skill needs them

## Installation

All skills are distributed as a single Claude Code plugin, `ai-assistant-starter`, at `plugins/ai-assistant-starter/`. It's a manifest over the canonical skill, command, and agent files (symlinks into `skills/`, `commands/`, and `agents/`), not a separate copy.

```bash
# Clone the repo
git clone https://github.com/hypefi/ai-assistant-starter.git

# Register this repo as a plugin marketplace, then install the plugin
claude plugin marketplace add ./ai-assistant-starter
claude plugin install ai-assistant-starter
```

There is no per-skill install — `claude plugin install` installs the whole
plugin: 5 skills, 1 command (`/commit`), 3 agents (`dispatch`, `verifier`,
`auditor`), and its runtime hooks (`guard` and `prompt-context-router`).

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/start` | Scope a new work session to a ticket, worktree, and goal via flags; auto-triggers on session start |
| `/done` | Close out a session — code review, verifier gate, commit, create/update the PR, record the outcome, nudge a context compaction |
| `/retro` | Mine session transcripts, cost traces, and tooling usage evidence (`--session`/`--cost`/`--tooling`/`--all`) for evidence-backed CLAUDE.md/skill/config corrections |
| `/stack` | Split a large branch into a resumable series of stacked PRs, one worktree per bucket |
| `/apply-template` | Apply the standardized CLAUDE.md template sections to an existing installation, with opt-in companion READMEs, the `guard`/`prompt-context-router` hooks, and cost-saving settings.json env vars |

The one command, `commands/commit.md` (`/commit`), reviews the current diff
and creates a commit behind a confirmation gate, with `--validate`,
`--amend`, `--all`, and `--no-gate` flags.

## Agents

Agent definitions live in `agents/`, are symlinked into
`plugins/ai-assistant-starter/agents/`, and are declared in the plugin
manifest as `"agents": ["./agents/"]`. Each carries an explicit model tier —
this is what point 3 of "What Belongs In This Repo" means by a fixed output
contract instead of a delegation instruction.

| Agent | Model | Purpose |
|-------|-------|---------|
| `dispatch` | haiku | Cost-aware task router — runs work on the cheapest capable model/effort, escalating only when the worker signals it's out of depth |
| `verifier` | sonnet | Runs tests, lint, typecheck, build, or any ad-hoc verification command; returns the command, exit code, and raw output |
| `auditor` | sonnet | Mines an evidence source (session transcripts, cost traces, usage counters) and returns ranked findings plus a proposed diff; backs `/retro` |

## Runtime Hooks

These live under `hooks/<name>/`, not `skills/`. Each is a plain script the
harness invokes directly via `plugins/ai-assistant-starter/hooks/hooks.json` —
never a `SKILL.md` Claude reads or executes. `hooks/<name>/README.md`
documents each one's exact trigger conditions and configuration.

| Hook | Domain |
|-------|--------|
| `guard` | Single `PreToolUse` entrypoint (`matcher: "*"`) that reads hook stdin once and dispatches, in order, to `destructive-command`, `branch-protection`, `secret-scan` (on `git commit`), `main-shell-run` (advisory notice when a test/lint/build runs in the main agent's shell), `cost-guardrail`, and `circuit-breaker` — most restrictive decision wins, `deny` short-circuits the rest |
| `branch-protection` | Blocks force-push, hard reset on protected branches — wrapped by `guard`, also runnable standalone |
| `destructive-command-protection` | Blocks rm -rf, DROP DATABASE, and other destructive commands — wrapped by `guard`, also runnable standalone |
| `cost-guardrail` | Warns/blocks Agent spawns and Bash calls whose historical cost is disproportionate, using cost-baseline data — wrapped by `guard`, also runnable standalone |
| `context-circuit-breaker` | Warns (never blocks) on subagent fan-out and expensive-call loops — wrapped by `guard`, also runnable standalone |
| `prompt-context-router` | Unchanged: classifies each prompt by task class and topic-pivot on `UserPromptSubmit`, advising standalone treatment (and subagent delegation for cheap asides); a companion `PostToolUse` hook denies a pivot away from a just-implemented plan until `EnterPlanMode` is called again |

## Contributing a Skill

A skill is instructions Claude reads and executes. A harness-invoked script
that the plugin's `hooks.json` calls directly — never read by Claude as
instructions — is a **hook**, not a skill. A fixed-model, fixed-output-contract
worker invoked via the `Agent` tool is an **agent**, not a skill either. See
the relevant section below instead.

### Adding a new skill

Before adding one, check it against "What Belongs In This Repo" above —
most candidates turn out to be a hook, an agent, a command flag, or a line
in this file instead.

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`, `category`)
2. Name must be lowercase, hyphen-separated, and match the directory name
3. Add `category:` — `process` or `meta`
4. Add `triggers` with 4-8 short keyword phrases (developer perspective, distinct across skills)
5. Add `references/` directory if the skill needs support docs (templates, rules)
6. Update the skill tables in both `README.md` and this file

### Adding a new agent

1. Create `agents/<name>.md` with frontmatter (`name`, `description`, `tools`, `model`) and a body describing its task, constraints, and report format
2. Symlink `plugins/ai-assistant-starter/agents/<name>.md` to `../../../agents/<name>.md`
3. Update the "Agents" tables in both `README.md` and this file

### Adding a new runtime hook

1. Create `hooks/<name>/hook.js` plus a `hooks/<name>/README.md` documenting
   its trigger conditions, configuration, and installation snippet — no
   Agent Skills frontmatter, since it's never discovered as a skill
2. Register it in `plugins/ai-assistant-starter/hooks/hooks.json` under the
   relevant event/matcher, and symlink `plugins/ai-assistant-starter/hooks/<name>`
   to `../../../hooks/<name>`
3. Update the "Runtime Hooks" tables in both `README.md` and this file

### Modifying an existing skill

1. Edit the `SKILL.md` directly — the frontmatter `description` is what users see in discovery
2. If changing the skill's purpose or name, update `README.md` and `CLAUDE.md`
3. Keep instructions concise — use `references/` for lengthy support material

### Conventions

- Skill instructions use progressive disclosure: frontmatter is loaded at startup, full body on activation
- Workflow skills should define clear phases with approval gates where user confirmation is needed
- Descriptions are single-line and start with an action or noun (not "This skill...")
- Triggers are short (1-4 words), written from the developer's perspective, and distinct across skills
