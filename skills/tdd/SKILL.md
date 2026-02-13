---
name: tdd
description: Strict Test-Driven Development workflow enforcing the RED-GREEN-REFACTOR cycle. Ensures every line of production code is justified by a failing test. Use when building new features, fixing bugs, or adding behavior.
triggers:
  - test first
  - test-driven
  - red green refactor
  - write test before code
---

# TDD

> **Purpose:** Enforce strict Test-Driven Development with verified RED-GREEN-REFACTOR cycles
> **Phases:** RED -> Verify RED -> GREEN -> Verify GREEN -> REFACTOR
> **Usage:** `/tdd <feature or behavior description>`

## Iron Laws

1. **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST** -- Every line of production code must be justified by a test that fails without it. No exceptions. No "just this once."
2. **WRITE THE MINIMUM CODE TO PASS** -- The GREEN phase produces only what the test demands. No extra features, no future-proofing, no refactoring. Just make the red test green.
3. **DELETE AND RESTART IF VIOLATED** -- If production code was written before its test, delete it completely. Then write the test first. There is no shortcut that preserves TDD's guarantees.

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Why TDD for AI Agents

Everything that makes TDD tedious for humans makes it ideal for AI: clear measurable goals per cycle, mechanical verification at each step, and tight feedback loops. Tests serve as natural-language specs that guide the agent toward exactly the behavior you expect.

## When to Use

- Building new features or modules from scratch
- Fixing bugs (write test that reproduces bug first)
- Adding behavior to existing code
- Implementing interfaces or contracts
- Any work where correctness matters more than speed

## When NOT to Use

- Exploratory prototyping (explore first, then delete and TDD) -> `/explore`
- Code already written that needs tests after the fact -> `/test-coverage`
- Refactoring working code with passing tests -> `/refactor`
- Investigating a bug you don't understand yet -> `/debug`
- Configuration or infrastructure files with no testable logic

## Never Do

- **Never keep production code written before its test** -- Delete it. Write the test. Then rewrite the code. The test must fail first or you have no proof it catches anything.
- **Never skip the verify step** -- Running the test and confirming it fails (RED) or passes (GREEN) is not optional. The verify step is what separates TDD from "writing tests."
- **Never mock what you don't own** -- Don't mock third-party libraries or framework internals. Wrap them in your own interface and mock that. See [testing-anti-patterns.md](references/testing-anti-patterns.md).
- **Never test implementation details** -- Test behavior, not how the code achieves it. If refactoring breaks your tests but not your behavior, your tests are wrong.
- **Never write more than one failing test at a time** -- One RED test. Make it GREEN. Refactor. Then write the next test. Multiple failing tests create confusion and split focus.
- **Never refactor during GREEN** -- GREEN means "make it pass." REFACTOR is a separate phase. Mixing them means you can't tell if breakage came from the fix or the cleanup.
- **Never commit with failing tests** -- Every commit must be GREEN. If you can't make it green, revert to the last green state.

## Gate Enforcement

**CRITICAL:** Each phase transition requires verification.

- RED -> Verify RED: Test MUST fail. Failure MUST be for the right reason.
- Verify RED -> GREEN: Test MUST pass after code change.
- GREEN -> Verify GREEN: All tests MUST pass, not just the new one.
- Verify GREEN -> REFACTOR: Only begin cleanup with a fully green suite.

---

## Phase 1: RED -- Write a Failing Test

**Mode:** Test files only -- no production code.

### Step 1.1: Identify the Next Behavior

Break the feature into the smallest testable behavior. One assertion, one concept.

```markdown
## TDD Cycle

**Behavior:** [What the code should do]
**Input:** [What goes in]
**Expected output:** [What comes out]
```

### Step 1.2: Write ONE Minimal Failing Test

```typescript
describe('ModuleName', () => {
  it('should [expected behavior] when [condition]', () => {
    // Arrange: set up inputs and dependencies
    const input = createInput();

    // Act: call the function/method under test
    const result = moduleName.doSomething(input);

    // Assert: verify the expected outcome
    expect(result).toEqual(expectedOutput);
  });
});
```

**Rules:**
- Test name describes **behavior**, not implementation ("should calculate total with tax" not "should call multiply")
- Use real objects over mocks wherever possible
- One logical assertion per test (multiple `expect` calls are fine if they assert one concept)
- The test must reference production code that does not yet exist or does not yet handle this case

### Step 1.3: Confirm Test is Written

