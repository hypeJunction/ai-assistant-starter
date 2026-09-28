# AI Assistant Starter

Reusable skills for AI coding assistants, following the [Agent Skills specification](https://agentskills.io/specification).

## Why This Exists

AI coding assistants have gotten native at the things a starter kit used to
paper over — plan mode, code review, exploration. What's left to package is
narrower and sharper:

- **Session lifecycle** skills (`/start`, `/done`, `/stack`) for scoping and closing out work
- **Agent definitions** with fixed model tiers for cost-aware delegation, verification, and auditing
- **Runtime hooks** that enforce mechanical rules for zero tokens instead of prose that's paid for on every turn
- **Template installation** (`/apply-template`) to carry the underlying conventions into a consumer project's own `CLAUDE.md`

See `CLAUDE.md`'s "What Belongs In This Repo" for the six-point test behind
every inclusion and removal here.

## Installation

Skills, the one command, and the three agents are distributed as a single
Claude Code plugin, `ai-assistant-starter`, at `plugins/ai-assistant-starter/`.
Runtime hooks (see "Runtime Hooks" below) ship alongside them — they're
plumbing the plugin wires in, not skills. Install by adding this repo as a
marketplace, then installing the plugin:

```bash
# Clone the repo (as a sibling of your project, or anywhere on disk)
git clone https://github.com/hypefi/ai-assistant-starter.git

# Register this repo as a plugin marketplace
claude plugin marketplace add ./ai-assistant-starter

# Install the plugin (installs every skill, the command, and the agents;
# there is no per-skill selection)
claude plugin install ai-assistant-starter
```

Installing the plugin also wires up its runtime hooks — the consolidated
`guard` `PreToolUse` entrypoint and `prompt-context-router` — so those
protections are active immediately, with no separate setup step.

Skills become available as `/name` commands as soon as the plugin is
installed.

## Skills

| Skill | Purpose |
|-------|---------|
| `/start` | Scope a new work session to a ticket, worktree, and goal via flags; auto-triggers on session start |
| `/done` | Close out a session — code review, verifier gate, commit, create/update the PR, record the outcome, nudge a context compaction |
| `/retro` | Mine session transcripts, cost traces, and tooling usage evidence for evidence-backed CLAUDE.md/skill/config corrections (`--session`/`--cost`/`--tooling`/`--all`) |
| `/stack` | Split a large branch into a resumable series of stacked PRs, one worktree per bucket |
| `/apply-template` | Apply the standardized CLAUDE.md template to an existing installation, with opt-in companion READMEs, hooks, and settings.json env vars |

## Command

| Command | Purpose |
|---------|---------|
| `/commit` | Review the current diff and create one well-formed commit behind a confirmation gate (`--validate`, `--amend`, `--all`, `--no-gate`) |

## Agents

Agent definitions live in `agents/` and are declared in the plugin manifest
directly (`"agents": ["./agents/"]`) — each has a fixed model tier and a
fixed report format, not an instruction telling Claude to delegate.

| Agent | Model | Purpose |
|-------|-------|---------|
| `dispatch` | haiku | Cost-aware task router — runs work on the cheapest capable model/effort, escalating only when the worker signals it's out of depth |
| `verifier` | sonnet | Runs tests, lint, typecheck, build, or any ad-hoc verification command; returns the command, exit code, and raw output |
| `auditor` | sonnet | Mines an evidence source and returns ranked findings plus a proposed config diff; backs `/retro` |

## Runtime Hooks (not skills)

These live under `hooks/<name>/`, not `skills/` — they're plain scripts the
harness invokes directly via `plugins/ai-assistant-starter/hooks/hooks.json`,
never instructions Claude reads or executes. Each `hooks/<name>/README.md`
documents its exact trigger conditions and configuration:

- **guard** — Single `PreToolUse` entrypoint. Reads hook stdin once and dispatches to `destructive-command`, `branch-protection`, `secret-scan` (on `git commit`), `main-shell-run` (advisory notice when a test/lint/build run happens in the main agent's own shell), `cost-guardrail`, and `circuit-breaker`, in that order; most-restrictive decision wins and a `deny` short-circuits everything after it
- **branch-protection** — Blocks force-push, hard reset, branch deletion on protected branches; wrapped by `guard`, still runnable standalone
- **destructive-command-protection** — Blocks `rm -rf /`, `DROP DATABASE`, and other destructive commands; wrapped by `guard`, still runnable standalone
- **cost-guardrail** — Warns or blocks Agent spawns and Bash calls whose historical cost is disproportionate to the cheapest tracked model tier, using baselines `/retro` refreshes; wrapped by `guard`, still runnable standalone
- **context-circuit-breaker** — Warns (never blocks) on subagent fan-out and expensive-call loops; wrapped by `guard`, still runnable standalone
- **prompt-context-router** — Classifies each prompt by task class and topic-pivot on `UserPromptSubmit`, and advises treating clear asides as standalone (with a delegation suggestion for cheap ones); a companion `PostToolUse` hook denies a pivot away from a just-implemented plan until `EnterPlanMode` is called again

## Specification Compatibility

Skills follow the [Agent Skills specification](https://agentskills.io/specification):

- Each skill is a directory containing a `SKILL.md` file with YAML frontmatter
- Required fields: `name` (matches directory name), `description`, `category`
- Progressive disclosure: metadata loaded at startup, full instructions on activation
- Optional `references/` and `assets/` directories for supplementary content

Every skill in this repo is user-invocable — there are no background,
auto-loading skills; reference knowledge that isn't a deliberate,
human-started procedure belongs in `CLAUDE.md` or `docs/` instead (see
`CLAUDE.md`'s "What Belongs In This Repo").

## Updating

```bash
# Pull the latest changes
cd ai-assistant-starter
git pull

# Update the marketplace and the plugin in your project
claude plugin marketplace update ai-assistant-starter
claude plugin update ai-assistant-starter
```

## Further Reading

- [Cost Optimization](docs/cost-optimization.md) — reference setup for reducing Claude Code token/dollar spend (command filtering hooks, model-tier routing, context hygiene)

## Third-Party Notices

This project includes content derived from third-party sources including WCAG 2.1 (W3C, CC BY 4.0), Conventional Commits (CC BY 3.0), and OWASP Top 10 (CC BY-SA 4.0). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for full attribution details.

## License

MIT
