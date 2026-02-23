# E2E Skill Verification

## Scenario

A developer has a Next.js application with a login flow:
- Email/password form on `/login`
- Form submits to `/api/auth/login`
- On success, redirects to `/dashboard`
- On failure, shows an error message on the login page

**Environment details:**
- Playwright is listed in `package.json` as a dev dependency
- Browser binaries have **not** been installed (fresh clone or CI environment)
- The dev server is **not** running; it needs port 3000
- The project uses `pnpm` (indicated by `pnpm-lock.yaml`)

**Invocation:** `/e2e --framework=playwright login flow`

## Expected Outcome

The agent installs missing browser binaries, handles dev server management, creates a login flow E2E test using the page object pattern, covers both success and failure cases, applies flaky test mitigations, and runs the tests to confirm they pass.

## Key Checkpoints

### 1. Agent detects testing framework (Playwright installed)

The agent reads `package.json` and finds `@playwright/test` in `devDependencies`. It locates `playwright.config.ts` (or `.js`/`.mjs`) and reads it for `baseUrl`, `webServer`, test directory, and configured browsers.

**Verify:** Setup table shows `Framework: Playwright`, config file found, and test directory identified.

### 2. Agent detects package manager from lockfile

The agent checks for lockfiles in this order: `pnpm-lock.yaml` (pnpm), `yarn.lock` (yarn), `bun.lockb` (bun), `package-lock.json` (npm). In this scenario, `pnpm-lock.yaml` is present, so the agent selects `pnpm`.

**Verify:** All subsequent install/run commands use `pnpm` (e.g., `pnpm exec playwright install`, `pnpm run dev`), never `npm` or `npx` for project-level commands.

### 3. Agent checks browser installation

The agent verifies whether browser binaries are installed for Playwright. It checks by running a dry-run or checking the Playwright cache directory, or notes the check in the setup table.

**Verify:** Setup table shows `Browsers installed: no` or equivalent detection output. The agent does not skip this step.

### 4. Agent installs browser binaries if missing

The agent runs the appropriate install command using the detected package manager: `pnpm exec playwright install chromium` (or all configured browsers). If the project's Playwright config specifies particular browsers, only those are installed.

**Verify:** Browser install command runs before any test execution. The agent waits for installation to complete and confirms success.

### 5. Agent handles dev server

The agent checks the Playwright config for a `webServer` block:
- **(a)** If `webServer` is configured (e.g., `{ command: 'pnpm run dev', url: 'http://localhost:3000' }`), the agent notes that Playwright will manage the server automatically and does not start it manually.
- **(b)** If `webServer` is not configured, the agent checks if port 3000 is already in use. If not running, the agent either adds a `webServer` config to `playwright.config.ts` or documents that the dev server must be started manually.
- **(c)** The agent does not ignore dev server status; it addresses the concern explicitly.

**Verify:** The agent either confirms `webServer` config exists or takes action. Tests do not fail due to `ECONNREFUSED` on localhost.

### 6. Agent discovers the login flow pages and API endpoints

The agent examines the application source to find:
- The login page component (e.g., `app/login/page.tsx` or `pages/login.tsx`)
- Form fields (email input, password input, submit button)
- The API endpoint (`/api/auth/login`) and its expected request/response shape
- The redirect target (`/dashboard`) and what renders there

**Verify:** Flow inventory table lists the login flow with its pages, and the agent presents the discovered form elements and API endpoint.

### 7. Agent creates test with page object pattern (or project's existing pattern)

The agent creates:
- A page object class (e.g., `e2e/pages/login.page.ts`) with locators for email input, password input, submit button, and error message. Extends a `BasePage` if one exists.
- A test file (e.g., `e2e/auth/login.spec.ts`) that uses the page object.
- Selectors follow the priority hierarchy: role-based > label > test ID > text > CSS.

**Verify:** Test file imports and instantiates the page object. Selectors use `getByLabel`, `getByRole`, or `getByTestId` -- never raw CSS selectors for test targeting.

### 8. Agent tests both success case and failure case