```markdown
## RED Phase Complete

**Test file:** `path/to/module.spec.ts`
**Test name:** `should [behavior] when [condition]`
**Asserts:** [what it checks]

Ready to verify this test fails.
```

---

## Phase 2: Verify RED -- Confirm the Test Fails

**Mode:** Read-only verification -- run tests, do not change anything.

### Step 2.1: Run the Test

```bash
npm run test -- path/to/module.spec.ts
```

### Step 2.2: Confirm Failure Reason

**CRITICAL:** The test must fail for the **right reason**.

| Failure Type | Verdict | Action |
|-------------|---------|--------|
| Function not found / module not exported | Valid RED | Proceed to GREEN |
| Assertion fails (wrong return value) | Valid RED | Proceed to GREEN |
| Syntax error in test | Invalid RED | Fix the test, re-run |
| Wrong import path | Invalid RED | Fix the test, re-run |
| Unrelated test fails | Invalid RED | Fix the unrelated failure first |
| Test passes unexpectedly | Invalid RED | The behavior already exists -- write a different test or verify your test actually tests what you think |

```markdown
## RED Verified

**Test result:** FAIL
**Failure reason:** [why it failed]
**Valid failure:** Yes / No
**Action:** Proceed to GREEN / Fix test and re-verify
```

**GATE: Test must fail for a valid reason before proceeding.**

---

## Phase 3: GREEN -- Write Minimum Code to Pass

**Mode:** Production code -- minimal changes only.

### Step 3.1: Write the Simplest Code That Passes

- If the test expects a return value, hardcode it if that makes the test pass
- Do not add error handling the test doesn't require
- Do not add features beyond what the test checks
- Do not refactor, rename, or reorganize

### Step 3.2: Keep It Minimal

| Temptation | Response |
|-----------|----------|
| "I should also handle the edge case" | Write a test for it first |
| "This needs error handling" | Write a test for the error first |
| "I should extract a helper" | Do that in REFACTOR |
| "The variable name is bad" | Rename in REFACTOR |
| "I know what the next test will need" | Write that test first |

```markdown
## GREEN Phase Complete

**File changed:** `path/to/module.ts`
**Change:** [what was added/modified]
**Lines added:** [count]

Ready to verify all tests pass.
```

---

## Phase 4: Verify GREEN -- Confirm All Tests Pass

**Mode:** Read-only verification -- run tests, do not change anything.

### Step 4.1: Run the Test

```bash
npm run test -- path/to/module.spec.ts
```

### Step 4.2: Run Related Tests

```bash
npm run test -- "path/to/directory/"
```

### Step 4.3: Confirm Clean Pass

```markdown
## GREEN Verified

**New test:** PASS
**Related tests:** PASS ({N} tests)
**Clean output:** Yes / No (warnings?)

Ready to refactor.
```

**GATE: ALL tests must pass before proceeding to REFACTOR.**

---

## Phase 5: REFACTOR -- Improve Without Changing Behavior

**Mode:** Production and test code -- behavior must remain identical.

### Step 5.1: Identify Improvements

- Extract duplicated logic into helpers
- Rename variables and functions for clarity
- Simplify conditional logic
- Remove dead code
- Improve test readability
- For utilities with well-defined input/output contracts, consider adding property-based tests (e.g., fast-check) to catch edge cases example-based tests miss

### Step 5.2: Refactor in Small Steps

After each change:

```bash
npm run test -- path/to/module.spec.ts
```

If any test fails, **undo the last change immediately**. Refactoring must never break tests.

### Step 5.3: Verify Final State

```bash
npm run test -- "path/to/directory/"
npm run typecheck
npm run lint
```

```markdown
## REFACTOR Complete

**Changes made:**
- [Refactoring 1]
- [Refactoring 2]

**All tests:** PASS
**Type check:** PASS
**Lint:** PASS

Cycle complete. Ready for next behavior or commit.
```

---

## Common Rationalizations

When tempted to skip TDD, consult this table:

