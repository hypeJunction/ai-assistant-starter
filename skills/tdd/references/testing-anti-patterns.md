# Testing Anti-Patterns

Common testing mistakes that undermine test suite value. Each anti-pattern includes what it looks like, why it harms you, and what to do instead.

---

## 1. Testing Mock Behavior Instead of Real Behavior

**What it looks like:** Tests assert that a mock was called with specific arguments rather than asserting the outcome of the operation.

**Why it's harmful:** You're testing your test setup, not your code. The mock always does what you told it to. If the real dependency changes behavior, your tests still pass -- and your code breaks.

**What to do instead:** Assert on observable outcomes (return values, state changes, side effects). Use real implementations when feasible. Reserve mocks for I/O boundaries (network, filesystem, clock).

---

## 2. Testing Implementation Details

**What it looks like:** Tests verify private methods, internal state, or the specific sequence of internal operations. Refactoring breaks the tests even though behavior is unchanged.

**Why it's harmful:** Tests become brittle. Every internal change requires test updates. Developers fear refactoring because "it breaks the tests." The tests protect the implementation, not the behavior.

**What to do instead:** Test through the public API. Assert on what the code does, not how it does it. If you can swap the implementation and behavior stays the same, the tests should still pass.

---

## 3. Tests That Mirror Implementation

**What it looks like:** The test has the same conditional logic as the production code. If the code has an `if`, the test has an `if`. The test is a copy of the implementation with assertions added.

**Why it's harmful:** Both the code and the test have the same bug. The test confirms the implementation matches itself, which proves nothing. Any logic error is duplicated.

**What to do instead:** Use concrete examples with hardcoded inputs and expected outputs. Let the test be a lookup table, not an algorithm. The test should be simpler than the code it tests.

---

## 4. Excessive Mocking

**What it looks like:** Every dependency is mocked. The test constructs an elaborate fake world. More lines configure mocks than assert behavior. The "unit" is tested in total isolation from everything.

**Why it's harmful:** The test proves the code works in a world that doesn't exist. Integration between components is never tested. Real bugs hide in the seams between units.

**What to do instead:** Mock at architectural boundaries (database, network, external APIs). Use real implementations for in-process collaborators. If mocking is painful, the design has too many dependencies -- fix the design.

---

## 5. Test-Only Production Code

**What it looks like:** Public methods, properties, or flags exist solely to make testing possible: `_testOnly_reset()`, `isTestMode`, `public` visibility on methods that should be private.

**Why it's harmful:** Production code becomes polluted with test infrastructure. The public API is wider than it should be. Other code starts depending on test-only methods.

**What to do instead:** Redesign for testability. Use dependency injection. Extract interfaces. If you can't test it through the public API, the API is wrong.

---

## 6. Shared Mutable State Between Tests

**What it looks like:** Tests share a module-level variable, a singleton, or a database that isn't reset between tests. Test order matters. Tests pass individually but fail together.

**Why it's harmful:** Tests are not independent. Adding, removing, or reordering tests causes failures. Debugging requires running the full suite in a specific order.

**What to do instead:** Each test creates its own state. Use `beforeEach` to reset shared resources. Avoid module-level mutable variables. Prefer factory functions over shared fixtures.

---

## 7. Testing the Framework

**What it looks like:** Tests assert that React renders a component, that Express calls a route handler, or that a database driver returns query results. The test verifies the framework works, not your code.

**Why it's harmful:** The framework is already tested by its maintainers. You're spending time proving that well-tested libraries work. Your application logic gets no coverage.

**What to do instead:** Test your logic, not the glue. Extract business logic from framework code. Test the logic directly. Use integration tests sparingly to verify the wiring.

---

## 8. Flaky Tests Accepted as Normal

**What it looks like:** Some tests fail intermittently. The team reruns CI until it passes. Nobody investigates. "Oh, that one's flaky" is a normal response.

**Why it's harmful:** Flaky tests erode trust in the entire suite. When a real failure occurs, it gets dismissed as "probably flaky." The test suite stops being a reliable safety net.

**What to do instead:** Treat flaky tests as bugs. Fix or delete them immediately. Common causes: race conditions, time-dependent assertions, shared state, network calls in unit tests.

---

## 9. Tests Without Assertions

**What it looks like:** The test calls a function but never asserts anything. It passes because no exception was thrown. Sometimes disguised as "smoke tests."

**Why it's harmful:** The test verifies that the code runs without crashing, but not that it produces correct results. Silent wrong behavior passes undetected.

**What to do instead:** Every test must assert a specific expected outcome. If you can't define what "correct" looks like, you don't understand the behavior well enough to test it.

---

## 10. Slow Tests Due to Unnecessary I/O

**What it looks like:** Unit tests hit the database, make HTTP requests, read files from disk, or wait on timers. The test suite takes minutes instead of seconds.

**Why it's harmful:** Slow tests don't get run. Developers skip them locally and wait for CI. The feedback loop stretches from seconds to minutes. TDD becomes impractical.

**What to do instead:** Unit tests should be pure computation with no I/O. Mock I/O boundaries. Use in-memory implementations. Reserve real I/O for integration tests in a separate suite with its own run target.
