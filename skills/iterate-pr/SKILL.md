---
name: iterate-pr
description: Iterate on an open PR until CI passes and all review feedback is addressed. Fetches status, categorizes findings by severity, applies fixes, and loops until clean.
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

## Severity Levels

This skill uses the same P0-P3 scale defined in `/review`:

| Level | Action |
|-------|--------|
| P0-P1 | Auto-fix immediately |
| P2 | Auto-fix + flag to user |
| P3 | Present as numbered menu — user picks which to address |

## Workflow

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

Present status summary (see templates reference).

### Phase 2: Categorize Findings

Group all findings into categories:

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

**CI:** X failures (Y build, Z lint, W test)
**Reviews:** X comments (Y P0-P1, Z P2, W P3)

Proceed with fixes?
```

**STOP HERE. Wait for user confirmation before fixing.**

### Phase 3: Address Findings

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

**STOP HERE. Wait for user selection.**

### Phase 4: Commit and Push

Separate commits by type:

```bash
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

**Exit conditions (stop iterating):**
- All CI checks pass AND all review comments addressed
- Same failure persists after 3 fix attempts → escalate to user
- User says stop

**Loop condition:**
- Remaining failures exist AND attempt count < 3 → return to Phase 1

```markdown
## Final Report

**Iterations:** X
**Fixes applied:** Y
**Status:** [Ready for re-review / Escalated / User stopped]

**Commits added:**
- `abc1234` fix: [description]
- `def5678` style: [description]
```

## Quick Reference

```
/iterate-pr           → Iterate on current branch's PR
/iterate-pr 123       → Iterate on PR #123
/iterate-pr [url]     → Iterate on PR by URL
```