| Rationalization | Rebuttal |
|----------------|----------|
| "Too simple to test" | Simple code breaks. A one-line function with a typo is still a bug in production. |
| "Need exploration first" | Explore freely. Then **delete** the exploration and rebuild with TDD. Exploration code is throwaway. |
| "Tests after achieve same result" | Tests-after verify what the code **IS**. Tests-first verify what the code **SHOULD BE**. Only one of these catches design mistakes. |
| "TDD is dogmatic" | TDD is pragmatic: it finds bugs at write time instead of debug time. Dogma would be following it without evidence. The evidence is overwhelming. |
| "I'll write the test right after" | You won't. And if you do, you can't verify it catches the bug -- because the code already passes. |
| "This is just a config file" | If it can break production, it can have a test. If it can't break production, why are you changing it? |
| "The function is obvious" | Obvious functions get called with non-obvious inputs. The test documents what "obvious" means. |
| "I need to see the implementation shape first" | The test IS the shape. Write what you want to call, then make it work. The test is the first client of your API. |
| "Mocking is too hard for this" | Hard-to-mock means hard-to-test means bad design. Fix the design. The difficulty is the signal. |
| "We're in a hurry" | TDD is faster. Debugging untested code is what wastes time. You're not saving time, you're borrowing it at high interest. |
| "Existing code has no tests" | Start now. Every tested line is one less future debugging session. Don't perpetuate the problem because someone else created it. |

---

## Red Flags -- Stop and Restart

If any of these occur, stop the current cycle and reassess:

1. **You wrote production code before a test** -- Delete the code. Write the test.
2. **The test passes on the first run** -- Your test doesn't test anything new. Rewrite it.
3. **You're not sure why the test fails** -- You don't understand the system well enough. Read the code first.
4. **You added "just one more thing" in GREEN** -- Revert to the last green state. Write a test for the extra thing.
5. **You're mocking more than two dependencies** -- The unit under test has too many collaborators. Refactor the design.
6. **The test name describes implementation** -- "should call database" is wrong. "should return user by email" is right.
7. **You're testing private methods** -- Test the public interface. Private methods are implementation details.
8. **Multiple tests are failing at once** -- You jumped ahead. Revert to last green. One failing test at a time.
9. **You refactored during GREEN** -- Revert. Make it pass first, then clean up.
10. **The test requires complex setup (>15 lines of arrange)** -- The code under test needs a simpler interface. Refactor first.
11. **You're writing tests to match existing code** -- That's `/test-coverage`, not `/tdd`. TDD means the test comes first.
12. **You feel confident enough to skip verification** -- That's exactly when bugs slip through. Run the test.

---

## Example: TDD Cycle for a Bug Fix

### RED

A user reports that `calculateDiscount` returns negative prices for 100% discounts.

```typescript
// discount.spec.ts
describe('calculateDiscount', () => {
  it('should return zero when discount is 100%', () => {
    const result = calculateDiscount(50.00, 100);
    expect(result).toBe(0);
  });
});
```

### Verify RED

```bash
npm run test -- discount.spec.ts
# FAIL: Expected 0, received -50
# Valid failure: the function subtracts beyond zero
```

### GREEN

```typescript
// discount.ts
export function calculateDiscount(price: number, discountPercent: number): number {
  const discounted = price - (price * discountPercent / 100);
  return Math.max(0, discounted);
}
```

### Verify GREEN

```bash
npm run test -- discount.spec.ts
# PASS: 1 test passed
```

### REFACTOR

No refactoring needed for this small change. Run full suite to confirm:

```bash
npm run test -- "src/pricing/"
# PASS: 12 tests passed
```

Commit the fix with its regression test.

---

## Verification Checklist

Before committing, confirm every item:

- [ ] Every production code change has a corresponding test that was written FIRST
- [ ] Every test was verified to FAIL before writing production code
- [ ] Every test was verified to PASS after writing production code
- [ ] No production code exists beyond what the tests require
- [ ] All tests pass (not just the new ones)
- [ ] Type check passes
- [ ] Lint passes
- [ ] Test names describe behavior, not implementation

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know what test to write | Describe the behavior in plain English first. The test is that sentence turned into code. |
| Test is too complex | Break the behavior into smaller pieces. Test each piece separately. |
| Can't make the test pass simply | The design is wrong. Step back. What interface would make this test trivial? Build that interface. |
| Too many mocks needed | The code has too many dependencies. Extract an interface, inject dependencies, or split the unit. |
| Existing code has no tests | Don't retrofit TDD. Use `/test-coverage` to add tests to existing code. Use `/tdd` for new behavior. |
| Feature is unclear | Use `/explore` or `/plan` first. Come back to `/tdd` when you know what to build. |
| Tests pass but behavior is wrong | Your tests don't cover the actual requirements. Write a new test for the failing scenario. |
| Refactoring breaks tests | Undo the refactoring. Refactoring should not change behavior. If it does, you're changing functionality -- write a test first. |

## References

- [Testing Anti-Patterns](references/testing-anti-patterns.md) -- Common testing mistakes and how to avoid them
