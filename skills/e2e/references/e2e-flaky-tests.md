# Flaky Test Prevention and Remediation

Deep guide for identifying, diagnosing, and fixing flaky end-to-end tests. Flaky tests erode confidence in the test suite and waste developer time. This guide provides systematic approaches to eliminate them.

## Flakiness Categories

### 1. Timing and Race Conditions

The most common cause of flaky E2E tests. The test runs faster than the UI renders.

**Symptoms:**
- "Element not found" or "Element not visible" errors
- Test passes locally, fails in CI
- Adding `sleep(1000)` "fixes" it

**Root Causes and Fixes:**

| Anti-Pattern | Fix |
|-------------|-----|
| `await page.click('.btn')` before element exists | `await page.getByRole('button', { name: 'Submit' }).click()` (auto-waits) |
| `setTimeout(() => assert(), 2000)` | `await expect(element).toBeVisible()` |
| Clicking during CSS transition | Disable animations in test config |
| Asserting immediately after navigation | `await page.waitForURL('/dashboard')` |
| Checking content before API response | Wait for the specific element that renders after response |

**Playwright auto-waiting (use this, not manual waits):**
```typescript
// These auto-wait for the element to be actionable:
await page.getByRole('button').click();      // waits for visible, enabled
await page.getByLabel('Email').fill('test'); // waits for visible, editable
await expect(locator).toBeVisible();         // waits with timeout
await expect(locator).toHaveText('Done');    // waits for text match

// These do NOT auto-wait (avoid in assertions):
const text = await locator.textContent(); // snapshot, may be stale
const visible = await locator.isVisible(); // snapshot, may change
```

### 2. Animation Interference

CSS animations and transitions move elements during test execution.

**Symptoms:**
- "Element is outside the viewport" or "Element is not stable"
- Click lands on wrong element
- Screenshot comparisons fail intermittently

**Fix: Disable animations globally in test config:**

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    // Disable CSS animations and transitions
    launchOptions: {
      args: ['--force-prefers-reduced-motion'],
    },
  },
});
```

```css
/* Or inject via addInitScript */
*, *::before, *::after {
  animation-duration: 0s !important;
  animation-delay: 0s !important;
  transition-duration: 0s !important;
  transition-delay: 0s !important;
}
```

### 3. Test Ordering Dependencies

Tests that pass in isolation but fail when run with other tests.

**Symptoms:**
- Test fails only when full suite runs
- Reordering tests changes which ones fail
- Test depends on data created by a previous test

**Diagnosis: Run the suspect test in isolation:**
```bash
# Run single test
npx playwright test tests/checkout.spec.ts --grep "should calculate total"

# Run with --repeat to catch intermittent issues
npx playwright test tests/checkout.spec.ts --repeat-each=5
```

**Fixes:**

```typescript
// Before: shared state across tests
let userId: string;

test('create user', async ({ page }) => {
  // creates user, saves to userId
  userId = await createUser(page);
});

test('edit user', async ({ page }) => {
  // uses userId from previous test — FRAGILE
  await page.goto(`/users/${userId}/edit`);
});

// After: each test creates its own state
test('edit user', async ({ page }) => {
  const userId = await createTestUser(); // fresh user per test
  await page.goto(`/users/${userId}/edit`);
  // ...
});
```

### 4. Network Flakiness

External API calls or slow server responses cause intermittent failures.

**Symptoms:**
- Timeout errors
- Different response data between runs
- Tests fail during high server load

**Fix: Mock external APIs:**
```typescript
// Mock before navigating to the page
await page.route('**/api/users', (route) => {
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ data: [{ id: 1, name: 'Test User' }] }),
  });
});

await page.goto('/users');
await expect(page.getByText('Test User')).toBeVisible();
```

**For tests that need real API responses, add explicit waits:**
```typescript
// Wait for the specific API call to complete
const responsePromise = page.waitForResponse('**/api/users');
await page.getByRole('button', { name: 'Load Users' }).click();
await responsePromise;
await expect(page.getByText('Users loaded')).toBeVisible();
```

### 5. Viewport and Responsive Issues

Tests fail because elements are off-screen or layout differs at test viewport size.

**Symptoms:**
- Click on element that's scrolled out of view
- Hamburger menu not opened (desktop nav expected)
- Different element visible at different breakpoints

**Fix: Set consistent viewport:**
```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    viewport: { width: 1280, height: 720 },
  },
});

// Or per-test for responsive testing
test('mobile menu works', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Menu' }).click();
  // ...
});
```

### 6. Browser State Leakage

Cookies, localStorage, or service workers from previous tests persist.

**Symptoms:**
- Test passes first, fails on re-run
- "Already logged in" when test expects login page
- Stale data appearing in assertions

**Fix: Isolate browser context per test:**
```typescript
// Playwright does this by default with test fixtures
// Each test() gets a fresh browser context

// For explicit cleanup:
test.beforeEach(async ({ context }) => {
  await context.clearCookies();
  await context.clearPermissions();
});

