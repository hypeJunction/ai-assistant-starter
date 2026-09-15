---
name: apply-template
description: Apply the AI Assistant Starter CLAUDE.md template (task classification, search-relevance protocol, process hygiene, AI-generated text conventions) to an existing installation, and optionally install companion reference READMEs and the context-circuit-breaker / cost-guardrail enforcement hooks. Use when a project already has skills installed but lacks the standardized CLAUDE.md sections, or to refresh them after a template update.
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
> companion reference READMEs and the context-circuit-breaker / cost-guardrail
> enforcement hooks.
> **Usage:** `/apply-template [--target <path>]`
> **Output:** Updated `CLAUDE.md` (backed up first), any selected
> `docs/README-*.md` files, and — only if opted in — a `context-circuit-breaker`
> and/or `cost-guardrail` `PreToolUse` hook entry in `settings.json` (also
> backed up first).

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
  a narrowly-scoped `settings.json` hook entry per enforcement hook.** The
  two exceptions are the `context-circuit-breaker` hook (Step 5.5) and the
  `cost-guardrail` hook (Step 5.6) — each installed only on explicit request,
  behind the same dry-run/backup/approval gate as everything else. Neither
  touches any other part of `settings.json` (permissions, model, other
  hooks) or `.claude/skills/` content beyond copying that one hook's
  `references/hook.js` — broader hook/settings changes are out of scope (see
  `docs/cost-optimization.md` once installed).

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

### Step 6: Report

Summarize: what was backed up, which sections were applied/refreshed, which
companion READMEs were installed, and whether the circuit-breaker and/or
cost-guardrail hooks were installed. Do not commit — leave staging/committing
to the user or a follow-up `/commit`.

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
