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
best-effort posts a Langfuse score (ticket + `session_done`) using
whatever Langfuse credentials are already configured for the
`langfuse-observability` plugin — never blocks or fails `/done` if
credentials are missing or the post fails; it's logged and kept local.

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
