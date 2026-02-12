# Hotfix Templates

All markdown output templates for the hotfix workflow phases.

---

## Triage: Symptoms Gathering (Step 1.1)

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

## Triage: Root Cause Identification (Step 1.3)

```markdown
## Root Cause Identification

**Most likely cause:** [specific issue]
**Evidence:** [what points to this]
**Confidence:** [high/medium]

**Affected files:**
- `path/to/file.ts` - [what's wrong]

**Confirm this is the root cause?** (yes / investigate more)
```

---

## Fix Plan (Step 2.1)

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

## Fix: Implementation Status (Step 2.2)

```markdown
## Implementing Hotfix

**File:** `path/to/file.ts`
**Change:** [description]
```

## Fix: Regression Test (Step 2.3)

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

---

## Verification Report (Step 3.2)

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

## Verification: Test Failure Warning

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

## Docs Prompt (Phase 4)

```markdown
## Documentation (Optional)

**Did this issue reveal a documentation gap?**

- `ai` - Update AI context (gotcha, edge case discovered)
- `readme` - Update README (if user-facing)
- `skip` - No docs needed (default for most hotfixes)
```

---

## Deploy: Commit (Step 5.1)

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

## Deploy: PR (Step 5.2)

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

## Deploy: Completion (Step 5.3)

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
