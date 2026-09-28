---
name: done
description: Close out a session as a fixed phase queue — review, verifier gate, commit, PR, outcome — over session_state.py, which sizes the diff and decides which gates it has earned. Invoke as `/done [--review] [--no-review] [--validate] [--no-validate] [--no-pr] [--dry-run]`.
category: process
model: sonnet
effort: low
triggers:
  - done
  - wrap and ship
  - close out ticket
  - finish and PR
  - ship this
---

# Done

Ships a unit of work: review, validate, commit, PR, record. The phase order
is fixed by the machine, not by this document — `/done` cannot commit before
validating or record before committing, because `complete` rejects any phase
that is not the running head.

`SS` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_state.py --root .`
and `<id>` means this session's id. An unrecognized flag is an error: report
it and stop before planning.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--no-review` | off | skip the `/code-review` gate |
| `--review` | off | run it even on a diff too small to have earned it |
| `--no-validate` | off | skip the `verifier` gate |
| `--validate` | off | run it even on a documentation-only diff |
| `--no-pr` | off | skip creating or updating the PR |
| `--dry-run` | off | report what each phase would do; no commit, push, or PR write |

## The machine

```bash
SS plan --session <id> --flow done [--skip review|validate|publish] [--force review|validate]
SS next --session <id>
SS complete --session <id> --phase <phase> --status passed|skipped|failed [--detail "..."]
```

`plan` measures the diff and decides the skips itself, so nothing below
re-checks them. It skips `validate` when `last_validated_sha` already matches
the exact current tree, `publish` when there is no `.claude/worktree.json`,
and every working phase when the tree is clean with no commits ahead of base.

It also sizes the work and hands out only the gates that size has earned: a
`trivial` diff gets no review, and a `docs` diff gets neither review nor
validation, because neither gate can find anything there that the diff itself
does not already show. Class boundaries are `DONE_DIFF_TRIVIAL_LINES` (10),
`DONE_DIFF_SMALL_LINES` (80) and `DONE_DIFF_MODERATE_LINES` (400) lines of
churn; `DONE_REVIEW_ALWAYS=1` and `DONE_VALIDATE_ALWAYS=1` disable the
discretion outright.

Read `plan`'s output — a phase already marked `skipped` is not yours to run,
and the `DIFF_*` and `REVIEW_LEVEL` lines beneath the queue are the inputs
the phases below use. `next` reprints them for the phase it hands out, so no
phase has to re-derive its own parameters.

A phase reported `failed` blocks the flow: `next` and `complete` both refuse
until the flow is re-planned with `--restart` or abandoned with `abort`. Stop
the run there and report why. Once the cause is fixed, a later `/done`
re-plans, and the phases that already passed are re-derived from the tree —
`validate` in particular stays skipped while the code is unchanged.

## Phases

### `review`
`next` prints `REVIEW_LEVEL` and `REVIEW_TARGET` for this phase. Run
`/code-review <REVIEW_LEVEL> <REVIEW_TARGET>` — the level is the machine's,
not yours to raise or lower. Fix critical findings — unsafe types, security
anti-patterns, missing boundary validation — before completing. Warnings may
be documented and deferred. Complete with the finding count as `--detail`.

### `validate`
Dispatch the `verifier` subagent, falling back to `general-purpose`, to run
the project's test, lint, typecheck, and build commands. Read its raw output
before treating the gate as passed; a pass/fail summary is not evidence.
Never run these in this agent's own shell.

On `passed` the machine records the tree fingerprint, so a second `/done` on
unchanged code skips this phase automatically.

### `commit`
Invoke `/commit`. Its approval gate is never bypassed by committing directly
here. Under `--dry-run`, report what would be committed, complete this phase
as `skipped` with `dry-run` as the detail, and let `plan`'s remaining phases
run in report-only form.

### `publish`
`next` prints this phase's parameters — `BRANCH`, `BASE`, `TICKET`,
`NEEDS_PUSH`, `PR_ACTION`, and `PR_NUMBER` when one exists. Push when
`NEEDS_PUSH=1`, then follow `PR_ACTION`: `create` runs `gh pr create --draft`,
because `/done` is a work-in-progress checkpoint and not a merge signal;
`update` runs `gh pr edit <PR_NUMBER>`, rewriting the description fresh rather
than appending. Do not run `gh pr view` to re-derive any of this.

Title is `[component]: description [TICKETS]`. Body: `## Summary` is one
prose paragraph in plain language, never a jargon dump; `## What changed`
lists up to five outcome bullets and never file or variable names;
`## Test Plan` and `## Security` appear only when non-obvious; ticket links
come last. Use tickets already known from `SS status`; omit the section
rather than asking. On update, re-derive `## Summary` for the branch's
current state and add bullets only for genuinely new behavior — a PR
description is not a changelog. Template and worked example:
`references/pr-body.md`.

Delegate the body draft to `dispatch` when `DIFF_CLASS` is `large`; it is
self-contained writing work.

### `record`
The session-context plugin owns the outcome. Invoke the
`session-context:session` skill with `end` so it collects the user's rating,
writes the overview, and posts to Langfuse. Then:

```bash
SS complete --session <id> --phase record --status passed --detail "<one-line outcome>"
```

That marks the session done and prints its local cost report. If the plugin
is not installed, the `SS complete` call alone is the whole phase. Under
`--dry-run`, complete as `skipped`. A `RETRO_SUGGESTED=1` line means the
session cost more than `SESSION_COST_RETRO_THRESHOLD_USD`; offer `/retro`
via `AskUserQuestion` when it appears, and never run it unasked.

With `hooks/user_prompt_submit.py` registered, the next prompt in this
session arrives asking for a `/compact` first. Advisory only — nothing can
force it.

## Output

```markdown
## Close-out
- Diff — 210 lines across 7 files, moderate
- Review — medium, 0 critical (or: skipped, <reason from the queue>)
- Validate — verifier passed (or: skipped, tree already validated)
- Commit — `feat: add data export` abc1234
- PR — draft #42 created (or: skipped, no worktree.json)
- Session — done, $0.42
```

Quote the machine's own skip reasons rather than inventing wording for them.

## Related

`/start` opens the session and writes the worktree state `publish` reads;
`/trash` is the abandon counterpart; `/commit` owns its own approval gate.
