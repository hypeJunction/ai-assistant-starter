---
name: iterate-pr
description: Iterate on an open PR until CI passes and all review feedback is addressed. Fetches status, categorizes findings by severity, applies fixes, and loops until clean.
category: process
triggers:
  - PR feedback
  - CI failing
  - address review comments
  - fix PR checks
---

# Iterate PR

> **Purpose:** Drive a PR to merge-ready state by fixing CI failures and addressing review feedback
> **Mode:** Read → categorize → fix → push → verify → loop
> **Usage:** `/iterate-pr [PR number or URL]`

## Constraints

- **`gh` CLI required** — Must be authenticated (`gh auth status`)
- **No force push** — Always use regular `git push`
- **Separate commits** — Functional fixes and cosmetic fixes go in separate commits
- **Exit after 3 attempts** at the same failure — escalate to user instead of looping
- **Never dismiss reviews** — Only resolve threads by pushing fixes
- **Never modify CI config** to make checks pass

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Severity Levels

This skill uses the same P0-P3 scale defined in `/review`:

| Level | Action |
|-------|--------|
| P0-P1 | Auto-fix immediately |
| P2 | Auto-fix + flag to user |
| P3 | Present as numbered menu — user picks which to address |

## Workflow

### Phase 0: Preflight

Verify GitHub CLI is authenticated:

```bash
gh auth status
```

If not authenticated, instruct user to run `gh auth login` and abort. Do not proceed with any subsequent phases until authentication is confirmed.

### Phase 1: Fetch PR Status

```bash
# Get PR details
gh pr view [number] --json number,title,state,reviewDecision,statusCheckRollup,url

# Get CI check results
gh pr checks [number]

# Get review comments
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq '.[] | {id, path, line, body, author: .user.login}'

# Get review threads
gh api repos/{owner}/{repo}/pulls/{number}/reviews --jq '.[] | {id, state, body, author: .user.login}'
```

```bash
# Check for merge conflicts
gh pr view [number] --json mergeable,mergeStateStatus --jq '{mergeable, mergeStateStatus}'
```

Present status summary (see templates reference).

**If all CI checks pass and no review comments are pending:** Report "PR is already clean — all checks pass, no pending feedback" and exit.

### Phase 2: Categorize Findings

Group all findings into categories:

**Merge Conflicts (P0 — resolve first):**
- List conflicting files
- Conflicts block all other work and must be resolved before CI fixes or review feedback

**CI Failures:**
- Build errors (typecheck, compilation)
- Lint errors
- Test failures
- Other check failures

**Review Comments:**
- Categorize each by P0-P3 severity
- Group by file for efficient fixing

Present the categorized findings to the user:

```markdown
## Findings Summary

**Conflicts:** X files — must resolve before push
**CI:** X failures (Y build, Z lint, W test)
**Reviews:** X comments (Y P0-P1, Z P2, W P3)

Proceed with fixes?
```

**GATE: User must confirm before fixing.**

### Phase 3: Address Findings

**Resolution order:** Merge conflicts first, then CI failures, then review comments.

**Merge Conflicts (resolve first):**
1. Fetch and rebase or merge the latest base branch: `git fetch origin && git merge origin/[base-branch]`
2. Resolve conflicts in each file
3. For lock files (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`), accept the base branch version and regenerate (`npm install`, `yarn install`, `pnpm install`)
4. Run full validation after conflict resolution to catch issues introduced by the merge
5. If conflicts are complex (non-trivial code conflicts in multiple files), present them to user for guidance before proceeding

**CI Failures (fix with explicit sequence):**
For each CI failure:
1. Read the failure log to understand the exact error
2. Identify the root cause (not just the symptom)
3. Fix the issue locally
4. Run the same check locally to confirm the fix (e.g., if lint failed, run the linter; if tests failed, run the tests)
5. Only after local confirmation, proceed to the next issue

**P0-P1 (auto-fix):**
1. Fix each issue in priority order
2. Run relevant checks locally after each fix
3. Report what was fixed

**P2 (auto-fix + flag):**
1. Fix the issue
2. Notify user: "Fixed P2: [description] — verify this matches your intent"

**P3 (user selection):**
Present as numbered menu:

```markdown
**P3 items — which would you like to address?**

1. [Description] — `file.ts:line`
2. [Description] — `file.ts:line`
3. [Description] — `file.ts:line`

Enter numbers (e.g., "1,3"), "all", or "skip":
```

**GATE: User must select items before proceeding.**

### Phase 4: Local Validation and Push

**Before pushing any fixes, run full local validation:**

```bash
# Run typecheck, lint, and tests
# Use project-specific commands (check package.json scripts)
npm run typecheck   # or equivalent
npm run lint        # or equivalent
npm run test        # or equivalent
```

Do not push code that fails locally. If local validation reveals new issues introduced by the fixes, fix them before proceeding. If a fix cannot be resolved, report to the user and ask for guidance.

**Once validation passes, commit and push:**

Separate commits by type:

```bash
# Conflict resolution (if any)
git add [affected-files]
git commit -m "chore: resolve merge conflicts with [base-branch]"

# Functional fixes (P0-P2, CI failures)
git add [affected-files]
git commit -m "fix: address PR feedback — [summary]

[list of fixes]"

# Cosmetic fixes (P3, style) — only if any were selected
git add [affected-files]
git commit -m "style: address PR style feedback

[list of changes]"

# Push
git push
```

### Phase 5: Verify and Reply

```bash
# Watch CI status
gh pr checks [number] --watch

# Reply to resolved review threads
gh api repos/{owner}/{repo}/pulls/{number}/comments/{id}/replies \
  -f body="Fixed in [commit-sha]."
```

Report results:

```markdown
## Iteration Result

**CI:** ✅ All passing / ❌ X still failing
**Reviews:** X resolved, Y remaining

[Details of any remaining failures]
```

### Phase 6: Loop or Exit

**Iteration limit:** Maximum 3 push-and-check cycles. If CI still fails after 3 iterations, present a summary of all remaining issues and ask user for guidance. Do not continue looping.

**Exit conditions (stop iterating):**
- All CI checks pass AND all review comments addressed
- Same failure persists after 3 fix attempts → escalate to user
- Total iteration count reaches 3 → present summary and escalate to user
- User says stop

**Loop condition:**
- Remaining failures exist AND iteration count < 3 → return to Phase 1

```markdown
## Final Report

**Iterations:** X
**Fixes applied:** Y
**Status:** [Ready for re-review / Escalated / User stopped]

**Commits added:**
- `abc1234` fix: [description]
- `def5678` style: [description]
```

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| ITP-T1 | Positive | "Fix the failing CI checks on my PR" | Skill triggers |
| ITP-T2 | Positive | "Address review feedback on PR #123" | Skill triggers |
| ITP-T3 | Positive | "PR checks are failing" | Skill triggers |
| ITP-T4 | Negative | "Create a new PR" | Does NOT trigger (-> /pr) |
| ITP-T5 | Negative | "Review my code" | Does NOT trigger (-> /review) |
| ITP-T6 | Negative | "Fix the bug in production" | Does NOT trigger (-> /hotfix) |
| ITP-T7 | Boundary | "Fix CI and push" | Triggers (CI fix is primary intent) |
| ITP-T8 | Early-exit | All CI checks pass and no review comments | Reports "PR is already clean" and exits |

## Quick Reference

```
/iterate-pr           → Iterate on current branch's PR
/iterate-pr 123       → Iterate on PR #123
/iterate-pr [url]     → Iterate on PR by URL
```
