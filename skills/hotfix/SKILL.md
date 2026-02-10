---
name: hotfix
description: Emergency bug fix with abbreviated validation for production issues. Use when production is broken, a critical security vulnerability is discovered, data corruption is occurring, or a user-blocking bug has no workaround.
---

# Hotfix

> **Purpose:** Emergency bug fix with abbreviated validation for production issues
> **Phases:** Triage -> Fix -> Verify -> Deploy
> **Usage:** `/hotfix [scope flags] <issue description>`

## Constraints

- **Minimal fix only** -- one issue, one fix
- **No refactoring** during hotfix
- **No adding features** or code cleanup
- **Never skip type check**
- **Never deploy with failing tests** without explicit user approval
- **Regression test required** for every hotfix

## When to Use

- Production is broken and needs immediate fix
- Critical security vulnerability discovered
- Data corruption or loss occurring
- User-blocking bug with no workaround

**Do NOT use for:**
- Non-urgent bugs (use `/debug` instead)
- Feature requests
- Performance improvements
- Code cleanup

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Known affected files |
| `--ticket=<id>` | Issue/ticket reference |
| `--severity=<level>` | `critical` / `high` (default: critical) |

**Examples:**
```bash
/hotfix --ticket=PROD-123 users cannot login
/hotfix --files=src/auth/ --severity=critical session tokens expiring
/hotfix payment processing failing for credit cards
```

## Workflow

### Phase 1: Triage

**Goal:** Quickly identify root cause -- skip extensive exploration

#### Step 1.1: Gather Symptoms (Fast)

```markdown
## Hotfix Triage

**Issue:** [from user input]
**Severity:** [critical/high]
**Ticket:** [if provided]

### Symptoms
- **What's broken:** [specific behavior]
- **Error message:** [if any]
- **Affected users:** [scope of impact]
- **When started:** [if known]
```

#### Step 1.2: Quick Investigation

```bash
# Check recent changes
git log --oneline -10

# If files known, check recent changes to them
git log --oneline -5 -- [affected-files]

# Search for obvious issues
grep -r "TODO\|FIXME\|HACK" [affected-files]
```

#### Step 1.3: Identify Root Cause

**Keep investigation brief -- this is an emergency.**

```markdown
## Root Cause Identification

**Most likely cause:** [specific issue]
**Evidence:** [what points to this]
**Confidence:** [high/medium]

**Affected files:**
- `path/to/file.ts` - [what's wrong]

**Confirm this is the root cause?** (yes / investigate more)
```

**GATE: Confirm root cause before fixing. Do NOT proceed without explicit user confirmation.**

---

### Phase 2: Fix

**Goal:** Minimal change to fix the issue -- no refactoring

#### Step 2.1: Plan Minimal Fix

```markdown
## Hotfix Plan

> **IMPORTANT:** Hotfixes should be MINIMAL.
> Fix only the immediate issue. Save improvements for later.

**Root cause:** [confirmed cause]

**Minimal fix:**
- `file.ts` line N: [specific change]

**What this fix does:**
[Brief explanation]

**What this fix does NOT do:**
- [ ] Refactoring
- [ ] Performance improvements
- [ ] Additional features
- [ ] Code cleanup

**Approve this minimal fix?** (yes / suggest alternative)
```

**GATE: User must approve fix approach before implementing.**

#### Step 2.2: Implement Fix

```markdown
## Implementing Hotfix

**File:** `path/to/file.ts`
**Change:** [description]
```

Apply the minimal fix.

#### Step 2.3: Add Regression Test

> **REQUIRED:** Every hotfix must include a regression test to prevent recurrence.

```markdown
## Regression Test

**Test file:** `path/to/file.spec.ts`
**Test case:** [describes the bug scenario]
```

```typescript
it('should [not reproduce the bug] when [trigger condition]', () => {
  // Reproduce the exact conditions that caused the bug
  // Assert that the fix prevents it
});
```

**Keep regression test minimal but effective:**
- Test the specific failing scenario
- Use realistic inputs that triggered the bug
- Assert the correct behavior after the fix

#### Step 2.4: Type Check

```bash
npm run typecheck
```

**If type errors:** They must be resolved before proceeding.

---

### Phase 3: Verify

**Goal:** Scoped validation -- only affected code

