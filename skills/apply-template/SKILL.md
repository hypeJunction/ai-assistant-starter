---
name: apply-template
description: Apply the AI Assistant Starter CLAUDE.md template (task classification, search-relevance protocol, process hygiene, verification/test delegation, scope discipline, repo pre-flight, AI-generated text conventions) to an existing installation, and optionally install companion reference READMEs, the context-circuit-breaker / cost-guardrail enforcement hooks, and verified cost-saving settings.json env vars. Use when a project already has skills installed but lacks the standardized CLAUDE.md sections, or to refresh them after a template update.
category: meta
model: sonnet
effort: medium
triggers:
  - apply template
  - adopt claude.md template
  - install claude.md sections
  - refresh claude.md template
  - rewire docs
---

# Apply Template

> **Purpose:** Merge the standardized CLAUDE.md sections into an existing
> installation without disturbing project-specific content, and offer
> companion reference READMEs, the context-circuit-breaker / cost-guardrail
> enforcement hooks, and verified cost-saving `settings.json` env vars.
> **Usage:** `/apply-template [--target <path>]`
> **Output:** Updated `CLAUDE.md` (backed up first), any selected
> `docs/README-*.md` files, and — only if opted in — a `context-circuit-breaker`
> and/or `cost-guardrail` `PreToolUse` hook entry and/or selected `env` vars
> in `settings.json` (also backed up first).

## Constraints

- **Never write without a diff.** Always run the merge script in dry-run
  mode first, show the user the diff, and only re-run with `--apply` after
  they confirm.
- **Never skip the backup.** `backup-claude-md.sh` runs before any write to
  an existing `CLAUDE.md`.
- **Don't touch content outside the managed marker blocks.** The merge is
  section-scoped (see `references/markers.md`); a project's own conventions
  outside those markers are never modified.
- **Ask before installing companion READMEs** — don't copy all of them by
  default.
- **This skill edits `CLAUDE.md`, `docs/`, and, only if the user opts in,
  a narrowly-scoped `settings.json` hook entry per enforcement hook or a
  selected set of env vars.** The three exceptions are the
  `context-circuit-breaker` hook (Step 5.5), the `cost-guardrail` hook
  (Step 5.6), and the cost-saving env vars (Step 5.7) — each installed only
  on explicit request, behind the same dry-run/backup/approval gate as
  everything else. None touches any other part of `settings.json`
  (permissions, model, other hooks/env keys) or `.claude/skills/` content
  beyond copying that one hook's `references/hook.js` — broader hook/settings
  changes are out of scope (see `docs/cost-optimization.md` once installed).

## Prerequisites

The target project should already have skills installed via
`npx skills add ./ai-assistant-starter` (see root `README.md`). This skill
works even if it doesn't, but its value is wiring the template into a
`CLAUDE.md` that skills like `/finish`, `/review`, and subagent-spawning
skills will actually read.

## Workflow

### Step 0: Refuse to run on this repo itself

Before doing anything else, check whether the target resolves to the
`ai-assistant-starter` source repo (this repo) rather than a downstream
consumer project — e.g. its `package.json` has `"name":
"ai-assistant-starter"`, or it has both a top-level `skills/` directory and
a `CLAUDE.md` mentioning "Agent Skills specification".

This skill and the `npx skills add` install step exist to configure a
*separate* project that consumes these skills — never this repo, which
authors them and already documents itself natively. If the target matches,
stop and tell the user this looks like the skills source repo itself; ask
them to confirm the actual target path (e.g. `--target ../my-project`)
before proceeding.

### Step 1: Locate the target

Default target is `./CLAUDE.md` (current working directory). If the user
passed `--target <path>`, use that instead.

```bash
ls -la <target>/CLAUDE.md 2>/dev/null
```

Tell the user whether an existing `CLAUDE.md` was found and how large it is.

### Step 2: Back up

```bash
skills/apply-template/scripts/backup-claude-md.sh <target>/CLAUDE.md
```

If no file existed, the script reports that and exits cleanly — nothing to
back up. Report the backup path (or its absence) to the user.

### Step 3: Dry-run the merge

```bash
skills/apply-template/scripts/apply-template.sh \
  skills/apply-template/assets/templates/CLAUDE.md.template \
  <target>/CLAUDE.md
```

