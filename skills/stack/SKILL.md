---
name: stack
description: Split a large branch into a series of stacked, dependent pull requests using one worktree per bucket, with resumable state and remote-ref-based base branches. Use when a branch is too large for a single PR and needs to become an ordered series of smaller reviewable PRs.
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

> **Purpose:** Manage a stacked-PR series end-to-end with a resumable manifest and correct base branches
> **Phases:** Plan Buckets → Set Up Worktrees → Validate Per Bucket → Open PRs → Advance/Resume
> **Usage:** `/stack <branch to split> --base=<target branch>`

## Iron Laws

1. **NEVER TRUST A LOCAL REF FOR DIVERGENCE OR BASE-BRANCH DECISIONS** — Always `git fetch origin` first and compute against the `origin/*` ref.
2. **ONE WORKTREE PER BUCKET** — Never cherry-pick multiple buckets into the same checkout; a shared checkout can silently mix bucket contents.
3. **NO COMMITS, SELECTORS, OR FILES OUTSIDE THE APPROVED BUCKET PLAN** — If something extra seems needed mid-bucket, add it to `proposed-additions` in the manifest and ask; don't just do it.
4. **EVERY PR BASE IS VERIFIED AFTER CREATION** — `gh pr view --json baseRefName` after `gh pr create`; self-correct if it's wrong rather than leaving it.

## When to Use

- A feature branch has grown too large for one reviewable PR and needs splitting into an ordered series
- Resuming a stacked-PR effort that was interrupted (killed subagent, closed session) and left worktrees or uncommitted work behind

## When NOT to Use

- A single, already-reasonably-scoped PR → `/pr`
- Fixing CI or review feedback on an existing PR → `/implement --pr-iterate`
- Multi-file changes that stay in one PR → `/refactor`

> **Note:** Requires `gh` (GitHub CLI) and `git worktree` support. Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Gate Enforcement

See `ai-assistant-protocol` for valid approval terms and invalid responses.

---

## Phase 0: Resume Check

Before planning anything new, check for an existing `stack-plan.md` in the repo root and for worktrees left over from an interrupted run:

```bash
git worktree list
cat stack-plan.md 2>/dev/null
```

If a manifest exists with buckets not marked `pushed`, or a worktree has uncommitted changes, report exactly what's there and **ask whether to resume, discard, or start over** before doing anything else. Never silently discard a worktree's uncommitted state.

---

## Phase 1: Plan Buckets

### Step 1.1: Fetch and Establish Divergence

```bash
git fetch origin
git merge-base HEAD origin/<base-branch>
git log origin/<base-branch>..HEAD --oneline
```

Report the merge-base and commit count. **Do not proceed on a stale local base ref** — always resolve against `origin/<base-branch>`.

### Step 1.2: Propose the Bucket Split

Group the commits/changes into logical, independently-reviewable buckets. For each bucket, determine: name, one-sentence rationale, files touched, and which prior bucket (if any) it depends on.

Write `stack-plan.md`:

```markdown
# Stack Plan: <branch>

Base: origin/<base-branch>
Merge-base: <sha>

## Buckets

| # | Name | Rationale | Files | Branch | Parent | Worktree | Status |
|---|------|-----------|-------|--------|--------|----------|--------|
| 1 | ... | ... | ... | stack/1-... | origin/<base-branch> | ../wt-stack-1 | pending |
| 2 | ... | ... | ... | stack/2-... | stack/1-... | ../wt-stack-2 | pending |

## proposed-additions
(empty until something extra is found mid-run)
```

**GATE: Present the bucket plan and wait for explicit approval before creating any worktree or branch.**

---

## Phase 2: Set Up Worktrees

For each approved bucket, in order:

```bash
git worktree add ../wt-stack-<n> -b stack/<n>-<name> <parent-branch>
```

Cherry-pick only that bucket's commits into its worktree — no opportunistic extra changes. Update `stack-plan.md` status to `in-progress`, then `committed`, recording the absolute worktree path and commit SHAs.

---

## Phase 3: Validate Per Bucket

**Delegate each check to its own subagent** — run every distinct command via a separate `Agent` call, never directly in the main agent's shell and never bundled into one call. Send independent checks in a single message with multiple tool uses so they run concurrently. Give each subagent its exact command and require full raw output back; read every subagent's output yourself before reporting results. See `ai-assistant-protocol` § Validation Execution.

```bash
npm run typecheck
npm run lint
npm run test
```

Compare against the Phase 1 baseline (pre-existing failures on the base branch) — never report a pre-existing failure as a regression introduced by this bucket. Update `stack-plan.md` status to `validated`.

**GATE: All checks pass (or match pre-existing baseline) before opening the PR for this bucket.**

---

## Phase 4: Open PRs

For each validated bucket, follow the `pr` skill's description conventions, but:

- Base branch is the bucket's `parent` from the manifest, not the repo default branch
- Always open as a **draft**
- After creation, verify: `gh pr view --json baseRefName` — if it doesn't match the manifest's `parent`, fix it with `gh pr edit --base <parent>` and re-verify

Update `stack-plan.md` status to `pushed` with the PR URL.

---

## Phase 5: Advance or Resume

After each bucket is pushed, report status and print the next bucket's plan. If the run is interrupted, Phase 0 picks it back up from the manifest.

```markdown
## Stack Progress

| # | Name | Status | PR |
|---|------|--------|-----|
| 1 | ... | pushed | #123 |
| 2 | ... | pending | — |

**Next:** bucket 2 — [name]. Say "continue" to proceed.
```

## References

- `pr` skill — PR description conventions and title format, reused for each bucket's PR
- `git-conventions` skill — fetch-first rule for divergence and base-branch decisions

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| STK-T1 | Positive | "Split this branch into a stack of PRs" | Skill triggers |
| STK-T2 | Positive | "This branch is too big, break it into a PR series" | Skill triggers |
| STK-T3 | Negative | "Create a PR for this branch" | Does NOT trigger (→ /pr, single PR) |
| STK-T4 | Negative | "Fix CI on PR #42" | Does NOT trigger (→ /iterate-pr) |
| STK-T5 | Boundary | `stack-plan.md` exists with unpushed buckets | Resume flow triggers (Phase 0), not a fresh plan |
| STK-T6 | Boundary | Local `origin/<base>` ref is stale | Blocked until `git fetch origin` reruns divergence check |
