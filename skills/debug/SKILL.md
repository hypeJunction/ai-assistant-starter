---
name: debug
description: Systematic bug investigation and fixing with hypotheses, root cause analysis, regression tests, and verification. Use when encountering bugs, errors, or unexpected behavior.
---

# Debug

> **Purpose:** Systematic bug investigation and fixing
> **Phases:** Reproduce → Analyze → Narrow → Fix → Verify
> **Usage:** `/debug [scope flags] <bug description>`

## Iron Laws

1. **NO FIXES WITHOUT ROOT CAUSE** — Never apply a fix without first identifying and confirming the root cause. Guessing is not debugging.
2. **ANALYZE FIRST, FIX SECOND** — AI excels at analysis but struggles when simultaneously diagnosing and fixing. Complete all analysis before proposing any fix.
3. **EVERY BUG FIX NEEDS A REGRESSION TEST** — A fix without a test is a fix that will break again.
4. **THREE FAILURES MEANS RETHINK** — If 3 fix attempts fail, the bug is a design problem. Stop patching and escalate.

## When to Use

- Bug reports or error messages
- Test failures with unclear cause
- Unexpected runtime behavior
- Performance regressions

## When NOT to Use

- Known fix, just needs implementation → `/implement`
- Adding new functionality → `/implement`
- Investigating code without a bug → `/explore`

## Never Do

- **Never suppress an error to "fix" it** — Catching and ignoring is hiding, not fixing
- **Never fix symptoms instead of root cause** — If the symptom is a null pointer, the root cause is why it's null
- **Never apply a fix you don't understand** — "It works but I don't know why" means it will break again
- **Never make multiple changes at once** — Change one thing, verify, then change the next

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Limit investigation to specific files |
| `--branch=<name>` | Compare against specific branch |

---

## Phase 1: Reproduce

**Mode:** Read-only — gather symptoms and establish reproduction.

### Step 1.1: Gather Symptoms

```markdown
## Bug Investigation

1. **What's happening?** Expected vs. Actual
2. **When does it occur?** Always / Sometimes / Specific conditions
3. **Reproduction steps?**
4. **Recent changes?**
```

**Wait for response.**

### Step 1.2: Establish Minimal Reproduction

Before investigating, identify the smallest possible reproduction case:
- What's the minimal input that triggers the bug?
- Can the bug be reproduced in a test?
- If a test reproduces it, that becomes the regression test.

### Step 1.3: Confirm Understanding

```markdown
**Issue:** [restate problem]
**Conditions:** [when it happens]
**Impact:** [who/what affected]

Is this correct?
```

**GATE: Wait for confirmation.**

---

## Phase 2: Analyze

**Mode:** Read-only — form hypotheses. Do NOT propose fixes yet.

### Step 2.1: Form Hypotheses

```markdown
## Hypotheses

1. **[Hypothesis A]** — Why: [reasoning] — Check: [how to verify]
2. **[Hypothesis B]** — Why: [reasoning] — Check: [how to verify]
```

### Step 2.2: Investigate

Use the debugging decision tree to select strategy:

| Symptom | Strategy |
|---------|----------|
| Error message present | Read stack trace, trace to source |
| Intermittent failure | Suspect race condition, timing, shared state |
| Works locally, fails in CI | Environment difference (env vars, Node version) |
| Worked before a specific date | `git bisect` to find breaking commit |
| Works for some inputs | Boundary analysis around failing input |
| Silent wrong output | Add logging at each transformation step |
| Performance regression | Profile first — don't guess |

### Step 2.3: Compare Working vs. Broken

Search for similar functionality that works correctly. Document differences.

```bash
git log --oneline -20 -- path/to/broken.ts
```

---

## Phase 3: Narrow

**Mode:** Read-only — converge on root cause with user input.

### Step 3.1: Present Analysis

```markdown
## Analysis Results

**Investigated:** [what was checked]
**Eliminated:** [hypotheses ruled out and why]
**Most likely:** [remaining hypothesis with evidence]
```

### Step 3.2: Narrow Focus with User

Ask the user to help eliminate hypotheses:

```markdown
Based on the analysis, I've narrowed to these possibilities:

1. [Hypothesis X] — Evidence: [what supports it]
2. [Hypothesis Y] — Evidence: [what supports it]

Can you help narrow further? (e.g., "it's not X because..." or "check Z")
```

### Step 3.3: Confirm Root Cause

```markdown
## Root Cause

**Location:** `path/to/file.ts:42`
**Problem:** [what's wrong]
**Why:** [explanation]
**Evidence:** [findings that confirm this]

Does this make sense?
```

**GATE: Wait for confirmation before proposing fix.**

---

## Phase 4: Fix

**Mode:** Full access — implement the approved fix.

### Step 4.1: Propose Fix

```markdown
## Fix Plan

**Root Cause:** [brief summary]
**Solution:** [what will change]
**Files:** `path/to/file.ts` — [fix description]
**Regression Test:** Test for [scenario]
**Security impact:** [Does the fix touch input handling, auth, or data access? If yes, verify no security regression]
**Risks:** [any concerns]

---
**Approve fix?** (yes / no / modify)
```

**GATE: Do NOT implement until user approves.**

### Step 4.2: Implement Fix

1. Apply fix — one change at a time
2. Run typecheck after change

### Step 4.3: Add Regression Test

**REQUIRED.** The test should reproduce the bug scenario and assert correct behavior:

```typescript
it('should [correct behavior] when [bug trigger condition]', () => {
  // Arrange: conditions that triggered the bug
  // Act: action that previously failed
  // Assert: correct behavior
});
```

### Escalation Rule

| Attempt | Action |
|---------|--------|
| 1st failure | Re-examine root cause, form new hypothesis |
| 2nd failure | Expand investigation scope, check assumptions |
| 3rd failure | **STOP.** Present architectural concerns. Don't attempt another fix. |

---

## Phase 5: Verify

**Mode:** Testing + git operations.

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
| Related tests | ✓ Pass (N tests) |
| Type check | ✓ Pass |
| Lint | ✓ Pass |

Can you verify the fix works?
```

**GATE: All tests must pass. Wait for user verification.**

### Step 5.3: Commit

Present commit message with root cause explanation and `Fixes #issue` reference.

**GATE: Wait for explicit approval before committing.**

---

## Quick Reference

| Phase | Mode | Gate |
|-------|------|------|
| 1. Reproduce | Read-only | User confirms symptoms |
| 2. Analyze | Read-only | Hypotheses formed |
| 3. Narrow | Read-only | **User confirms root cause** |
| 4. Fix | Full access | **User approves fix plan** |
| 5. Verify | Testing + git | **All tests pass + user confirms** |
