---
name: done
description: Close out a session — code review, verifier gate, commit, create or update the PR, record the session outcome, nudge a context compaction. Flag-driven; supports --review/--no-review, --validate/--no-validate, --pr/--no-pr, --dry-run.
category: process
model: sonnet
effort: medium
triggers:
  - done
  - wrap and ship
  - close out ticket
  - finish and PR
  - ship this
  - dry run close out
---

# Done

> **Purpose:** Wrap up a unit of work: review, validate, commit, create/update the PR, record the outcome, nudge compaction — driven entirely by flags given at invocation.
> **Usage:** `/done [--review|--no-review] [--validate|--no-validate] [--pr|--no-pr] [--dry-run]`

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--review` / `--no-review` | `--review` | Run the native `/code-review` gate against the current diff |
| `--validate` / `--no-validate` | `--validate` | Delegate to the `verifier` subagent (fallback `general-purpose`) to run tests/lint/typecheck/build |
| `--pr` / `--no-pr` | `--pr` | Create or update the PR for this branch |
| `--dry-run` | off | Report what each phase would do; no commits, no pushes, no PR writes |

All flags resolve once at invocation — `/done` never asks mid-run which gates to run. An unrecognized flag is reported as an error and the run stops before Phase 0.

## Session State (optional)

`/done` reads, but doesn't require, two files `/start` writes. Every phase below runs the same with or without them — `/done` works standalone on any branch when `/start` never ran.

- `.claude/sessions/<session_id>.json` — `last_validated_sha`, read in Phase 2 to skip re-validation when it already matches the current code; `status` and outcome fields, written in Phase 5.
- `.claude/worktree.json` — presence gates Phase 4 (PR): absent means this branch was never scoped to a dedicated worktree by `/start`, so Phase 4 is skipped with that reason reported.

## Phases

### Phase 0: Assess State
```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo main)
git branch --show-current; git status --short; git log --oneline $MAIN..HEAD
```
No uncommitted changes and no commits ahead of `$MAIN` → report "nothing to close out" and skip to Phase 5.

### Phase 1: Review (`--review`)
Run `/code-review` against the current diff. Fix critical findings (unsafe types, security anti-patterns, missing boundary validation) before continuing; warnings can be documented and deferred. `--no-review` skips straight to Phase 2, noted in the final report.

### Phase 2: Validate (`--validate`)
Compare `last_validated_sha` (from `.claude/sessions/<id>.json`, if present) against current `HEAD` + `git diff HEAD`. A match means this exact code already passed validation this session — skip silently to Phase 3. Otherwise dispatch the `verifier` subagent (fall back to `general-purpose` if unavailable) to run the project's test, lint, typecheck, and build commands, and read its raw command output — not just a pass/fail summary — before treating this gate as passed. `--no-validate` skips the gate, noted in the final report.

### Phase 3: Commit
Invoke `/commit`. Its approval gate is never bypassed by committing directly here. Under `--dry-run`, report what would be committed and stop — no commit, no push, no PR write.

### Phase 4: PR (`--pr`)
```bash
test -f .claude/worktree.json && echo present || echo absent
gh pr view --json number,url,title,state 2>/dev/null
```
No `.claude/worktree.json` → skip this phase, report why. `--no-pr` → skip this phase, report skipped by flag.

Otherwise: push, then —
- **No PR exists** → `gh pr create --draft` (drafted — `/done` is a work-in-progress checkpoint, not a merge signal).
- **PR exists** → `gh pr edit`, rewriting the description fresh (never appended).

Use tickets already known from the session or the user's request; if none is known, omit the ticket section rather than asking. Title: `[component]: description [TICKETS]`. Body: `## Summary` is one prose paragraph in plain language, never a jargon dump; `## What changed` lists up to 5 outcome bullets, never file or variable names; `## Test Plan`/`## Security` appear only when non-obvious; ticket links come last. On update, re-derive `## Summary` for the branch's current state and add bullets only for genuinely new behavior — never let the description accumulate into a changelog. Full title/body template and a worked example: `references/pr-body.md`.

### Phase 5: Session Bookkeeping
```bash
python3 skills/done/scripts/session_log.py --root . done --session <id> --summary "<one-line outcome>"
```
Marks `status: "done"` in `.claude/sessions/<id>.json`, best-effort posts Langfuse scores (`session_outcome` 9), and prints the session's local cost report. No prior session file → the script backfills one (`backfilled: true`) instead of failing. Under `--dry-run`, skip this write and report what it would record.

### Phase 6: Compaction Nudge
Requires the `UserPromptSubmit` hook (`skills/done/hooks/user_prompt_submit.py`) registered via the `update-config` skill. Once registered, the next user message in this session arrives with a note to run `/compact` first — advisory only; there's no mechanism to force it.

## Output

```markdown
## Close-out Summary
### Review — 0 critical issues (or: skipped by flag)
### Validate — verifier passed (or: last_validated_sha matched, or: skipped by flag)
### Commit — `feat: add data export` (SHA abc1234) (or: dry-run, not committed)
### PR — created draft #42 / updated #42 (or: skipped — reason)
### Session — cost $0.42, session_outcome 9
```

## Related Skills

- `/start` — opens the session this skill closes and writes the state files Phase 2/4 read.
- `/code-review` — Phase 1.
- `/commit` — Phase 3, owns its own approval gate.