#### Step 3.1: Run Scoped Tests

```bash
# Type check (required)
npm run typecheck

# Lint (quick)
npm run lint -- [affected-files]

# Regression test (MUST pass)
npm run test -- [regression-test-file]

# Other affected tests
npm run test -- [affected-test-pattern]
```

#### Step 3.2: Verification Report

```markdown
## Hotfix Verification

| Check | Scope | Status |
|-------|-------|--------|
| Type check | Full | Pass / Fail |
| Lint | Affected files | Pass / Fail |
| Regression test | New test | Pass / Fail |
| Affected tests | Existing tests | Pass / Fail (N tests) |

**Manual verification needed:**
- [ ] [Specific thing to verify manually]

**Verification complete?** (yes / found issues)
```

**GATE: All tests (especially the regression test) must pass before deployment.**

**If tests fail:**

```markdown
> **WARNING:**
> Tests failing. This must be resolved before deploying.
>
> **Options:**
> 1. Fix the failing tests
> 2. Adjust the hotfix approach
> 3. Skip tests (DANGEROUS - requires explicit approval)
>
> **How to proceed?**
```

---

### Phase 4: Docs (Optional)

**Goal:** Quick documentation if issue revealed a gap

> **Note:** Keep this lightweight. Hotfixes need to ship fast.

```markdown
## Documentation (Optional)

**Did this issue reveal a documentation gap?**

- `ai` - Update AI context (gotcha, edge case discovered)
- `readme` - Update README (if user-facing)
- `skip` - No docs needed (default for most hotfixes)
```

If `skip` (most common), proceed immediately to deploy.

---

### Phase 5: Deploy

**Goal:** Fast-track commit and PR

#### Step 5.1: Create Hotfix Commit

```markdown
## Hotfix Commit

**Files changed:**
- `path/to/file.ts`

**Commit message:**
```
fix: [brief description]

[HOTFIX] [TICKET-ID if provided]

Root cause: [one line explanation]
```

**Create commit?** (yes / edit)
```

**STOP HERE. Wait for explicit user confirmation before committing.**

```bash
git add [affected-files]
git commit -m "fix: [description]

[HOTFIX] [TICKET-ID]

Root cause: [explanation]"
```

#### Step 5.2: Create PR or Push

**If on feature branch:**

```markdown
## Create Hotfix PR

**Title:** `[HOTFIX] [description]`
**Base:** `main`
**Labels:** `hotfix`, `priority:critical`

**PR Body:**

## HOTFIX

**Issue:** [description]
**Ticket:** [TICKET-ID]

### Root Cause
[Brief explanation]

### Fix
[What was changed]

### Testing
- [x] Type check passing
- [x] Affected tests passing
- [ ] Manual verification: [what to verify]

### Rollback
If issues occur, revert commit [sha].

**Create PR?** (yes / push directly)
```

**If approved:**

```bash
git push -u origin HEAD
gh pr create --title "[HOTFIX] [description]" --body "..." --label hotfix,priority:critical
```

#### Step 5.3: Deployment Notes

```markdown
## Hotfix Ready

**PR:** [URL]
**Branch:** [branch name]
**Commit:** [sha]

### Next Steps
1. Get PR reviewed (expedited)
2. Merge to main
3. Deploy to production
4. Verify fix in production
5. Monitor for regressions

### Rollback Plan
git revert [commit-sha]

**Hotfix complete!**
```

## Post-Hotfix Actions

After the hotfix is deployed:

1. **Create follow-up todo** if the fix is a workaround
2. **Schedule post-mortem** for critical issues
3. **Update documentation** if not done in Phase 4
4. **Verify regression test coverage** -- confirm the regression test adequately covers the bug scenario

## Rules

### Prohibited
- Refactoring during hotfix
- Adding features
- Extensive code cleanup
- Skipping type check
- Deploying with failing tests (without explicit approval)

### Required
- Minimal fix only -- one issue, one fix
- User confirmation of root cause
- User approval of fix approach
- Regression test added for the bug
- Type check must pass
- All tests (including regression) must pass
- Rollback plan documented

### Recommended
- Link to ticket/issue
- Add `[HOTFIX]` label to PR
- Document root cause for post-mortem
- Create follow-up todo for proper fix if hotfix is a workaround
