# TDD Mode

**Discipline:** Strict Test-Driven Development enforcing the RED-GREEN-REFACTOR cycle. Every line of production code must be justified by a failing test.

## Iron Laws

1. **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST** — Every line of production code must be justified by a test that fails without it. No exceptions.
2. **WRITE THE MINIMUM CODE TO PASS** — The GREEN phase produces only what the test demands. No extra features, no future-proofing, no refactoring.
3. **DELETE AND RESTART IF VIOLATED** — If production code was written before its test, delete it completely. Then write the test first.

## Workflow: Decompose → RED → Verify RED → GREEN → Verify GREEN → REFACTOR (per behavior)

### Phase 0: Setup — Decompose and Plan

**Goal:** Break the feature into testable behaviors; create a test roadmap.

1. **Decompose into testable behaviors (not methods):**
   - A behavior is a single observable outcome: "When [condition], it should [result]"
   - Methods may have multiple behaviors — happy paths, edge cases, error cases are separate
   - Decompose complex behaviors into simpler ones until each fits one assertion

   | # | Behavior | Expected |
   |---|----------|----------|
   | 1 | When [condition], it should [result] | [expected output] |
   | 2 | When [condition], it should [result] | [expected output] |

2. **Create test file with roadmap:** Before the first RED phase, create the test file with `describe` block and planned tests as skipped/todo:
   ```typescript
   describe('ModuleName', () => {
     it.todo('behavior 1');
     it.todo('behavior 2');
     it.todo('behavior 3');
   });
   ```
   Run the file to confirm it loads (all tests show as todo/skipped). This file is your session plan.

### Phase 1: RED — Write a Failing Test

**Goal:** Write one minimal failing test for the next behavior.

1. **Pick the next behavior** from your decomposition. Replace its `it.todo` entry with a real test.

2. **Write ONE minimal failing test:**
   - Test name describes **behavior**, not implementation ("should calculate total with tax" not "should call multiply")
   - Use real objects over mocks wherever possible
   - One logical assertion per test (multiple `expect` calls are fine if they assert one concept)
   - The test must reference production code that does not yet exist or does not yet handle this case

   ```typescript
   it('should [expected behavior] when [condition]', () => {
     // Arrange: set up inputs and dependencies
     const input = createInput();
     // Act: call the function/method under test
     const result = moduleName.doSomething(input);
     // Assert: verify the expected outcome
     expect(result).toEqual(expectedOutput);
   });
   ```

3. **Confirm test is written** — Ready to verify it fails.

### Phase 2: Verify RED — Confirm the Test Fails for the Right Reason

**Goal:** Ensure the test fails before you write any code (proof that it catches the missing behavior).

1. **Run the test:** Invoke `/validate` with test file flag

2. **Confirm failure reason (CRITICAL):**
   | Failure Type | Verdict | Action |
   |-------------|---------|--------|
   | Function not found / module not exported | Valid RED | Proceed to GREEN |
   | Assertion fails (wrong return value) | Valid RED | Proceed to GREEN |
   | Syntax error in test | Invalid RED | Fix the test, re-run |
   | Wrong import path | Invalid RED | Fix the test, re-run |
   | Unrelated test fails | Invalid RED | Fix the unrelated failure first |
   | Test passes unexpectedly | Invalid RED | The behavior already exists — write a different test or verify your test actually tests what you think |

**GATE:** Test must fail for a valid reason before proceeding to GREEN.

### Phase 3: GREEN — Write Minimum Code to Pass

**Goal:** Write the simplest code that passes the test.

1. **Write the simplest code that passes:**
   - If the test expects a return value, hardcode it if that makes the test pass
   - Do not add error handling the test doesn't require
   - Do not add features beyond what the test checks
   - Do not refactor, rename, or reorganize

   | Temptation | Response |
   |-----------|----------|
   | "I should also handle the edge case" | Write a test for it first |
   | "This needs error handling" | Write a test for the error first |
   | "I should extract a helper" | Do that in REFACTOR |
   | "The variable name is bad" | Rename in REFACTOR |

### Phase 4: Verify GREEN — Confirm All Tests Pass

**Goal:** Ensure your change passes the new test AND doesn't break anything else.

1. **Run your test:** Invoke `/validate` with test file flag
2. **Run related tests:** Invoke `/validate` with related module/directory flag
3. **Confirm clean pass:** New test PASS, related tests PASS, no warnings

