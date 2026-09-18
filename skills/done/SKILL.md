---
name: done
description: Close out a session — test coverage, review, validation gate, commit, create or update the PR, record the session outcome, and nudge a context compaction. Works standalone or for a session opened by /start.
category: process
model: sonnet
effort: medium
triggers:
  - done
  - wrap and ship
  - close out ticket
  - finish and PR
  - ship this
  - wrap up
  - done for now
---

# Done

> **Purpose:** Wrap up a unit of work: cover with tests, review, validate, commit, create/update the PR, record the outcome, nudge compaction.
> **Usage:** `/done`

## Constraints

- **Only ever runs from an explicit user invocation.** No other skill calls
  `/done` on the user's behalf, or should be read as implying it runs next —
  `/implement`'s Close phase, `/pivot`, and every other skill stop after
  their own step and let the user decide. The steps below (test coverage,
  review, validation) are things `/done` does once *it's* been invoked, not
  a reason for anything else to trigger it. The human looks at the diff
  themselves and types `/done` — the internal `/review --quick` in Step 2 is
  a machine check, not a substitute for that.
- Never call `gh pr create` or `gh pr edit` directly — delegate to `/pr`,
  which owns that (`skills/pr/SKILL.md`'s own constraint says nothing else
  should call these directly).
- Never commit without going through `/commit`'s own approval gate.
- Never skip the Step 3 validation gate — see that step for the override
  path if validation genuinely doesn't apply.
- The compaction nudge in Step 6 is advisory, not a guarantee — Claude Code
  has no mechanism for a hook to force `/compact`.

## Workflow

### Step 0: Assess State

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git branch --show-current
git status --short
git log --oneline $MAIN..HEAD
```

**If no uncommitted changes and no commits ahead of base branch:** report "Nothing to close out — working tree is clean and branch is up to date" and skip to Step 4 (Session Bookkeeping) so the session still gets closed cleanly.

### Step 1: Test Coverage

Ensure changed code has test coverage.

1. **Identify changed files:** `git diff --name-only $MAIN..HEAD` and `git diff --name-only`
2. **Check for missing tests:** each changed `.ts`/`.tsx` file should have a corresponding test file.
3. **Create missing tests** covering the changed behavior. If a test cannot be created (no testing framework configured, untestable code pattern, missing test utilities), report this to the user with the reason rather than silently skipping — let them decide whether to proceed without coverage for that file.
4. **Run and fix:** `npm run test -- ChangedComponent`; investigate and fix any failures, then re-run to confirm.

**Exit criteria:** all changed code has tests (or gaps reported to the user), all tests pass.

### Step 2: Review

Invoke `/review --quick` against the current diff. Fix any critical issues (any-typed code, security anti-patterns, missing input validation at boundaries) before proceeding. Warnings can be documented and deferred if the user agrees.

**Exit criteria:** no critical issues remaining.

### Step 3: Validate Gate

Read the current session's validation record and compare it against the code as it stands right now:

```bash
python3 skills/done/scripts/session_log.py --root . show --session <id>   # or equivalent read of .claude/sessions/<id>.json
git rev-parse HEAD
git diff HEAD
```

- **`last_validated_sha` present and matches the current `HEAD` + diff state** → validation already ran against this exact code (via `/validate` finishing cleanly, from this step or from `/implement`/`/commit`/`/pr` earlier in the session) — proceed silently to Step 4.
- **Record missing, or stale (code has changed since it was written)** → stop and ask via `AskUserQuestion`:
  - Run `/validate --full` now (recommended) — then re-check the record and proceed.
  - Proceed anyway — explicit override; note in the close-out report that `/done` shipped without a fresh validation record, and why the user chose to.
  - Cancel.

**Never silently skip this gate, and never auto-run `/validate` without asking first.**

### Step 4: Commit

Invoke the `/commit` skill. It has its own approval gate — do not bypass it by committing directly here.

### Step 5: PR Lifecycle

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

### Step 6: Session Bookkeeping

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
report is unavailable instead of failing (this is the normal case for a
resumed session whose transcript check happens under a new, branched
session id — see `/start`). Relay this line to the user as part of the
close-out report.

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

### Step 7: Compaction Nudge (Setup + Behavior)

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

## Session Exit Options and Summary Template

For the session exit-option decision tree, post-merge verification steps, and session summary template, see `references/finish-options.md`.

## Output Format

```markdown
## Close-out Summary

### Test Coverage
- utility.spec.ts — created, 6 tests passing

### Review
- `/review --quick`: 0 critical issues remaining

### Validation
- Gate: last_validated_sha matched current HEAD+diff — proceeded
  (or: ran `/validate --full` now — passed)

### Commit
- Committed: `feat: add data export feature` (SHA abc1234)

### PR
- Updated existing draft PR #42 (or: skipped — no worktree session)

### Session
- Cost: $0.42 (or: cost report unavailable — no local transcript)
- session_outcome: 9
```

## Related Skills

- `/start` — opens the session this skill closes; also where the worktree
  and session-state files this skill reads/writes are created, and where a
  resumed session gets branched to its own id (see `/start`'s hook).
- `/review` — this skill's Step 2, in `--quick` mode.
- `/validate` — this skill's Step 3 gate.
- `/commit` — this skill's Step 4.
- `/pr` — this skill's Step 5; owns all `gh pr create`/`gh pr edit` calls.
- `/trash` — the counterpart when the session is being abandoned instead
  of shipped: same session-state file and cost report, `session_outcome`
  scored 1 instead of 9, no commit/PR step.
- `/session-retro` — offered when Step 6's cost report exceeds
  `SESSION_COST_RETRO_THRESHOLD_USD`.
