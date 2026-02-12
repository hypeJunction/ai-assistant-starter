---
name: review
description: Comprehensive code review of the current branch against base. Read-only analysis with P0-P3 severity-rated findings and actionable feedback. Use before merging or to check code quality.
---

# Review

> **Purpose:** Code review of the current branch against the base branch
> **Mode:** Read-only — do NOT modify files, run tests, or make commits
> **Usage:** `/review`

## Iron Laws

1. **READ EVERYTHING BEFORE JUDGING** — Read all changed files before forming any opinion. Early conclusions from partial reading lead to wrong findings.
2. **EVIDENCE, NOT THEORY** — Every P0/P1 finding must include the specific code and a concrete explanation of why it's a real problem, not a hypothetical one.
3. **CLEAN REVIEWS ARE VALID** — If the code is good, say so. Not finding issues is a legitimate review outcome, not a failure to review thoroughly.

## When to Use

- Before merging a PR
- After completing implementation work
- Reviewing someone else's branch
- Quality check before release

## When NOT to Use

- Security-specific concerns → `/security-review`
- Running validation commands → `/validate`
- Making code changes → `/implement` or `/refactor`
- Investigating a bug → `/debug`

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Review specific files instead of full branch diff |
| `--pr=<number>` | Review a specific PR by number |

**Examples:**
```bash
/review                           # Review current branch vs base
/review --files=src/auth/         # Review only auth-related changes
/review --pr=42                   # Review PR #42
```

## Constraints

- **Read-only** — Suggestions only, no modifications
- **Read all changed files** before providing feedback
- **Use P0-P3 severity levels** — see definitions below
- **Provide actionable feedback** with specific file locations
- **Acknowledge good patterns** — not just problems
- **Don't invent issues** — if nothing found at a severity level, say so
- **Evidence required** — every P0/P1 finding must include why this is real, not theoretical

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

### Step 4: Validate Review Scope

Before reviewing, check for edge cases:

- **Empty diff** → Report "No changes found between branches" and exit
- **Large diff (>500 lines changed)** → Warn user and ask: review all files, or focus on specific areas?
- **Mixed-concern changes** (e.g., feature + refactor + config) → Flag as candidate for splitting into separate PRs

### Step 5: Read and Review Each File

For each changed file:
1. Read the full file for context
2. Check against the review checklist
3. Note issues by severity level (P0-P3)

### Step 6: Run Lint Check

```bash
npm run lint
```

List each warning with file location and proposed fix.

### Step 7: Review Checklist

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

#### Escalation Flags

Flag these for explicit discussion even if no bug is found:
- Schema or migration changes
- API contract changes (request/response shape, status codes)
- New dependencies added
- Security-sensitive code (auth, crypto, input handling)
- Infrastructure or CI/CD config changes

### Step 8: Generate Review Report

```markdown
## Code Review: [Branch Name]

### PR Information
- **PR:** #[number] - [title] (if exists)
- **Branch:** [current] → [base]
- **Files Changed:** [count]

### Summary
[Brief overview of what the changes accomplish]

### P0 Critical 🔴
[Must fix before merge — security vulnerabilities, data loss, correctness bugs]

1. **[Issue title]**
   - **Location:** `file.ts:line`
   - **Evidence:** [Why this is a real problem, not theoretical]
   - **Fix:** [Specific remediation]

_(None found — or list findings)_

### P1 High 🟠
[Should fix before merge — logic errors, SOLID violations, performance regressions]

1. **[Issue title]**
   - **Location:** `file.ts:line`
   - **Evidence:** [Why this matters]
   - **Fix:** [Suggested approach]

_(None found — or list findings)_

### P2 Medium 🟡
[Fix in this PR or create follow-up — code smells, maintainability concerns]

1. [Issue] — `file.ts:line` — [suggestion]

_(None found — or list findings)_

### P3 Low 🔵
[Optional — style, naming, minor suggestions]

1. [Suggestion] — `file.ts:line`

_(None found — or list findings)_

### Positive Notes ✅
- [What was done well]
- [Good patterns used]

### Escalation Flags
- [Any flagged items from Step 7, or "None"]

### Files Reviewed
| File | Status | Notes |
|------|--------|-------|
| path/to/file.ts | ✅/🟡/🔴 | Brief note |

### Areas Not Covered
[Anything you couldn't fully verify — e.g., runtime behavior, external API contracts]

### Residual Risks
[Known risks that remain even after fixing all findings — e.g., "auth flow depends on third-party token validation"]

### Conclusion
[Overall assessment]

---
**Recommendation:** [Approve / Request Changes / Needs Discussion]
```

### Step 9: Post-Review Action Menu

After presenting the report, offer:

```markdown
**What would you like to do?**
1. **Fix all** — Apply fixes for all P0-P2 findings
2. **Fix P0-P1 only** — Address critical and high issues only
3. **Fix specific items** — Choose which findings to fix (e.g., "P0.1, P1.2, P2.3")
4. **No changes** — Keep as read-only review
```

**STOP HERE. Wait for user selection.**

If user picks a fix option:
1. Switch from read-only mode
2. Apply fixes in priority order (P0 first, then P1, then P2)
3. Run typecheck and lint after fixes
4. Offer to commit the fixes

## Severity Levels

| Level | Label | When to Use | Examples |
|-------|-------|-------------|---------|
| P0 | 🔴 Critical | Security vulnerability, data loss, correctness bug — must fix before merge | SQL injection, auth bypass, data corruption, crashes |
| P1 | 🟠 High | Logic error, SOLID violation, performance regression — should fix before merge | Race condition, N+1 query, broken error handling |
| P2 | 🟡 Medium | Code smell, maintainability concern — fix in PR or follow-up | Large function, missing types, poor naming |
| P3 | 🔵 Low | Style, naming, minor suggestion — optional | Comment wording, import ordering, whitespace |
