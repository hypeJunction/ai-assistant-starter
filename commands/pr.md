---
description: Create or update the PR for the current branch, deriving branch/PR state from session_state.py. Use when work is ready for review, a PR needs its description refreshed, or the user says "open a PR"/"update the PR".
argument-hint: "[--ready] [--no-gate] [--dry-run]"
---

# PR

Creates or updates the PR for the current branch. Unrecognized flags are an
error — report and stop.

## Flags

| Flag | Description |
|------|-------------|
| `--ready` | create as a non-draft PR (default: draft); or, when updating an existing draft PR, mark it ready for review (`gh pr ready`) |
| `--no-gate` | skip the confirmation prompt before pushing/creating/editing |
| `--dry-run` | report the title/body/action that would be taken; no push, create, or edit |

## Workflow

1. **Derive state.** Run `SS publish-plan --root .` (`SS` = `python3
   ${CLAUDE_PLUGIN_ROOT}/scripts/session_state.py`). Read `BRANCH`, `BASE`,
   `TICKET`, `UPSTREAM`, `NEEDS_PUSH`, `PR_ACTION`, and, when present,
   `PR_NUMBER`/`PR_STATE`/`PR_DRAFT`/`PR_URL`. Do not re-derive any of this
   with separate `git`/`gh` calls. Empty `TICKET` means no `worktree.json` —
   omit the ticket section later rather than asking or erroring.

2. **Branch/state check.** If `BRANCH` equals `BASE`, report "Cannot open a
   PR from the base branch" and stop. If `PR_STATE` is `MERGED` or `CLOSED`,
   report that and stop rather than reopening or editing it.

3. **Push if needed.** Under `--dry-run`, skip this step — report that a
   push would happen instead. Otherwise, if `NEEDS_PUSH=1`, `git push`
   (`-u origin <BRANCH>` when `UPSTREAM=none`).

4. **Delegate diff analysis.** Dispatch a subagent to gather the diff
   between `BASE` and `HEAD` and return a digest — file list with one-line
   descriptions and stats, not raw diff text, including total lines changed.
   Delegate the body draft itself to `dispatch` when that total exceeds
   `DONE_DIFF_MODERATE_LINES` (400 by default, same boundary `/done` uses
   for its own `DIFF_CLASS`).

5. **Draft title/body.** Title: `[component]: description [TICKETS]`. Body
   per `commands/references/pr/pr-body.md`: `## Summary` is one
   plain-language paragraph, never a jargon dump; `## What changed` lists up
   to five outcome bullets and never file or variable names; `## Test Plan`
   and `## Security` appear only when non-obvious; ticket links come last,
   omitted entirely when `TICKET` is empty. On `PR_ACTION=update`, re-derive
   `## Summary` fresh for the branch's current state and add bullets only
   for genuinely new behavior — never append, never treat it as a
   changelog.

6. **Confirm.** Unless `--no-gate`, show the drafted title/body and the
   action about to happen (create draft / create ready / update #N / update
   #N and mark ready) and require explicit approval.

7. **Act.**
   - `PR_ACTION=create`: `gh pr create --title "..." --body "..."`, adding
     `--draft` unless `--ready` was passed.
   - `PR_ACTION=update`: `gh pr edit <PR_NUMBER> --title "..." --body
     "..."`; if `--ready` was passed and `PR_DRAFT=1`, follow with `gh pr
     ready <PR_NUMBER>`.
   - Under `--dry-run`, this step is a no-op — step 3 already reported the
     push and no create/edit/ready call happens here.

8. **Report.** PR number, URL, action taken (created draft / created ready /
   updated / updated and marked ready), and whether a push preceded it.

See `commands/references/pr/pr-body.md` for the full title/body template
and a worked example.