**Success case:**
1. Navigate to `/login`
2. Fill email and password with valid credentials
3. Click the sign-in button
4. Assert redirect to `/dashboard` (`await expect(page).toHaveURL('/dashboard')`)
5. Assert a dashboard element is visible

**Failure case:**
1. Navigate to `/login`
2. Fill email and password with invalid credentials
3. Click the sign-in button
4. Assert error message is visible (e.g., `await expect(page.getByRole('alert')).toContainText('Invalid')`)
5. Assert URL is still `/login`

**Verify:** Both test cases are present, with distinct test names. Assertions check both URL and visible content.

### 9. Agent applies flaky test mitigations

- Uses Playwright's auto-waiting locators (`getByRole`, `getByLabel`), never `page.$()` or element handles
- Uses `await expect(locator).toBeVisible()` instead of `await locator.isVisible()`
- Waits for URL change with `await expect(page).toHaveURL(...)` or `await page.waitForURL(...)`
- Does not use `page.waitForTimeout()`, `setTimeout()`, or `sleep()`
- If the login triggers an API call, optionally waits for the response with `page.waitForResponse()`

**Verify:** No `waitForTimeout`, `setTimeout`, or `sleep` calls in the test. All assertions use Playwright's `expect` with auto-retry.

### 10. Agent runs the tests and they pass

The agent executes the tests:
```bash
pnpm exec playwright test e2e/auth/login.spec.ts
```

If tests fail, the agent follows the escalation rule (fix obvious issues on 1st failure, enable tracing on 2nd, stop and present findings on 3rd).

**Verify:** Test output shows all tests passing. If there were failures, the agent diagnosed and fixed them within the escalation limit.

### 11. Agent handles third-party iframe if login uses OAuth widget

If the login flow involves a third-party OAuth provider (e.g., Google, GitHub) rendered in an iframe or popup:
- The agent recognizes that third-party iframes cannot be reliably tested end-to-end
- The agent mocks the third-party auth at the API level (e.g., mock `/api/auth/callback` to return a valid session)
- The agent tests up to the redirect to the provider and after the callback
- The agent documents the limitation in the test file with a comment

**Verify:** If OAuth is detected, the test does not attempt to interact with the third-party iframe. A mock or bypass strategy is used. A comment documents why.

## Anti-patterns

| Anti-pattern | Why it's wrong | What to do instead |
|---|---|---|
| Assume browsers are installed | Browser binaries may not exist in fresh clones, CI, or containers | Always check and install if missing before running tests |
| Use `npm` when project uses `pnpm` | Causes lockfile conflicts, installs to wrong location, breaks reproducibility | Detect package manager from lockfile and use it consistently |
| Use `sleep()` or arbitrary timeouts for waiting | Creates flaky tests that are timing-dependent; pass on fast machines, fail on slow ones | Use framework-native auto-waiting: `expect(locator).toBeVisible()`, `page.waitForURL()` |
| Skip dev server management | Tests fail with `ECONNREFUSED` or `ERR_CONNECTION_REFUSED` because no server is listening | Check Playwright's `webServer` config, verify port is active, or start the server |
| Ignore third-party iframe/OAuth scenarios | Tests hang or fail trying to interact with cross-origin iframes that block automation | Mock the third-party at the API level; test up to redirect and after callback |
| Use raw CSS selectors for test targeting | CSS classes change with styling and refactoring, causing brittle tests | Use role-based, label-based, or test-id selectors |
| Share mutable state between tests | Creates ordering dependencies and mystery failures | Each test starts from a clean state and creates its own data |

## Known Gaps (addressed in this update)

| Gap | Status |
|-----|--------|
| No package manager detection | Fixed: added lockfile detection step in Phase 1 |
| No browser installation step | Fixed: added browser binary verification and install step |
| No dev server management | Fixed: added dev server check and management step |
| No third-party iframe guidance | Fixed: added iframe/OAuth handling guidance |
| `e2e-patterns.md` not linked from main workflow | Fixed: added reference links in Implement and Flaky Tests sections |