This prints a unified diff and writes nothing. Show the diff to the user
verbatim (or a summary if it's large) — this is the approval gate.

**GATE: Ask the user to confirm before proceeding**, via `AskUserQuestion` with options:
- **Apply as-is**
- **Trim/adjust first** (editing the template invocation is out of scope —
  tell them to edit `CLAUDE.md` directly after applying, since the merge
  only owns the marker-delimited blocks)
- **Decline**

### Step 4: Apply

```bash
skills/apply-template/scripts/apply-template.sh \
  skills/apply-template/assets/templates/CLAUDE.md.template \
  <target>/CLAUDE.md --apply
```

Confirm the reported section count matches what was shown in the dry run.

### Step 5: Offer companion READMEs

Present the available companion READMEs (see `assets/readmes/`) and ask
which, if any, the user wants installed into `<target>/docs/`:

| File | Covers |
|------|--------|
| `README-cost-optimization.md` | Pointer to the full cost-optimization reference (filtering hooks, model routing, settings.json skeleton) |
| `README-search-relevance.md` | Rationale behind the Search & Relevance Protocol section just applied |
| `README-security-scripts.md` | What this skill's own install scripts do and don't do — useful to hand to a reviewer |

**GATE: Only copy the ones the user selects.** Don't default to "all."

```bash
skills/apply-template/scripts/copy-readmes.sh \
  skills/apply-template/assets/readmes \
  <target>/docs \
  <selected-file-1.md> [<selected-file-2.md> ...]
```

The script skips (does not overwrite) a destination file that already
exists unless the user explicitly asks to overwrite, in which case add
`--force` before the file list.

**If at least one README was actually copied**, add the "Further Reading"
section listing only those files — never the full catalog:

```bash
skills/apply-template/scripts/write-further-reading.sh \
  <target>/CLAUDE.md docs \
  <copied-file-1.md> [<copied-file-2.md> ...]
```

Run without `--apply` first (dry-run diff, same gate as Step 3), then re-run
with `--apply`. **If no READMEs were selected or copied, skip this
sub-step entirely** — do not add a "Further Reading" section pointing at
docs that don't exist.

### Step 5.5: Offer the circuit-breaker hook

Ask the user (`AskUserQuestion`, options **Install** / **Skip**) whether to
install the `context-circuit-breaker` hook — a `PreToolUse` hook that warns
(never blocks) on subagent fan-out and expensive-call loops. See
`skills/context-circuit-breaker/SKILL.md` for what it does and doesn't do.

**GATE: only proceed on explicit "Install."** This is the only step in this
skill that touches `settings.json`; treat it with the same caution as any
other settings/hooks change.

If installed:

1. Copy the hook script:
   ```bash
   mkdir -p <target>/.claude/skills/context-circuit-breaker/references
   cp skills/context-circuit-breaker/references/hook.js \
     <target>/.claude/skills/context-circuit-breaker/references/hook.js
   ```
2. Back up any existing target settings file the same way `CLAUDE.md` is
   backed up (reuse `backup-claude-md.sh <target>/.claude/settings.json` —
   it works on any file path, not just `CLAUDE.md`).
3. Dry-run the merge and show the resulting JSON as the diff/approval gate:
   ```bash
   node skills/apply-template/scripts/merge-settings-hook.js \
     <target>/.claude/settings.json
   ```
4. Only after confirmation, apply it:
   ```bash
   node skills/apply-template/scripts/merge-settings-hook.js \
     <target>/.claude/settings.json --apply
   ```

The merge script only ever adds or confirms the presence of one
`PreToolUse` entry referencing `context-circuit-breaker/references/hook.js`
— it is idempotent and leaves every other key in `settings.json` untouched.

### Step 5.6: Offer the cost-guardrail hook

Ask the user (`AskUserQuestion`, options **Install** / **Skip**) whether to
install the `cost-guardrail` hook — a `PreToolUse` hook that warns or blocks
on `Agent` spawns (and `Bash` calls) whose historical cost is disproportionate
to the cheapest tracked model tier. See `skills/cost-guardrail/SKILL.md` for
what it does and doesn't do, including that it fails open until a
`cost_baselines.json` file exists — installing the hook alone is harmless.

**GATE: only proceed on explicit "Install."** Same caution as Step 5.5 — this
is the only other step in this skill that touches `settings.json`.

If installed:

1. Copy the hook script:
   ```bash
   mkdir -p <target>/.claude/skills/cost-guardrail/references
   cp skills/cost-guardrail/references/hook.js \
     <target>/.claude/skills/cost-guardrail/references/hook.js
   ```
2. Back up any existing target settings file the same way as Step 5.5
   (`backup-claude-md.sh <target>/.claude/settings.json`).
3. Dry-run the merge — this hook needs two matcher entries (`Agent` and
   `Bash`), both pointing at the same command, in one call:
   ```bash
   node skills/apply-template/scripts/merge-settings-hook.js \
     <target>/.claude/settings.json \
     --command "node .claude/skills/cost-guardrail/references/hook.js" \
     --matcher Agent --matcher Bash
   ```
4. Only after confirmation, apply it:
   ```bash
   node skills/apply-template/scripts/merge-settings-hook.js \
     <target>/.claude/settings.json \
     --command "node .claude/skills/cost-guardrail/references/hook.js" \
     --matcher Agent --matcher Bash --apply
   ```
5. Remind the user that the hook is inert until they run
   `/cost-audit`'s baseline-refresh command (see its SKILL.md's "Continuous
   baseline refresh" section) to populate `.claude/cost-audit/cost_baselines.json`,
   and that it defaults to `warn-only` mode (never blocks) until
   `COST_GUARDRAIL_MODE=enforce` is set explicitly.

Same idempotency guarantee as Step 5.5: re-running only confirms presence,
never duplicates an entry, and every other key in `settings.json` is left
untouched.

### Step 5.7: Offer cost-saving env vars

Ask the user (`AskUserQuestion`, `multiSelect: true`) which of these verified,
documented env vars (see `code.claude.com/docs/en/env-vars`) they want added
to `settings.json`'s top-level `env` object. None are forced — only the ones
explicitly selected are installed:

| Var | What it does | Suggested value |
|---|---|---|
| `DISABLE_TELEMETRY` | Turns off telemetry collection | `1` |
| `DISABLE_ERROR_REPORTING` | Turns off error reporting | `1` |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Disables non-essential network calls | `1` |
| `CLAUDE_CODE_FORK_SUBAGENT` | `0` disables fork-mode subagents entirely (no context-inheriting forks, no background scheduling for them); `1` forces fork mode on everywhere including non-interactive/SDK | `0` |
| `BASH_DEFAULT_TIMEOUT_MS` | Default timeout for Bash commands | `120000` |
| `BASH_MAX_TIMEOUT_MS` | Hard cap a command can request | `600000` |
| `BASH_MAX_OUTPUT_LENGTH` | Truncates large Bash output before it reaches the model | `30000` |

**Flag this distinction to the user explicitly:** the first three are
telemetry/network-only and behavior-neutral. `CLAUDE_CODE_FORK_SUBAGENT=0`
and the three `BASH_*` vars change runtime behavior — forks become
unavailable, and commands can now time out or have output truncated that
previously wouldn't have been — so don't bundle these silently with the
telemetry vars.

**GATE: only proceed with the vars explicitly selected.** This is the third
and last step in this skill that touches `settings.json`.

If any are selected:

1. Back up any existing target settings file the same way Steps 5.5/5.6 do:
   ```bash
   skills/apply-template/scripts/backup-claude-md.sh <target>/.claude/settings.json
   ```
2. Dry-run the merge (one `--env KEY=VALUE` per selected var):
   ```bash
   node skills/apply-template/scripts/merge-settings-hook.js \
     <target>/.claude/settings.json \
     --env DISABLE_TELEMETRY=1 --env BASH_DEFAULT_TIMEOUT_MS=120000
   ```
3. Only after confirmation, apply it:
   ```bash
   node skills/apply-template/scripts/merge-settings-hook.js \
     <target>/.claude/settings.json \
     --env DISABLE_TELEMETRY=1 --env BASH_DEFAULT_TIMEOUT_MS=120000 --apply
   ```

The merge script only ever adds or updates the specific `env` keys given,
reporting which were added vs. already present — it never touches
`hooks.PreToolUse` or any other key unless `--command`/`--matcher` are also
passed, and re-running is idempotent.

> **Note on fork mode:** `CLAUDE_CODE_FORK_SUBAGENT` is real and `0` does
> disable fork-mode subagents, but it doesn't change whether a *non-fork*
> subagent (`general-purpose`, `Explore`, a definition-based agent) inherits
> context — those are always isolated regardless of this setting. See
> `docs/cost-optimization.md`'s "Fork mode" section once installed for the
> full explanation before presenting this option to the user.

### Step 5.8: Offer the prompt-context-router hook

Ask the user (`AskUserQuestion`, options **Install** / **Skip**) whether to
install the `prompt-context-router` hook — a `UserPromptSubmit` hook that
classifies each incoming prompt by task class and topic-pivot, and advises
(never blocks, except for two opt-in one-shot-per-session/cycle deny checks —
see below) treating clear asides as standalone — with a delegation
suggestion for cheap ones. See `skills/prompt-context-router/SKILL.md` for
what it does and doesn't do.

This installs **two** hooks that share one state file: the `UserPromptSubmit`
classifier (`hook.js`) and a companion `PostToolUse` hook
(`post-tool-hook.js`) that watches for `ExitPlanMode` followed by a mutating
tool call, so `hook.js` can tell when a prompt pivots away from a plan that
was just implemented.

**GATE: only proceed on explicit "Install."** This step touches
`settings.json`'s `hooks.UserPromptSubmit` and `hooks.PostToolUse` arrays —
same caution as Steps 5.5/5.6.

If installed:

1. Copy both hook scripts:
   ```bash
   mkdir -p <target>/.claude/skills/prompt-context-router/references
   cp skills/prompt-context-router/references/hook.js \
     skills/prompt-context-router/references/post-tool-hook.js \
     <target>/.claude/skills/prompt-context-router/references/
   ```
2. Back up any existing target settings file the same way Steps 5.5/5.6 do
   (`backup-claude-md.sh <target>/.claude/settings.json`).
3. Dry-run the `UserPromptSubmit` merge — this hook needs
   `--event UserPromptSubmit` since it binds a different hook event than the
   `PreToolUse` default:
   ```bash
   node skills/apply-template/scripts/merge-settings-hook.js \
     <target>/.claude/settings.json \
     --command "node .claude/skills/prompt-context-router/references/hook.js" \
     --matcher "*" --event UserPromptSubmit
   ```
4. Dry-run the `PostToolUse` merge — pass `--matcher` once per tool name
   (the same pattern `cost-guardrail` uses for `Agent`/`Bash`), not a single
   regex-alternation string:
   ```bash
   node skills/apply-template/scripts/merge-settings-hook.js \
     <target>/.claude/settings.json \
     --command "node .claude/skills/prompt-context-router/references/post-tool-hook.js" \
     --matcher ExitPlanMode --matcher Edit --matcher Write \
     --matcher NotebookEdit --matcher Bash --event PostToolUse
   ```
5. Only after confirmation, apply both (repeat 3 and 4 with `--apply`
   appended).
6. In the same `AskUserQuestion` call from Step 5.8 (or a follow-up one),
   ask whether `PROMPT_CONTEXT_ROUTER_POST_PLAN_PIVOT_MODE` should be
   `enforce` (recommended default if unset — a pivot away from a
   just-implemented plan gets denied once per plan cycle until
   `EnterPlanMode` is called again) or `warn-only` (advisory only, matching
   `PROMPT_CONTEXT_ROUTER_PIVOT_ARCHITECTURE_MODE`'s default). Only write the
   env var if the user picks `warn-only` — `enforce` needs no explicit
   setting since it's the hook's own default.

Same idempotency guarantee as Steps 5.5/5.6: re-running only confirms
presence under `hooks.UserPromptSubmit`/`hooks.PostToolUse`, never
duplicates an entry, and every other key in `settings.json` (including
`hooks.PreToolUse`) is left untouched.

### Step 6: Report

Summarize: what was backed up, which sections were applied/refreshed, which
companion READMEs were installed, whether the circuit-breaker, cost-guardrail,
and/or prompt-context-router hooks were installed, and which (if any) env
vars were added. Do not commit — leave staging/committing to the user or a
follow-up `/commit`.

## Security Notes

The four scripts in `scripts/` (three dependency-free POSIX shell, one
dependency-free Node script for JSON-aware merging) make no network calls
and are short enough to read end-to-end before running. See
`assets/readmes/README-security-scripts.md` for the specific properties of
each — offer to show the user that file if they ask why it's safe to run.

## Re-running / Updates

Re-running this skill after the template changes upstream is safe: the merge
is idempotent per marker block (replaces the block's own content, never
duplicates it) and always re-backs-up first.
