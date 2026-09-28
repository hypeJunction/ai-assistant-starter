---
name: stack
description: Split a large branch into a resumable series of stacked PRs, one worktree per bucket, via `--buckets=<n>` or `--resume`. Use when a branch is too large for a single PR and needs to become an ordered series of smaller reviewable PRs.
category: process
model: sonnet
effort: high
triggers:
  - split into PRs
  - stacked PR
  - stack of PRs
  - break this branch up
  - PR series
---

# Stack

Splits a branch into an ordered series of stacked PRs, each in its own
worktree, tracked in a resumable manifest. `/stack <branch> --base=<target>`
— requires `gh` and `git worktree`. Unrecognized flags are an error — report
and stop.

## Flags

| Flag | Description |
|------|-------------|
| `--buckets=<n>` | target number of stacked PRs (default: propose a split, gate on approval) |
| `--resume` | continue a previously started split from its saved state |

## State

`stack-plan.md` in the repo root, one row per bucket:

```markdown
# Stack Plan: <branch>
Base: origin/<base-branch>
Merge-base: <sha>

## Buckets
| # | Name | Rationale | Files | Branch | Parent | Worktree | Status |
|---|------|-----------|-------|--------|--------|----------|--------|
| 1 | ... | ... | ... | stack/1-... | origin/<base-branch> | ../wt-stack-1 | pending |

## proposed-additions
(empty until something extra is found mid-run)
```

Status per bucket: `pending → in-progress → committed → validated →
pushed`. Base branches are always the bucket's `parent`, resolved from
`origin/*` — never a local ref.

## Workflow

1. **Resume check.** `git worktree list` and `cat stack-plan.md
   2>/dev/null`. If `--resume`, or a manifest has buckets not marked
   `pushed`, or a worktree has uncommitted changes, pick up at the first
   non-`pushed` bucket instead of replanning — never silently discard
   uncommitted state; if `--resume` conflicts with what's on disk, ask
   first. Otherwise go to step 2.

2. **Fetch and establish divergence.**
   ```bash
   git fetch origin
   git merge-base HEAD origin/<base-branch>
   git log origin/<base-branch>..HEAD --oneline
   ```
   Always resolve against `origin/<base-branch>`, never a stale local ref.

3. **Propose buckets.** Group commits into independently reviewable
   buckets (respect `--buckets=<n>` as a target count if given): name,
   rationale, files, parent bucket. Write `stack-plan.md` per the schema
   above. **GATE: wait for explicit approval before creating any worktree
   or branch.**

4. **Set up worktrees.** Per approved bucket, in order:
   `git worktree add ../wt-stack-<n> -b stack/<n>-<name> <parent-branch>`.
   Cherry-pick only that bucket's commits — no opportunistic extras; if
   something extra seems needed, add it to `proposed-additions` and ask.
   Update status `in-progress` → `committed` with worktree path and SHAs.

5. **Validate per bucket.** Delegate each check (typecheck, lint, test) to
   its own `verifier` subagent call (fall back to `general-purpose`),
   never inline or bundled. Require exact command, exit code, and raw
   output back; read it before reporting. Compare against the base
   branch's pre-existing failures — never report one as a new regression.
   Update status `validated`. **GATE: all checks pass (or match baseline)
   before opening the PR.**

6. **Open PRs.** Per validated bucket:
   ```bash
   gh pr create --draft --base <bucket-parent> --title "<title>" --body "<body>"
   gh pr view --json baseRefName
   ```
   Base is always the bucket's `parent`, never the repo default. If the
   verified base doesn't match, `gh pr edit --base <parent>` and
   re-verify. Update status to `pushed` with the PR URL.

7. **Advance or resume.** Report the bucket status table and the next
   bucket's plan. If interrupted, step 1 resumes from the manifest.