**GATE:** ALL tests must pass before proceeding to REFACTOR.

### Phase 5: REFACTOR — Improve Without Changing Behavior

**Goal:** Clean up code while keeping all tests passing.

1. **Identify improvements:**
   - Extract duplicated logic into helpers
   - Rename variables and functions for clarity
   - Simplify conditional logic
   - Remove dead code
   - Improve test readability

2. **Refactor in small steps:** After each change, run tests. If any test fails, undo immediately.

3. **Verify final state:** Invoke `/validate` with module directory and typecheck/lint flags

4. **Track progress:** Report "Behavior N/M: [description] — COMPLETE"

## Commit Frequency

Commit at natural TDD boundaries:
1. **After completing each behavior cycle** for complex features (significant logic or multiple files)
2. **After every 2-3 cycles** for simpler features (straightforward, single-file changes)
3. **Always commit before starting a risky refactor** — ensure the current green state is committed first

Commit messages reference the behavior:
- `test: add PriceCalculator subtotal calculation`
- `refactor: extract shared pricing helpers`

Never commit with failing tests. Every commit must be GREEN.

## Common Rationalizations

When tempted to skip TDD, consult this table (see `references/tdd-rationalizations.md` for deeper analysis with real-world scenarios):

| Rationalization | Rebuttal |
|----------------|----------|
| "Too simple to test" | Simple code breaks. A one-line function with a typo is still a bug in production. |
| "Need exploration first" | Explore freely. Then **delete** the exploration and rebuild with TDD. |
| "Tests after achieve same result" | Tests-after verify what the code **IS**. Tests-first verify what the code **SHOULD BE**. |
| "TDD is dogmatic" | TDD is pragmatic: it finds bugs at write time instead of debug time. |
| "I'll write the test right after" | You won't. And you can't verify it catches the bug. |
| "This is just a config file" | If it can break production, it can have a test. |
| "The function is obvious" | Obvious functions get called with non-obvious inputs. |
| "I need to see the implementation shape first" | The test IS the shape. The test is the first client of your API. |
| "Mocking is too hard for this" | Hard-to-mock means bad design. The difficulty is the signal. |
| "We're in a hurry" | TDD is faster. Debugging untested code wastes time. |

## Red Flags — Stop and Restart

If any of these occur, stop and reassess:

1. **You wrote production code before a test** — Delete the code. Write the test.
2. **The test passes on the first run** — Your test doesn't test anything new. Rewrite it.
3. **You're not sure why the test fails** — You don't understand the system well enough. Read the code first.
4. **You added "just one more thing" in GREEN** — Revert to the last green state.
5. **You're mocking more than two dependencies** — The unit under test has too many collaborators. Refactor the design.
6. **The test name describes implementation** — "should call database" is wrong. "should return user by email" is right.
7. **You're testing private methods** — Test the public interface.
8. **Multiple tests are failing at once** — You jumped ahead. Revert to last green. One failing test at a time.
9. **You refactored during GREEN** — Revert. Make it pass first, then clean up.
10. **The test requires complex setup (>15 lines)** — The code under test needs a simpler interface. Refactor first.
11. **You're writing tests to match existing code** — That's test-coverage, not TDD. TDD means the test comes first.
12. **You feel confident enough to skip verification** — That's exactly when bugs slip through. Run the test.

## When Stuck

See `references/tdd-troubleshooting.md` for detailed decision tables, the "wish" technique, and debugging integration guidance.

| Problem | Solution |
|---------|----------|
| Don't know what test to write | Describe the behavior in plain English first. The test is that sentence turned into code. |
| Test is too complex | Break the behavior into smaller pieces. Test each piece separately. |
| Can't make the test pass simply | The design is wrong. Step back. What interface would make this test trivial? |
| Too many mocks needed | Extract an interface, inject dependencies, or split the unit — see `references/testing-anti-patterns.md`. |
| Existing code has no tests | Don't retrofit TDD. Use test-coverage mode. Use TDD mode for new behavior. |
| Feature is unclear | Explore first. Come back to TDD when you know what to build. |
| Tests pass but behavior is wrong | Your tests don't cover the actual requirements. Write a new test for the failing scenario. |
| Refactoring breaks tests | Undo. Refactoring should not change behavior. If it does, you're changing functionality. |
