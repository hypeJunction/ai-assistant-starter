---
name: apply-template
description: Apply the AI Assistant Starter CLAUDE.md template (task classification, search-relevance protocol, process hygiene, AI-generated text conventions) to an existing installation, and optionally install companion reference READMEs. Use when a project already has skills installed but lacks the standardized CLAUDE.md sections, or to refresh them after a template update.
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
> companion reference READMEs.
> **Usage:** `/apply-template [--target <path>]`
> **Output:** Updated `CLAUDE.md` (backed up first) plus any selected
> `docs/README-*.md` files.

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
- **This skill only edits `CLAUDE.md` and `docs/`.** It never modifies
  `settings.json`, hooks, or `.claude/skills/` — those are separate,
  heavier-weight changes (see `docs/cost-optimization.md` once installed) and
  are out of scope here.

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

### Step 6: Report

Summarize: what was backed up, which sections were applied/refreshed, which
companion READMEs were installed. Do not commit — leave staging/committing
to the user or a follow-up `/commit`.

## Security Notes

All three scripts in `scripts/` are dependency-free POSIX shell, make no
network calls, and are short enough to read end-to-end before running. See
`assets/readmes/README-security-scripts.md` for the specific properties of
each — offer to show the user that file if they ask why it's safe to run.

## Re-running / Updates

Re-running this skill after the template changes upstream is safe: the merge
is idempotent per marker block (replaces the block's own content, never
duplicates it) and always re-backs-up first.
