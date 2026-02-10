---
name: debug
description: Systematic bug investigation and fixing with hypotheses, root cause analysis, regression tests, and verification. Use when encountering bugs, errors, or unexpected behavior.
---

# Debug

> **Purpose:** Systematic bug investigation and fixing
> **Phases:** Understand → Investigate → Fix → Verify
> **Usage:** `/debug [scope flags] <bug description>`

## Gate Enforcement

**CRITICAL:** This workflow requires confirmation before applying fixes.

**Valid approval:** `yes`, `y`, `approved`, `proceed`, `lgtm`, `go ahead`
**Invalid (NOT approval):** Silence, questions, "I see", "okay", "hmm"

**Key gates:**
1. Confirm root cause understanding before proposing fix
2. Approve fix plan before implementation
3. Confirm before committing

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Limit investigation to specific files |
| `--branch=<name>` | Compare against specific branch |

**Examples:**
```bash
/debug --files=src/api/client.ts network timeout errors
/debug --files=src/auth/ login fails with special characters
/debug users can't save their profile
```

---

## Phase 1: Understand

**Mode:** Read-only investigation — gather symptoms and context.

### Step 1.0: Parse Scope

```bash
git branch --show-current
git status --porcelain
```

### Step 1.1: Gather Symptoms

```markdown
## Bug Investigation

1. **What's happening?**
   - Expected: [what should happen]
   - Actual: [what does happen]

2. **When does it occur?**
   - Always / Sometimes / Specific conditions

3. **Reproduction steps?**

4. **Recent changes?**
```

**Wait for response.**

### Step 1.2: Technical Context

Collect error messages, environment details, stack traces, relevant logs.

**Wait for details.**

### Step 1.3: Confirm Understanding

```markdown
## Summary

**Issue:** [restate problem]
**Conditions:** [when it happens]
**Impact:** [who/what affected]

Is this correct?
```

**GATE: Wait for confirmation.**

---

## Phase 2: Investigate

**Mode:** Read-only — form and test hypotheses.

### Step 2.1: Form Hypothesis

```markdown
## Hypothesis

Possible causes:

1. **[Hypothesis A]**
   - Why: [reasoning]
   - Check: [how to verify]

2. **[Hypothesis B]**
   - Why: [reasoning]
   - Check: [how to verify]
```

### Step 2.2: Trace the Bug

```bash
grep -rn "functionName" src/
git log --oneline -10 path/to/file.ts
git blame path/to/file.ts | head -50
```

### Step 2.3: Confirm Root Cause

```markdown
## Root Cause Found

**Location:** `path/to/file.ts:42`
**Problem:** [what's wrong]
**Why:** [explanation]
**Evidence:**
- [Finding 1]
- [Finding 2]

Does this make sense?
```

**GATE: Wait for confirmation.**

---

## Phase 3: Fix

**Mode:** Full access — implement the approved fix.

**Constraints:**
- Actual fixes require user approval first
- Every bug fix must include a regression test

### Step 3.1: Propose Fix

```markdown
## Fix Plan

### Root Cause
[Brief summary]

### Solution
[What will change]

### Files
- `path/to/file.ts` - [fix]

### Regression Test
- Test for [scenario]

### Risks
- [Any concerns]

---
**Approve fix?** (yes / no / modify)
```

**STOP HERE. Do NOT implement the fix until user responds with explicit approval.**

### Step 3.2: Implement Fix

1. Apply fix
2. Run type check to verify

### Step 3.3: Add Regression Test

**REQUIRED:** Every bug fix must include a regression test.

1. Test should reproduce the bug scenario
2. Assert correct behavior after fix

```typescript
it('should [correct behavior] when [bug trigger condition]', () => {
  // Arrange: Set up conditions that triggered the bug
  // Act: Perform the action that previously failed
  // Assert: Verify correct behavior
});
```

---

## Phase 4: Verify

**Mode:** Testing + git operations with user confirmation.

### Step 4.1: Run All Tests

```bash
npm run test -- path/to/file.spec.ts   # Regression test first
npm run test -- [affected-pattern]      # Related tests
npm run typecheck
npm run lint
```

### Step 4.2: Verification Report

```markdown
## Verification

| Check | Status |
|-------|--------|
| Regression test | ✓ Pass |
| Related tests | ✓ Pass ({N} tests) |
| Type check | ✓ Pass |
| Lint | ✓ Pass |

Can you verify the fix works?
```

**GATE: All tests (especially regression test) must pass.**

**Wait for user verification.**

### Step 4.3: Commit

```markdown
## Ready to Commit

**Files changed:**
- `path/to/file.ts` - [fix]
- `path/to/file.spec.ts` - [regression test]

**Message:**
\`\`\`
fix: prevent null pointer in user lookup

Adds null check before accessing user properties.
Includes regression test to prevent recurrence.

Fixes #123
\`\`\`

**Commit?** (yes / no / edit)
```

**STOP HERE. Wait for explicit approval before committing.**

---

## Debugging Tips

| Pattern | Check For |
|---------|-----------|
| Null/undefined | Missing null checks |
| Race condition | Async timing issues |
| State mutation | Unintended side effects |
| Type mismatch | Incorrect type assertions |

## Quick Reference

| Phase | Mode | Gate |
|-------|------|------|
| 1. Understand | Read-only | User confirms symptoms |
| 2. Investigate | Read-only | **User confirms root cause** |
| 3. Fix | Full access | **User approves fix plan** |
| 4. Verify | Testing + git | **All tests pass + user confirms** |
