---
name: trash
description: Abandon a session — show exactly what would be lost, discard the branch and worktree behind an explicit confirmation, close any draft PR, and record the outcome through the session-context plugin. Invoke as `/trash [--reason=<text>] [--keep-branch] [--keep-worktree] [--dry-run]`.
category: process
model: sonnet
effort: low
triggers:
  - trash this
  - abandon session
  - throw this away
  - discard branch
  - scrap this work
---

# Trash

The abandon counterpart to `/done`: the work is not shipping, so discard it
and record why. Destructive, and deliberately gated — the `confirm` phase
cannot be auto-skipped, and no branch, worktree, or PR is touched before it
passes.

`SS` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_state.py --root .`
and `<id>` means this session's id. An unrecognized flag is an error: report
it and stop before planning.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--reason=<text>` | — | why this is being abandoned, recorded verbatim |
| `--keep-branch` | off | leave the branch in place; remove only the worktree |
| `--keep-worktree` | off | leave the worktree in place; reset the tree only |
| `--dry-run` | off | report what would be lost and stop before `discard` |

## The machine

```bash
SS plan --session <id> --flow trash
SS next --session <id>
SS complete --session <id> --phase <phase> --status passed|skipped|failed [--detail "..."]
```

`plan` auto-skips `discard` when the tree is already clean with no commits
ahead of base — there is nothing to throw away, and only the record remains.
A phase reported `failed` blocks the flow outright: `next` and `complete`
both refuse afterwards, which is what makes a declined confirmation final.

## Phases

### `assess` — inventory what would be lost
`next` prints the inventory with the phase: `BRANCH`, `BASE`, `WORKTREE`,
`TICKET`, `GOAL`, `DIRTY_FILES`, `UNPUSHED_COMMITS`, `STASHES`, `PR`, then one
`FILE` line per dirty path and one `COMMIT` line per unpushed commit. Report
it as a short list. Run no git or `gh` command to re-derive any of it; `SS
inventory --session <id>` reprints it if it is ever needed again.

### `confirm` — the gate
Ask once with `AskUserQuestion`, offering discard and keep. The question
states `BRANCH`, `WORKTREE`, and the counts from the inventory — never a bare
"are you sure". Anything other than an explicit discard answer
completes this phase as `failed`, which blocks the flow and leaves every
artifact untouched. `--dry-run` completes it as `skipped` with `dry-run` as
the detail and ends the run here.

Take a safety net first, so an abandoned branch is recoverable for the
reflog's lifetime:
```bash
git stash push --include-untracked --message "trash/<ticket>: <reason>" 2>/dev/null || true
```

### `discard` — remove the artifacts
In this order, each step skipped when its flag says so:

```bash
gh pr close <PR_NUMBER> --comment "Abandoned: <reason>"   # only when PR is not `none`
cd <main-checkout>
git worktree remove <WORKTREE> --force                    # only if LINKED_WORKTREE=1, unless --keep-worktree
git branch -D <BRANCH>                                    # unless --keep-branch
```

Never force-push and never touch a protected branch; if the branch to delete
is the repo's default branch, complete this phase as `failed` and report
that instead. Push nothing.

### `record` — outcome
The session-context plugin owns the outcome. Invoke the
`session-context:session` skill with `end`, giving the abandonment and its
reason as the summary so the rating is scored against what actually
happened. Then:

```bash
SS complete --session <id> --phase record --status passed --detail "trashed: <reason>"
```

That marks the session trashed and prints its local cost report. A
`RETRO_SUGGESTED=1` line means the session cost more than
`SESSION_COST_RETRO_THRESHOLD_USD`; offer `/retro` via `AskUserQuestion`
when it appears, and never run it unasked.

## Output

```markdown
## Trashed
- Lost — 3 uncommitted files, 2 unpushed commits (stashed as `trash/CORE-42: ...`)
- PR — #42 closed (or: none)
- Branch — `ft/CORE-42-export` deleted, worktree removed
- Session — trashed, $0.31 — "approach superseded by CORE-58"
```

## Related

`/done` is the ship counterpart, `/start` opens the session this closes, and
`/retro` is where an abandoned session's cost is worth mining.
