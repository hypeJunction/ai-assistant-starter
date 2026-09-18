# Debugging Techniques

Specialized techniques for common bug categories, plus rationalization prevention to keep debugging honest and systematic.

## Failure Mode Taxonomy

Classify the bug early to select the right diagnostic approach:

| Category | Symptoms | Diagnostic Approach |
|----------|----------|-------------------|
| **Logic Error** | Wrong output, incorrect calculation, off-by-one | Trace data through the algorithm step by step. Add assertions at each transformation. |
| **Data Issue** | Unexpected null, wrong type, missing field, corrupt data | Log the actual data at each stage. Compare expected vs actual shape. |
| **State Problem** | Works sometimes, depends on order, accumulates errors | Map all state mutations. Look for shared mutable state, stale closures, missing resets. |
| **Integration Failure** | Works in isolation, fails when combined | Test each component boundary independently. Check serialization, encoding, API contracts. |
| **Resource Issue** | Memory leak, connection pool exhaustion, disk full | Profile resource usage over time. Look for unclosed handles, unbounded caches, missing cleanup. |
| **Environment Mismatch** | Works locally, fails elsewhere | Compare: Node version, env vars, OS, file paths, timezone, locale, available ports. |

## Condition-Based Waiting

For intermittent or timing-related bugs, replace arbitrary timeouts with condition polling.

### The Problem

```typescript
// BAD: Arbitrary timeout — passes on fast machines, fails on slow ones
await new Promise(resolve => setTimeout(resolve, 2000));
expect(element).toBeVisible();
```

### The Solution

```typescript
// GOOD: Wait for the actual condition
await waitFor(() => {
  expect(element).toBeVisible();
}, { timeout: 5000 });

// GOOD: Playwright auto-waiting
await expect(page.locator('#result')).toBeVisible();

// GOOD: Poll for a backend condition
async function waitForCondition(
  check: () => Promise<boolean>,
  { timeout = 5000, interval = 100 } = {}
) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (await check()) return;
    await new Promise(r => setTimeout(r, interval));
  }
  throw new Error(`Condition not met within ${timeout}ms`);
}

await waitForCondition(() => db.job.findFirst({ where: { status: 'complete' } }));
```

### When to Suspect Timing

- Test passes 9/10 times
- Test passes locally but fails in CI (CI is slower)
- Adding `console.log` makes the test pass (slows execution enough)
- Test passes with a `setTimeout` but fails without it

## Test Polluter Detection

When a test fails only when run with the full suite (not in isolation), another test is polluting shared state.

### Bisection Method

```bash
# Step 1: Confirm it passes in isolation
npx vitest run path/to/failing.test.ts

# Step 2: Run with the full suite to confirm failure
npx vitest run

# Step 3: Bisect — run with first half of other tests
npx vitest run tests/a-through-m/**

# Step 4: If it fails, the polluter is in a-m. If it passes, it's in n-z.
# Continue bisecting until you find the polluting test.
```

### Common Polluters

| Pollution Type | Symptom | Fix |
|---------------|---------|-----|
| Global variable mutation | Tests depend on global state set by prior test | Reset globals in `beforeEach` or use `vi.stubGlobal` |
| Database state | Prior test inserts data that affects query results | Use transactions with rollback, or truncate tables in `beforeEach` |
| Module-level cache | Cached value from prior test affects current test | Clear caches in `beforeEach`, or use `vi.resetModules()` |
| Environment variables | Prior test sets `process.env.X` | Restore env in `afterEach` using `vi.stubEnv` |
| Mocks not restored | `vi.spyOn` or `vi.mock` leaks into next test | Use `vi.restoreAllMocks()` in `afterEach` |
| Singleton state | Module-level instance carries state between tests | Provide factory function, not singleton |

## Git Bisect Cookbook

When you know the code worked at some point and broke later, use `git bisect` to find the exact commit.

```bash
# Start bisect
git bisect start

# Mark current (broken) as bad
git bisect bad

# Mark a known good commit (e.g., last release tag, or a specific commit)
git bisect good v1.2.0

# Git will checkout a midpoint. Test it:
npm run test -- path/to/failing.test.ts

# If the test passes at this commit:
git bisect good

# If the test fails:
git bisect bad

# Repeat until git identifies the first bad commit
# Git will output: "abc1234 is the first bad commit"

# When done:
git bisect reset
```

### Automated Bisect

```bash
# Fully automated: git runs the test at each step
git bisect start HEAD v1.2.0
git bisect run npm test -- path/to/failing.test.ts
# Git will automatically find the breaking commit
git bisect reset
```

## Race Condition Analysis

### Detection

```typescript
// Technique: Add artificial delays to expose race conditions
async function debugRaceCondition() {
  const results = await Promise.all([
    operation1(),                           // Concurrent
    delay(10).then(() => operation2()),     // Slightly delayed
  ]);
  // If results change with different delays, you have a race condition
}
```

### Common Race Patterns

| Pattern | Example | Fix |
|---------|---------|-----|
| Check-then-act | Check balance → deduct (another request deducts between) | Use database transaction or atomic operation |
| Read-modify-write | Read counter → increment → write (another write overwrites) | Use atomic increment (`UPDATE SET count = count + 1`) |
| Double submit | User clicks twice → two orders created | Use idempotency key, disable button, debounce |
| Stale closure | React useEffect captures old state value | Add dependency to deps array, use ref for latest value |

## Rationalization Prevention

Common excuses that lead to bad debugging. Recognize and resist them.

| Rationalization | Why It's Wrong | What to Do Instead |
|----------------|----------------|-------------------|
| "It works on my machine" | Different environment, different result | Reproduce in CI or a clean environment |
| "It must be a race condition" | Underpowered hypothesis — could be anything | Prove timing dependence with controlled delays first |
| "The fix is obvious" | Obvious fixes often fix symptoms, not causes | Verify the hypothesis before writing any code |
| "Let me just try this quick fix" | Guessing isn't debugging. Quick fixes accumulate. | Form hypothesis → design experiment → verify → then fix |
| "I'll add a null check" | Null checks at the symptom hide the real problem | Trace backward: WHY is it null? Fix THAT. |
| "This is probably a framework bug" | Almost never true. It's your code. | Prove it with a minimal reproduction outside your app |
| "Works in the test, must be fine" | Tests may not cover the actual failure condition | Add a test that reproduces the exact bug scenario |
| "It was working yesterday" | Something changed. Find what. | Use `git bisect` or `git log` to find the change |
| "It's flaky, just retry" | Flaky tests have deterministic root causes | Find the root cause. See condition-based waiting and test polluter detection. |
| "I just need more logging" | Logging without a hypothesis is fishing | Form a hypothesis FIRST, then add targeted logging to confirm or deny it |

## See Also

- [TDD Troubleshooting](../../tdd/references/tdd-troubleshooting.md) — Test isolation techniques and debugging test failures
- [E2E Flaky Tests](../../e2e/references/e2e-flaky-tests.md) — Flaky test diagnosis for end-to-end tests
