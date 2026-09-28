---
description: Review changes and create a git commit with a confirmation gate, via `--validate`, `--amend`, `--all`, `--no-gate`. Use when work is ready to commit, changes need staging, or the user says "commit".
argument-hint: "[--validate] [--amend] [--all] [--no-gate]"
---

# Commit

Reviews the current diff and creates one well-formed commit. Unrecognized
flags are an error — report and stop.

## Flags

| Flag | Description |
|------|-------------|
| `--validate` | run the `verifier` gate (typecheck, lint, scoped tests) before committing (default: off) |
| `--amend` | amend the previous commit instead of creating a new one |
| `--all` | stage all tracked modifications (`git add -u`) instead of only the changes identified in the digest |
| `--no-gate` | skip the confirmation prompt (explicit opt-out only) |

Secrets in staged content are blocked by the repo's `PreToolUse` guard hook
on `git commit` — this workflow does not duplicate that scan.

## Workflow

1. **Branch/state check.** `git status --porcelain` and `git branch
   --show-current`. Clean tree → report "Nothing to commit" and exit. On
   `main`/`master`, note it but continue.

2. **Delegate diff analysis.** Dispatch a subagent to gather the diff
   (scoped to `--files=<paths>` if given, else all uncommitted or
   `--staged` changes) and flag mixed concerns (e.g. feature + refactor in
   the same set of files). Return a digest only — file list with one-line
   descriptions, stats, mixed-concern flag — not raw diff text.

3. **Act on the digest.** If mixed concerns are flagged, ask via
   `AskUserQuestion` whether to split into separate commits — this is a real
   decision, not a config default. If uncommitted changes exist and intent
   is otherwise unclear, stage them and ask rather than guessing.

4. **Validate (gated).** If `--validate` is effective, delegate typecheck/
   lint/scoped-test runs to a `verifier` subagent (fall back to
   `general-purpose` if unavailable). Require the exact command, exit code,
   and raw output back; read it before proceeding. A failure stops the
   commit until resolved or the user overrides.

5. **Stage.** `--all` → `git add -u` (tracked modifications only, never
   `-A`/`.`, so untracked files stay out unless named explicitly).
   Otherwise stage only the files identified in scope/digest, by name.
   Verify with `git status` that no unintended files were included.

6. **Confirm.** Unless `--no-gate`, show the suggested commit message and
   require explicit approval (yes/edit/review/cancel) before committing.
   Silence, questions, or "okay" are not approval.

7. **Commit.** `git commit -m "[message]"` (or `git commit --amend -m
   "[message]"` if `--amend`). Never add a `Co-Authored-By` trailer.

8. **Report.** Committed SHA, message, and file count.

## Commit Message Format

```
[type](scope): [short description]

[optional body]

[optional footer: references, breaking changes]
```

| Type | Use |
|------|-----|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Structure change (no behavior change) |
| `test` | Adding/updating tests |
| `docs` | Documentation |
| `chore` | Maintenance, dependencies |
| `perf` | Performance |

- Imperative mood, lowercase after the type/scope prefix, no trailing
  period, subject ≤50 chars, body wrapped at 72.
- Banned: "update code", "fix bug", "changes", "misc", "wip", "stuff".
- `Fixes #123` / `Closes #123` (closes on merge), `Refs #123` (links only).
  If the branch name encodes a ticket (`git-conventions` naming), add
  `Refs TICKET-123` automatically — don't ask each commit.

See `commands/references/commit/commit-conventions.md` for extended formats
(breaking changes, reverts, multi-issue references, scope conventions).
