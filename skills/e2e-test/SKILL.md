---
name: e2e-test
description: End-to-end testing workflow for web applications using Playwright or Cypress. Covers user flow discovery, test design, implementation, execution, and flaky test management.
---

# E2E Test

> **Purpose:** End-to-end testing for web applications
> **Phases:** Setup → Discover → Design → Implement → Run → Report
> **Usage:** `/e2e-test [scope flags] <description of what to test>`

## Iron Laws

1. **TEST USER FLOWS, NOT IMPLEMENTATION** — E2E tests should mirror real user behavior, not internal APIs. If the user would not do it, the test should not do it.
2. **EVERY TEST MUST CLEAN UP AFTER ITSELF** — No test should depend on state from another test. Each test starts from a known state and leaves no residue.
3. **FLAKY TESTS ARE BROKEN TESTS** — A test that sometimes passes and sometimes fails is not acceptable. Fix it or delete it. Never ignore, never retry-and-hope.

## When to Use

- Critical user flows (signup, login, checkout)
- Authentication and authorization flows
- Form submissions with validation
- Multi-page workflows and wizards
- Checkout and payment processes
- Cross-browser compatibility verification

## When NOT to Use

- Unit testing individual functions → `/cover` or `/tdd`
- API testing without a browser → `/api-test`
- Visual design review → `/review`
- Performance benchmarking → use dedicated profiling tools
- Testing third-party services directly → mock them instead

## Never Do

- **Never use CSS selectors for test targeting** — Use `data-testid` or role-based selectors. CSS classes change with styling; test anchors must be stable.
- **Never use fixed sleep/wait times** — Use the framework's built-in waiting mechanisms (`waitForSelector`, `waitForNavigation`, Cypress auto-retry). `setTimeout` in tests is a flakiness factory.
- **Never test third-party services in E2E** — Mock external APIs. Your tests should not fail because Stripe's sandbox is down.
- **Never write E2E tests for every edge case** — That is what unit tests are for. E2E tests cover critical paths and integration points.
- **Never share mutable state between tests** — Each test is an island. Shared state creates ordering dependencies and mystery failures.

## Gate Enforcement

**CRITICAL:** This workflow requires confirmation before implementing tests.

**Valid approval:** `yes`, `y`, `approved`, `proceed`, `lgtm`, `go ahead`
**Invalid (NOT approval):** Silence, questions, "I see", "okay", "hmm"

**Key gates:**
1. Confirm flow inventory before designing tests
2. Approve test design before implementation
3. Confirm before committing test files

## Scope Flags

| Flag | Description |
|------|-------------|
| `--framework=<name>` | Testing framework: `playwright` or `cypress` |
| `--files=<paths>` | Limit scope to specific test files or app files |
| `--flow=<name>` | Target a specific user flow (e.g., `login`, `checkout`) |

**Examples:**
```bash
/e2e-test --framework=playwright login and signup flows
/e2e-test --flow=checkout verify the full purchase flow
/e2e-test --files=e2e/auth/ fix flaky authentication tests
```

---

## Phase 1: Setup

**Mode:** Read-only investigation — verify testing infrastructure.

### Step 1.1: Detect Framework

```bash
cat package.json | grep -E "playwright|cypress"
ls playwright.config.* cypress.config.* 2>/dev/null
```

- Check `package.json` for `@playwright/test` or `cypress`
- If neither detected, recommend Playwright and offer to scaffold
- Verify test config exists (`playwright.config.ts`, `cypress.config.ts`)

### Step 1.2: Verify Configuration

```markdown
## E2E Setup

| Check | Status |
|-------|--------|
| Framework | [Playwright/Cypress/None] |
| Config file | [Found/Missing] |
| Base URL | [configured/missing] |
| Test directory | [path or missing] |
| Browsers installed | [yes/no] |
```

If setup is incomplete, offer to scaffold before proceeding.

### Step 1.3: Parse Scope

```bash
git branch --show-current
git status --porcelain
```

Identify target scope from flags and description.

---

## Phase 2: Discover

**Mode:** Read-only — identify what needs testing.

### Step 2.1: Identify User Flows

Examine the application to map critical user flows:

```bash
# Find route definitions
grep -rn "path=" src/ --include="*.tsx" --include="*.ts"
grep -rn "Route" src/ --include="*.tsx" --include="*.ts"

# Find page components
find src -name "page.*" -o -name "Page.*" | head -20
```

### Step 2.2: Review Existing Tests

```bash
# Check what is already covered
find e2e tests/e2e cypress/e2e -name "*.spec.*" -o -name "*.test.*" 2>/dev/null
```

### Step 2.3: Present Flow Inventory

```markdown
## Flow Inventory

| Flow | Pages | Existing Tests | Priority |
|------|-------|----------------|----------|
| Login | /login → /dashboard | 0 | High |
| Signup | /signup → /verify → /dashboard | 0 | High |
| Checkout | /cart → /shipping → /payment → /confirm | 0 | Critical |

Confirm these flows? (yes / modify)
```

**GATE: Wait for confirmation before designing tests.**

---

## Phase 3: Design

**Mode:** Read-only — plan test scenarios for each flow.

### Step 3.1: Design Test Scenarios

For each approved flow, design scenarios covering:

- **Happy path:** Standard successful flow
- **Error states:** Validation errors, network failures, unauthorized access
- **Edge cases:** Empty states, long inputs, special characters, back-button navigation

### Step 3.2: Define Page Objects (if needed)

For flows spanning multiple pages, outline Page Object Model structure:

```markdown
## Page Objects

- `LoginPage` — email input, password input, submit button, error message
- `DashboardPage` — user greeting, navigation menu, logout button
```

### Step 3.3: Present Test Design

