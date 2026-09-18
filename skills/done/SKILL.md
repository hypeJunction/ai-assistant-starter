---
name: done
description: Close out a session opened by /start — commit, create or update the PR, record the session outcome, and nudge a context compaction.
category: process
model: sonnet
effort: medium
triggers:
  - done
  - wrap and ship
  - close out ticket
  - finish and PR
  - ship this
---

# Done

> **Purpose:** Close out a `/start`-scoped session: commit, create/update the PR, record the outcome, nudge compaction.
> **Usage:** `/done`

## Constraints

- Never call `gh pr create` or `gh pr edit` directly — delegate to `/pr`,
  which owns that (`skills/pr/SKILL.md`'s own constraint says nothing else
  should call these directly).
- Never commit without going through `/commit`'s own approval gate.
- This assumes tests/review/validation already happened. If they haven't,
  run `/finish` first — see Related Skills.
- The compaction nudge in Step 4 is advisory, not a guarantee — Claude Code
  has no mechanism for a hook to force `/compact`.

## Workflow

### Step 1: Commit

Invoke the `/commit` skill. It has its own approval gate — do not bypass it
by committing directly here.

### Step 2: PR Lifecycle

```bash
test -f .claude/worktree.json && echo present || echo absent
```

- **No `.claude/worktree.json`** → this session was never scoped by
  `/start` to a dedicated worktree. Skip this step entirely — do not
  create or update a PR. Tell the user the PR step was skipped for this
  reason when reporting the outcome.
- **`.claude/worktree.json` present** → proceed as below.

```bash
gh pr view --json number,url,title,state 2>/dev/null
```

- **No PR exists** → invoke `/pr`'s flow with draft forced
  (`gh pr create --draft`, not a ready-for-review PR — `/done` is a
  work-in-progress checkpoint, not a "ready to merge" signal).
- **PR exists** → `git push`, then update the description via `/pr`'s
  existing "rewrite fresh, don't append" logic
  (`skills/pr/SKILL.md`). Do not touch the PR description any other way.

### Step 3: Session Bookkeeping

Update *this session's own* state file — never a shared pointer, so
concurrent sibling sessions on the same worktree are untouched:

```bash
python3 skills/done/scripts/session_log.py --root . done --session <id> --summary "<one-line outcome>"
```

This marks `status: "done"` in `.claude/sessions/<id>.json` and
best-effort posts three Langfuse scores — `ticket` (categorical, if a
worktree ticket is known), the legacy `session_done` boolean (1), and
`session_outcome` (numeric, **9** for a completed session — see `/trash`
for the counterpart) — using whatever Langfuse credentials are already
configured for the `langfuse-observability` plugin. Never blocks or fails
`/done` if credentials are missing or the post fails; it's logged and kept
local.

The same command then prints a cost report for the session — total USD
cost and token breakdown (input/output/cache read/cache write), computed
from the session's own local JSONL transcript (`~/.claude/projects/<slug>/
<id>.jsonl`), not Langfuse — no network call, no credentials required. If
no transcript file is found for that session id, it prints that the cost
report is unavailable instead of failing. Relay this line to the user as
part of the close-out report.

**If `SESSION_COST_RETRO_THRESHOLD_USD` is set** and the session's cost
exceeds it, the script prints one extra advisory line naming the cost and
threshold. When that line appears, ask the user via `AskUserQuestion`
whether to run `/session-retro` now — never invoke it automatically.

**If this session was never opened with `/start`** (no prior
`.claude/sessions/<id>.json`), `session_log.py done` backfills a record
retroactively instead of failing — it creates one with `started_at` set to
now (the true start time is unknown) and `backfilled: true`, then marks it
done immediately. The CLI prints a line noting the backfill; mention it
when reporting the outcome so it's clear the session's start time is
approximate.

### Step 4: Compaction Nudge (Setup + Behavior)

Requires the `UserPromptSubmit` hook
(`skills/done/hooks/user_prompt_submit.py`) registered in the project's
`.claude/settings.json` — use the `update-config` skill to add it once per
project if missing.

Once registered: the next user message in this session, whatever it says,
arrives with an injected note asking Claude to run `/compact` first. This
fires once per `/done` (the flag clears itself after nudging) and only for
the session that ran `/done` — sibling sessions on the same worktree are
unaffected. This is advisory: Claude Code has no documented way for a hook
to force compaction, so if the assistant doesn't act on the nudge, the user
may need to type `/compact` themselves.

## Related Skills

- `/start` — opens the session this skill closes; also where the worktree
  and session-state files this skill reads/writes are created.
- `/finish` — the heavier pre-`/done` step (tests, review, validation) when
  those haven't run yet this session.
- `/commit` — this skill's Step 1.
- `/pr` — this skill's Step 2; owns all `gh pr create`/`gh pr edit` calls.
- `/trash` — the counterpart when the session is being abandoned instead
  of shipped: same session-state file and cost report, `session_outcome`
  scored 1 instead of 9, no commit/PR step.
- `/session-retro` — offered when Step 3's cost report exceeds
  `SESSION_COST_RETRO_THRESHOLD_USD`.
