---
name: debug
description: Systematic bug investigation and fixing with hypotheses, root cause analysis, regression tests, and verification. Use when encountering bugs, errors, or unexpected behavior.
---

# Debug

> **Purpose:** Systematic bug investigation and fixing
> **Phases:** Understand → Investigate → Analyze Patterns → Fix → Verify
> **Usage:** `/debug [scope flags] <bug description>`

## Iron Laws

1. **NO FIXES WITHOUT ROOT CAUSE** — Never apply a fix without first identifying and confirming the root cause. Guessing is not debugging.
2. **EVERY BUG FIX NEEDS A REGRESSION TEST** — A fix without a test is a fix that will break again.
3. **THREE FAILURES MEANS RETHINK** — If 3 fix attempts fail, the bug is a design problem, not a code problem. Stop patching and escalate to architectural review.

## When to Use

- Bug reports or error messages
- Test failures with unclear cause
- Unexpected runtime behavior
- Performance regressions

## When NOT to Use

- Known fix, just needs implementation → `/implement`
- Code works but needs restructuring → `/refactor`
- Adding new functionality → `/implement`
- Investigating code without a bug → `/explore`

## Never Do

- **Never suppress an error to "fix" it** — Catching and ignoring is hiding, not fixing
- **Never fix symptoms instead of root cause** — If the symptom is a null pointer, the root cause is why it's null
- **Never apply a fix you don't understand** — "It works but I don't know why" means it will break again
- **Never skip the regression test** — The bug will recur. Write the test.
- **Never make multiple changes at once** — Change one thing, verify, then change the next

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

### Debugging Decision Tree

Use this to select your investigation strategy:

| Symptom | Strategy |
|---------|----------|
| Error message present | Read carefully, trace to source via stack trace |
| Intermittent failure | Suspect race condition, timing, shared mutable state |
| Works locally, fails in CI | Environment difference (env vars, Node version, OS) |
| Worked before a specific date | Use `git bisect` to find the breaking commit |
| Works for some inputs | Boundary analysis — test edge cases around the failing input |
| Silent wrong output | Add logging at each transformation step, compare expected vs actual |
| Performance regression | Profile first — don't guess where time is spent |

---

## Phase 3: Analyze Patterns

**Mode:** Read-only — compare working vs broken code.

### Step 3.1: Find Working Examples

Search the codebase for similar functionality that works correctly:

```bash
grep -rn "similar_pattern" src/
```

### Step 3.2: Compare Working vs Broken

```markdown
## Pattern Analysis

**Working example:** `path/to/working.ts:42`
**Broken code:** `path/to/broken.ts:17`

**Differences:**
1. [Difference 1]
2. [Difference 2]

**Relevant recent changes:**
```

```bash
git log --oneline -20 -- path/to/broken.ts
```

### Step 3.3: Confirm Root Cause

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

## Phase 4: Fix

**Mode:** Full access — implement the approved fix.

**Constraints:**
- Actual fixes require user approval first
- Every bug fix must include a regression test

### Step 4.1: Propose Fix

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

### Step 4.2: Implement Fix

1. Apply fix — one change at a time
2. Run type check to verify

### Step 4.3: Add Regression Test

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

### Escalation Rule

If your fix attempt fails:

| Attempt | Action |
|---------|--------|
| 1st failure | Re-examine root cause, form new hypothesis |
| 2nd failure | Expand investigation scope, check assumptions |
| 3rd failure | **STOP.** The bug is likely a design problem. Present architectural concerns to user before attempting another fix. |

---

## Phase 5: Verify

**Mode:** Testing + git operations with user confirmation.

### Step 5.1: Run All Tests

```bash
npm run test -- path/to/file.spec.ts   # Regression test first
npm run test -- [affected-pattern]      # Related tests
npm run typecheck
npm run lint
```

### Step 5.2: Verification Report

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

### Step 5.3: Commit

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
| Null/undefined | Missing null checks, optional chaining |
| Race condition | Async timing, missing await, shared state |
| State mutation | Unintended side effects, reference vs value |
| Type mismatch | Incorrect type assertions, any casts |
| Import errors | Circular dependencies, wrong paths |
| Environment | Missing env vars, wrong config |

## Quick Reference

| Phase | Mode | Gate |
|-------|------|------|
| 1. Understand | Read-only | User confirms symptoms |
| 2. Investigate | Read-only | Hypotheses formed |
| 3. Analyze Patterns | Read-only | **User confirms root cause** |
| 4. Fix | Full access | **User approves fix plan** |
| 5. Verify | Testing + git | **All tests pass + user confirms** |
