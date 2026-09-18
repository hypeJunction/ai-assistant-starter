---
name: trash
description: Abandon the current session — record why it won't be completed or pursued further, score the outcome in Langfuse, and report session cost.
category: process
model: sonnet
effort: low
triggers:
  - trash this session
  - abandon this session
  - scrap this
  - not pursuing this
  - kill this session
  - give up on this
---

# Trash

> **Purpose:** Close out a session that is being abandoned, not shipped — record why, score it, report cost.
> **Usage:** `/trash [reason]`

## Constraints

- **Bookkeeping only.** This skill never touches git, GitHub, or any file
  in the repo on its own — it only writes the session-state JSON and posts
  to Langfuse. It does not commit, push, revert, reset, or delete anything.
- The one exception is Step 2 below, and only with explicit per-run
  approval — never stash without asking, and never `git stash drop` or
  otherwise discard the stash afterward.
- Never call `gh pr create`, `gh pr edit`, `gh pr close`, or any other `gh`
  mutation — this skill does not touch the PR at all. If the PR needs
  closing too, that's a separate, explicit ask.
- A reason is required. If the user invoked `/trash` without one, ask for
  it before proceeding — `session_outcome` and the Langfuse comment both
  depend on it.

## Workflow

### Step 1: Get the Reason

If the user supplied a reason with the invocation (e.g. `/trash wrong
approach, scope changed`), use it as-is. Otherwise ask:

```markdown
Why is this session being abandoned? (one or two sentences — this gets
recorded against the session)
```

**Wait for user response.**

### Step 2: Offer to Stash Uncommitted Work

```bash
git status --porcelain
```

**If uncommitted changes exist**, ask before touching them:

```markdown
There are uncommitted changes:
  [list of modified/untracked files]

Stash them (`git stash push -u`) before closing out this session, so
they're recoverable later? (yes / no)
```

**Wait for user response.**
- **Yes** → `git stash push -u -m "trash: <reason>"`, then report the
  stash ref in the final summary so it's easy to find later.
- **No** → leave the working tree exactly as-is. Do not commit, discard,
  or otherwise touch it.

**If the working tree is clean**, skip this step silently.

### Step 3: Session Bookkeeping

```bash
python3 skills/done/scripts/session_log.py --root . trash --session <id> --reason "<reason>"
```

This reuses `/done`'s session-state file and Langfuse plumbing
(`skills/done/scripts/session_log.py`):

- Marks `status: "trashed"` in `.claude/sessions/<id>.json`, with the
  reason recorded on the record.
- If this session was never opened with `/start` (no prior session
  record), the script backfills one retroactively rather than failing —
  same behavior as `/done`.
- Best-effort posts to Langfuse: the legacy `session_done` boolean (**0**)
  and `session_outcome` (numeric, **1** — the counterpart to `/done`'s
  9), both carrying the reason as the score comment, plus the `ticket`
  categorical score if a worktree ticket is known. Never blocks or fails
  `/trash` if Langfuse credentials are missing or the post fails — it's
  logged and kept local.
- Prints a cost report for the session — total USD cost and token
  breakdown (input/output/cache read/cache write), computed from the
  session's own local JSONL transcript (`~/.claude/projects/<slug>/
  <id>.jsonl`), not Langfuse — no network call, no credentials required.
  Prints that the report is unavailable instead of failing if no
  transcript file is found for that session id.
- **If `SESSION_COST_RETRO_THRESHOLD_USD` is set** and the session's cost
  exceeds it, the script prints one extra advisory line naming the cost
  and threshold. When that line appears, ask the user via
  `AskUserQuestion` whether to run `/session-retro` now — never invoke it
  automatically.

### Step 4: Report

```markdown
**Session:** trashed
**Reason:** [reason]
**Stash:** [stash ref, or "none — working tree was clean / left as-is"]
**Cost:** [the cost-report line printed by the script, or "unavailable — no local transcript found"]
```

## Related Skills

- `/done` — the counterpart when the session is being closed out
  successfully: same session-state file and cost report, `session_outcome`
  scored 9 instead of 1, plus a commit/PR step this skill deliberately
  omits.
- `/start` — opens the session this skill can close out early.
- `/session-retro` — offered when Step 3's cost report exceeds
  `SESSION_COST_RETRO_THRESHOLD_USD`.
