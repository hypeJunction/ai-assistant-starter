---
name: review
description: Comprehensive code review of the current branch against base. Read-only analysis with severity-rated findings and actionable feedback. Use before merging or to check code quality.
---

# Review

> **Purpose:** Code review of the current branch against the base branch
> **Mode:** Read-only — do NOT modify files, run tests, or make commits
> **Usage:** `/review`

## Constraints

- **Read-only** — Suggestions only, no modifications
- **Read all changed files** before providing feedback
- **Use severity levels** (Critical/Warning/Suggestion) appropriately
- **Provide actionable feedback** with specific file locations
- **Acknowledge good patterns** — not just problems

## Workflow

### Step 1: Gather Branch Context

```bash
git branch --show-current
MAIN_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
gh pr view --json number,title,body,baseRefName,url 2>/dev/null
```

### Step 2: Get the Diff

```bash
# If PR exists
gh pr diff

# If no PR, diff against base
git diff $MAIN_BRANCH...HEAD --stat
git diff $MAIN_BRANCH...HEAD
```

### Step 3: Identify Changed Files

```bash
git diff $MAIN_BRANCH...HEAD --name-only
```

Categorize by type: source code, tests, config files.

### Step 4: Read and Review Each File

For each changed file:
1. Read the full file for context
2. Check against the review checklist
3. Note issues by severity level

### Step 5: Run Lint Check

```bash
npm run lint
```

List each warning with file location and proposed fix.

### Step 6: Review Checklist

#### Code Quality
- [ ] No `any` types (TypeScript)
- [ ] Proper type usage
- [ ] Correct import organization
- [ ] No `var` declarations
- [ ] No lint warnings

#### Testing
- [ ] Test coverage for new code
- [ ] Meaningful test descriptions
- [ ] Proper async handling

#### Security
- [ ] No XSS vulnerabilities
- [ ] Input validation present
- [ ] No sensitive data exposed
- [ ] No hardcoded secrets

#### Performance
- [ ] No obvious bottlenecks
- [ ] Efficient data fetching

#### General
- [ ] No `console.log` in production code
- [ ] Error handling present
- [ ] No dead code or unused imports

### Step 7: Generate Review Report

```markdown
## Code Review: [Branch Name]

### PR Information
- **PR:** #[number] - [title] (if exists)
- **Branch:** [current] → [base]
- **Files Changed:** [count]

### Summary
[Brief overview of what the changes accomplish]

### Critical Issues 🔴
[Must fix before merge]
1. [Issue] — **Location:** file.ts:line — **Fix:** [how]

### Warnings 🟡
[Should fix, not blocking]
1. [Issue] — **Location:** file.ts:line — **Suggestion:** [approach]

### Suggestions 🔵
[Nice to have]
1. [Improvement] — **Location:** file.ts:line

### Positive Notes ✅
- [What was done well]
- [Good patterns used]

### Files Reviewed
| File | Status | Notes |
|------|--------|-------|
| path/to/file.ts | ✅/🟡/🔴 | Brief note |

### Conclusion
[Overall assessment]

---
**Recommendation:** [Approve / Request Changes / Needs Discussion]
```

## Severity Levels

| Level | When | Examples |
|-------|------|---------|
| 🔴 Critical | Must fix | Security vulnerabilities, breaking changes without tests, `any` types |
| 🟡 Warning | Should fix | Style violations, missing tests, suboptimal patterns |
| 🔵 Suggestion | Nice to have | Refactoring opportunities, alternative approaches |
