# Debug Mode

**Discipline:** Systematic root-cause analysis before any fix, with mandatory regression tests and escalation after 3 failed attempts.

## Iron Laws

1. **NO FIXES WITHOUT ROOT CAUSE** — Never apply a fix without first identifying and confirming the root cause. Guessing is not debugging.
2. **ANALYZE FIRST, FIX SECOND** — Complete all analysis before proposing any fix.
3. **EVERY BUG FIX NEEDS A REGRESSION TEST** — A fix without a test is a fix that will break again.
4. **THREE FAILURES MEANS RETHINK** — If 3 fix attempts fail, stop patching and escalate.

## Workflow: 5 Phases

### Phase 1: Reproduce

**Goal:** Gather symptoms and establish a minimal reproduction case.

1. **Gather symptoms:** Expected vs. actual behavior, when it occurs, reproduction steps, recent changes
2. **Establish minimal reproduction:** Identify the smallest input that triggers the bug; express it as a test if possible
3. **Confirm understanding:** Restate the problem, conditions, and impact

**GATE:** Wait for user confirmation of symptoms before proceeding.

### Phase 2: Analyze

**Goal:** Form hypotheses and investigate root cause (read-only — no fixes yet).

1. **Form hypotheses:** List candidate explanations with supporting reasoning and how to verify each
2. **Investigate using context-aware strategy:**
   - Load debugging references based on failure category (see table below)
   - Use the debugging decision tree to select investigation strategy
   
   | Failure Category | Strategy |
   |---|---|
   | Test failures / flaky tests | Check for test polluters (isolation violations, shared state) — see `references/debugging-techniques.md` (Test Polluter Detection) |
   | Logic errors / wrong output | Use backward tracing from the incorrect output — see `references/root-cause-tracing.md` (Backward Tracing) |
   | Type errors | Check for type mismatches, null/undefined issues |
   | API integration issues | Verify request/response contracts, error handling |
   | Security-related bugs | Check input validation, auth, data access |
   | Performance issues | Profile to find bottlenecks (don't guess) |
   | Database / ORM errors | Check schema drift, migration state, connection setup — see `references/debugging-techniques.md` (Schema Drift Detection) |

   | Symptom | Strategy |
   |---------|----------|
   | Error message present | Read stack trace, trace to source |
   | Intermittent failure | Suspect race condition, timing, shared state |
   | Works locally, fails in CI | Check environment differences (env vars, Node version) |
   | Production-only failure | Check database schema/migration state, env vars, connection strings, Node.js version, dependency versions, server logs |
   | Worked before a specific date | Use `git bisect` to find breaking commit |
   | Works for some inputs | Boundary analysis around failing input |
   | Silent wrong output | Add logging at each transformation step |
   | Performance regression | Profile first — don't guess |

3. **Compare working vs. broken:** Search for similar functionality that works correctly; document differences

### Phase 3: Narrow

**Goal:** Converge on root cause with user input.

1. **Present analysis:** Document what was investigated, hypotheses ruled out, most likely remaining hypothesis with evidence
2. **Ask user to eliminate hypotheses:** Present remaining candidates with supporting evidence; ask which to rule out or which additional checks to run
3. **Confirm root cause:** Once converged, state location, problem, explanation, and supporting evidence

**GATE:** Wait for explicit user confirmation of root cause before proposing fix.

### Phase 4: Fix

**Goal:** Implement the approved fix with regression test.

1. **Propose fix plan:** Summarize root cause, solution, files to change, regression test scenario, any security/risk concerns
   **GATE:** Wait for user approval before implementing.

2. **Implement fix:** Apply one change at a time, then invoke `/validate typecheck` after each change to catch errors early. Validate at multiple layers — see `references/defense-in-depth.md` for four-layer validation and related code audit.

3. **Add regression test (REQUIRED):** Test must reproduce the bug scenario and assert correct behavior:
   ```typescript
   it('should [correct behavior] when [bug trigger condition]', () => {
     // Arrange: conditions that triggered the bug
     // Act: action that previously failed
     // Assert: correct behavior
   });
   ```

4. **Escalation rule:**
   | Attempt | Action |
   |---------|--------|
   | 1st failure | Re-examine root cause, form new hypothesis |
   | 2nd failure | Expand investigation scope, check assumptions |
   | 3rd failure | STOP. Present architectural concerns. Don't attempt another fix. |

   **Escalation report (on 3rd failure):**
   - Bug description
   - Hypotheses tested and evidence for/against each
   - Remaining theories not yet ruled out
   - Suggested next steps
   - Architectural concerns (why this may be a design problem)

### Phase 5: Verify

**Goal:** Confirm fix is correct and no regressions were introduced.

1. **Run validation tests:** Invoke `/validate` with flags for:
   - Regression test (the test you wrote)
   - Related tests in the same module/area
   - Full typecheck
   - Lint checks

2. **Verification report:**
   | Check | Status |
   |-------|--------|
   | Regression test | ✓ Pass |
   | Related tests | ✓ Pass (N tests) |
   | Type check | ✓ Pass |
   | Lint | ✓ Pass |

3. **External verification:** Ask user to confirm fix works outside the test environment

**GATE:** All tests must pass. Wait for user verification before committing.

## Summary

| Phase | Purpose | Gate |
|-------|---------|------|
| 1. Reproduce | Establish minimal reproduction | User confirms symptoms |
| 2. Analyze | Form and test hypotheses | Hypotheses formed |
| 3. Narrow | Converge on root cause | **User confirms root cause** |
| 4. Fix | Implement approved fix with regression test | **User approves fix plan** |
| 5. Verify | Run all tests, user verifies externally | **All tests pass + user confirms** |