// Clear localStorage via page
test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.clear());
});
```

## Diagnosis Toolkit

### Step 1: Reproduce Locally

```bash
# Run the flaky test 10 times to reproduce
npx playwright test path/to/test.spec.ts --repeat-each=10

# Run with tracing to capture detailed execution
npx playwright test path/to/test.spec.ts --trace on

# Run headed to see what happens
npx playwright test path/to/test.spec.ts --headed
```

### Step 2: Analyze Traces

```bash
# Open the trace viewer
npx playwright show-trace test-results/path-to-trace/trace.zip
```

In the trace viewer, check:
- **Timeline:** Was there a gap between actions? Was the element ready?
- **Network:** Did any API call take unusually long or fail?
- **Snapshots:** What did the page look like at the point of failure?
- **Console:** Any JavaScript errors?

### Step 3: Isolate the Cause

| Observation | Likely Cause | Next Step |
|-------------|-------------|-----------|
| Fails in CI, passes locally | Timing (CI is slower) | Add explicit waits, check animations |
| Fails with other tests, passes alone | Shared state | Check for global state pollution |
| Fails intermittently everywhere | Race condition or animation | Trace the exact failure point |
| Fails after another specific test | Test ordering dependency | Check for shared data or cookies |
| Fails with "timeout" | Slow response or missing element | Check network mocking, selector stability |

### Step 4: Verify the Fix

```bash
# Run 20 times to confirm the fix
npx playwright test path/to/test.spec.ts --repeat-each=20

# Run full suite to check no new flakiness
npx playwright test --workers=1  # sequential to surface ordering issues
npx playwright test --workers=4  # parallel to surface race conditions
```

## Prevention Patterns

### 1. Always Wait for Specific Conditions

```typescript
// Bad: arbitrary wait
await page.waitForTimeout(2000);

// Good: wait for specific condition
await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
```

### 2. Use Locators, Not Element Handles

```typescript
// Bad: element handle is a snapshot
const button = await page.$('button.submit');
await button.click(); // may be stale

// Good: locator auto-retries
const button = page.getByRole('button', { name: 'Submit' });
await button.click(); // re-queries the DOM each time
```

### 3. Wait for Network Before Asserting

```typescript
// When a user action triggers an API call
const responsePromise = page.waitForResponse(
  (resp) => resp.url().includes('/api/save') && resp.status() === 200
);
await page.getByRole('button', { name: 'Save' }).click();
await responsePromise;
await expect(page.getByText('Saved successfully')).toBeVisible();
```

### 4. Avoid Relying on Element Order

```typescript
// Bad: fragile position-based
const items = await page.locator('.list-item').all();
expect(await items[2].textContent()).toBe('Third Item');

// Good: find by content
await expect(page.getByRole('listitem').filter({ hasText: 'Third Item' })).toBeVisible();
```

### 5. Make Tests Deterministic

```typescript
// Bad: depends on current time
test('shows greeting', async ({ page }) => {
  await page.goto('/');
  // Fails at night: "Good evening" vs "Good morning"
  await expect(page.getByText('Good morning')).toBeVisible();
});

// Good: control the clock
test('shows greeting', async ({ page }) => {
  await page.clock.setFixedTime(new Date('2025-01-15T09:00:00'));
  await page.goto('/');
  await expect(page.getByText('Good morning')).toBeVisible();
});
```

## Flaky Test Decision Tree

```
Test fails intermittently
├── Fails in CI only?
│   ├── Yes → Timing issue (CI is slower)
│   │   ├── Check for missing waits
│   │   ├── Disable animations
│   │   └── Mock slow APIs
│   └── No → Continues below
├── Fails with full suite only?
│   ├── Yes → State leakage or ordering
│   │   ├── Check for shared state
│   │   ├── Check for cookie/storage leaks
│   │   └── Ensure test isolation
│   └── No → Continues below
├── Fails with --repeat-each=10?
│   ├── Yes → Race condition
│   │   ├── Check animation interference
│   │   ├── Check for missing network waits
│   │   └── Check for DOM instability
│   └── No → Hard to reproduce
│       ├── Run with --repeat-each=50
│       ├── Add tracing and review
│       └── Check for external dependencies
└── Always fails?
    └── Not flaky — it's a broken test or broken code
```

## CI-Specific Considerations

### Retry Strategy (Last Resort)

Retries mask flakiness. Use them only as a temporary measure while diagnosing:

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 1 : 0, // 1 retry in CI only
});
```

**Rule:** If a test needs retries to pass, it has a bug. Track retried tests and fix them:

```bash
# Find tests that needed retries (check CI output for "retry")
# These are your flaky tests — fix them
```

### Parallelism

```typescript
// playwright.config.ts
export default defineConfig({
  workers: process.env.CI ? 2 : undefined,
  fullyParallel: true,
});
```

Ensure tests don't share database records, files, or server state when running in parallel.

### Artifact Collection

Always collect traces and screenshots on failure:

```yaml
# GitHub Actions
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: test-results
    path: |
      test-results/
      playwright-report/
    retention-days: 7
```

## See Also

- [Debugging Techniques](../../implement/references/debug-mode.md) — Test polluter detection with bisection, race condition analysis, and general debugging methodology