```markdown
## Test Design: [Flow Name]

### Happy Path
1. Navigate to /login
2. Fill email and password
3. Click Sign in
4. Verify redirect to /dashboard
5. Verify user greeting visible

### Error: Invalid Credentials
1. Navigate to /login
2. Fill invalid credentials
3. Click Sign in
4. Verify error message displayed
5. Verify still on /login

### Edge: Empty Form Submission
1. Navigate to /login
2. Click Sign in without filling fields
3. Verify validation messages

---
**Approve test design?** (yes / no / modify)
```

**STOP HERE. Do NOT implement tests until user responds with explicit approval.**

---

## Phase 4: Implement

**Mode:** Full access — create test files.

### Step 4.1: Create Test Files

Follow project conventions for file naming and directory structure. Use the approved test design as the blueprint.

**Selector strategy (in priority order):**
1. Role-based: `getByRole('button', { name: 'Sign in' })`
2. Label: `getByLabel('Email')`
3. Test ID: `getByTestId('submit-btn')`
4. Text content: `getByText('Welcome')`
5. CSS selector: **last resort only**

### Step 4.2: Implement with Proper Waits

Use framework-native waiting, never `setTimeout`:

```typescript
test.describe('User Authentication', () => {
  test('should allow login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('user@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText('Invalid email or password')).toBeVisible();
  });
});
```

### Step 4.3: Add Page Objects (if designed)

```typescript
// e2e/pages/login.page.ts
export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.page.getByLabel('Email').fill(email);
    await this.page.getByLabel('Password').fill(password);
    await this.page.getByRole('button', { name: 'Sign in' }).click();
  }

  async expectError(message: string) {
    await expect(this.page.getByRole('alert')).toContainText(message);
  }
}
```

### Step 4.4: Test Isolation

Ensure each test:
- Starts from a clean state (fresh page, no leftover data)
- Does not depend on test execution order
- Cleans up any data it creates (users, records, files)

---

## Phase 5: Run

**Mode:** Execution — run tests and collect results.

### Step 5.1: Run in Headless Mode

```bash
# Playwright
npx playwright test [file]

# Cypress
npx cypress run --spec [file]
```

### Step 5.2: Handle Failures

If tests fail:

1. Review the error output and screenshots/traces
2. Offer headed mode for debugging:

```bash
# Playwright — headed with trace
npx playwright test [file] --headed --trace on

# Cypress — interactive
npx cypress open
```

3. Fix issues and re-run

### Step 5.3: Escalation Rule

| Attempt | Action |
|---------|--------|
| 1st failure | Review error, fix obvious issues (selectors, timing) |
| 2nd failure | Enable tracing/screenshots, inspect step-by-step |
| 3rd failure | **STOP.** Likely a flaky test or app bug, not a test bug. Present findings to user. |

---

## Phase 6: Report

**Mode:** Summary — present results and recommendations.

### Step 6.1: Results Summary

```markdown
## E2E Test Results

| Flow | Tests | Passed | Failed | Skipped |
|------|-------|--------|--------|---------|
| Login | 4 | 4 | 0 | 0 |
| Signup | 3 | 2 | 1 | 0 |
| Checkout | 5 | 5 | 0 | 0 |

**Total:** 12 tests, 11 passed, 1 failed
```

### Step 6.2: Failure Details

For each failure, include:
- Test name and file
- Error message
- Screenshot or trace link (if available)
- Likely cause and suggested fix

### Step 6.3: Coverage and Recommendations

```markdown
## Coverage by Flow

| Flow | Happy Path | Errors | Edge Cases |
|------|------------|--------|------------|
| Login | Covered | Covered | Partial |
| Signup | Covered | Missing | Missing |

## Recommendations
- [ ] Add signup error handling tests
- [ ] Add edge case tests for login (special characters in email)
- [ ] Consider adding visual regression tests for critical pages
```

### Step 6.4: Commit

```markdown
## Ready to Commit

**Files created/changed:**
- `e2e/auth/login.spec.ts` — Login flow tests
- `e2e/pages/login.page.ts` — Login page object

**Message:**
```
test(e2e): add login flow end-to-end tests

Covers happy path, invalid credentials, and empty form
submission. Uses Page Object Model for maintainability.
```

**Commit?** (yes / no / edit)
```

**STOP HERE. Wait for explicit approval before committing.**

---

## Handling Flaky Tests

### Identify

A test is flaky if:
- It passes locally but fails in CI
- It passes sometimes and fails other times with no code changes
- It fails only when run with other tests but passes in isolation

### Common Causes

| Cause | Symptom | Fix |
|-------|---------|-----|
| Timing issues | Element not found, timeout | Add proper waits (`waitForSelector`, `expect().toBeVisible()`) |
| Animation interference | Click on wrong element, element moving | Disable animations in test mode |
| Network dependency | Intermittent timeout, connection refused | Mock all external API calls |
| Test ordering | Passes alone, fails in suite | Isolate state, reset between tests |
| Shared state | Random data appearing in assertions | Each test creates its own data |
| Race condition | Inconsistent assertion failures | Wait for specific conditions, not time |

### Decision

**Fix or delete. Never ignore.**

- If the flaky test covers a critical flow: fix it (proper waits, mocking, isolation)
- If the flaky test covers a non-critical edge case: delete it and document why
- Never add retry logic as a "fix" for flakiness — that masks the real problem

---

## Quick Reference

| Phase | Mode | Gate |
|-------|------|------|
| 1. Setup | Read-only | Framework detected and configured |
| 2. Discover | Read-only | **User confirms flow inventory** |
| 3. Design | Read-only | **User approves test design** |
| 4. Implement | Full access | Tests written per approved design |
| 5. Run | Execution | **All tests pass (or failures triaged)** |
| 6. Report | Summary | **User approves before commit** |
