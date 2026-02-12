Patterns and best practices for end-to-end testing with Playwright and Cypress, including Page Object Model, selector strategies, authentication, forms, network mocking, visual regression, and CI integration.

## Page Object Model Template

```typescript
// e2e/pages/base.page.ts
import { Page, Locator, expect } from '@playwright/test';

export abstract class BasePage {
  constructor(protected page: Page) {}

  abstract readonly url: string;

  async goto() {
    await this.page.goto(this.url);
  }

  async waitForLoad() {
    await this.page.waitForLoadState('networkidle');
  }
}

// e2e/pages/login.page.ts
export class LoginPage extends BasePage {
  readonly url = '/login';

  get emailInput(): Locator {
    return this.page.getByLabel('Email');
  }

  get passwordInput(): Locator {
    return this.page.getByLabel('Password');
  }

  get submitButton(): Locator {
    return this.page.getByRole('button', { name: 'Sign in' });
  }

  get errorMessage(): Locator {
    return this.page.getByRole('alert');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(text: string) {
    await expect(this.errorMessage).toContainText(text);
  }
}
```

## Selector Strategy Hierarchy

Use selectors in this priority order. Higher priorities are more resilient to UI changes.

| Priority | Strategy | Example | When to Use |
|----------|----------|---------|-------------|
| 1 | Role | `getByRole('button', { name: 'Submit' })` | Interactive elements with ARIA roles |
| 2 | Label | `getByLabel('Email address')` | Form inputs with labels |
| 3 | Test ID | `getByTestId('checkout-total')` | Elements without accessible roles or labels |
| 4 | Text | `getByText('Welcome back')` | Static content verification |
| 5 | CSS | `page.locator('.btn-primary')` | Last resort only — fragile |

## Common Playwright Patterns

### Navigation

```typescript
// Navigate and wait for load
await page.goto('/dashboard');
await page.waitForURL('/dashboard');

// Click link and wait for navigation
await page.getByRole('link', { name: 'Settings' }).click();
await page.waitForURL('/settings');

// Go back
await page.goBack();
await page.waitForURL('/dashboard');
```

### Forms

```typescript
// Text input
await page.getByLabel('Name').fill('Jane Doe');

// Select dropdown
await page.getByLabel('Country').selectOption('US');

// Checkbox
await page.getByLabel('Accept terms').check();
await expect(page.getByLabel('Accept terms')).toBeChecked();

// Radio button
await page.getByLabel('Monthly').check();

// Date input
await page.getByLabel('Start date').fill('2025-01-15');
```

### Modals and Dialogs

```typescript
// Wait for modal to appear
const modal = page.getByRole('dialog');
await expect(modal).toBeVisible();

// Interact within modal
await modal.getByLabel('Reason').fill('Testing');
await modal.getByRole('button', { name: 'Confirm' }).click();

// Wait for modal to close
await expect(modal).toBeHidden();

// Handle browser dialogs
page.on('dialog', async (dialog) => {
  expect(dialog.message()).toContain('Are you sure?');
  await dialog.accept();
});
```

### File Upload

```typescript
// Single file
const fileInput = page.locator('input[type="file"]');
await fileInput.setInputFiles('tests/fixtures/document.pdf');

// Multiple files
await fileInput.setInputFiles([
  'tests/fixtures/photo1.png',
  'tests/fixtures/photo2.png',
]);

// Clear file selection
await fileInput.setInputFiles([]);
```

### Drag and Drop

```typescript
const source = page.getByTestId('drag-item');
const target = page.getByTestId('drop-zone');
await source.dragTo(target);
```

## Common Cypress Patterns

### Navigation

```typescript
cy.visit('/dashboard');
cy.url().should('include', '/dashboard');

cy.contains('a', 'Settings').click();
cy.url().should('include', '/settings');
```

### Forms

```typescript
cy.findByLabelText('Name').type('Jane Doe');
cy.findByLabelText('Country').select('US');
cy.findByLabelText('Accept terms').check();
cy.findByRole('button', { name: 'Submit' }).click();
```

### Modals

```typescript
cy.findByRole('dialog').within(() => {
  cy.findByLabelText('Reason').type('Testing');
  cy.findByRole('button', { name: 'Confirm' }).click();
});
cy.findByRole('dialog').should('not.exist');
```

## Authentication Test Patterns

### Login Flow

```typescript
test.describe('Login', () => {
  test('successful login redirects to dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('user@example.com');
    await page.getByLabel('Password').fill('validpassword');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome')).toBeVisible();
  });

  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('user@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('alert')).toContainText('Invalid');
    await expect(page).toHaveURL('/login');
  });
});
```

### Session Expiry

```typescript
test('expired session redirects to login', async ({ page, context }) => {
  // Login first
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('validpassword');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL('/dashboard');

  // Clear cookies to simulate expiry
  await context.clearCookies();

  // Attempt to visit protected page
  await page.goto('/settings');
  await expect(page).toHaveURL('/login');
});
```

### Role-Based Access

```typescript
test('non-admin cannot access admin page', async ({ page }) => {
  // Login as regular user
  await loginAs(page, 'user@example.com', 'password');
  await page.goto('/admin');
  await expect(page.getByText('Access denied')).toBeVisible();
});
```

## Form Testing Patterns

### Validation

```typescript
test('shows validation errors for empty required fields', async ({ page }) => {
  await page.goto('/register');
  await page.getByRole('button', { name: 'Register' }).click();

  await expect(page.getByText('Email is required')).toBeVisible();
  await expect(page.getByText('Password is required')).toBeVisible();
});

test('shows validation error for invalid email format', async ({ page }) => {
  await page.goto('/register');
  await page.getByLabel('Email').fill('not-an-email');
  await page.getByRole('button', { name: 'Register' }).click();

  await expect(page.getByText('Enter a valid email')).toBeVisible();
});
```

### Multi-Step Form

```typescript
test('completes multi-step registration', async ({ page }) => {
  await page.goto('/register');

  // Step 1: Personal info
  await page.getByLabel('Full name').fill('Jane Doe');
  await page.getByLabel('Email').fill('jane@example.com');
  await page.getByRole('button', { name: 'Next' }).click();

  // Step 2: Password
  await page.getByLabel('Password').fill('SecurePass123!');
  await page.getByLabel('Confirm password').fill('SecurePass123!');
  await page.getByRole('button', { name: 'Next' }).click();

  // Step 3: Review and submit
  await expect(page.getByText('Jane Doe')).toBeVisible();
  await expect(page.getByText('jane@example.com')).toBeVisible();
  await page.getByRole('button', { name: 'Create account' }).click();

  await expect(page.getByText('Account created')).toBeVisible();
});
```

## Network Mocking Patterns

### Playwright Route Interception

```typescript
// Mock a successful API response
await page.route('**/api/users', (route) => {
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Mock User' }]),
  });
});

// Simulate a server error
await page.route('**/api/checkout', (route) => {
  route.fulfill({ status: 500, body: 'Internal Server Error' });
});

// Simulate network failure
await page.route('**/api/data', (route) => {
  route.abort('connectionrefused');
});

// Delay a response to test loading states
await page.route('**/api/slow', async (route) => {
  await new Promise((resolve) => setTimeout(resolve, 3000));
  route.fulfill({ status: 200, body: JSON.stringify({ data: 'loaded' }) });
});
```

### Cypress Interception

```typescript
// Mock API response
cy.intercept('GET', '/api/users', { fixture: 'users.json' }).as('getUsers');
cy.visit('/users');
cy.wait('@getUsers');

// Simulate error
cy.intercept('POST', '/api/checkout', { statusCode: 500 }).as('checkout');

// Delay response
cy.intercept('GET', '/api/data', (req) => {
  req.reply({ delay: 3000, body: { data: 'loaded' } });
});
```

## Visual Regression Testing

### Playwright Screenshots

```typescript
// Full page screenshot comparison
await expect(page).toHaveScreenshot('dashboard.png');

// Element screenshot comparison
const card = page.getByTestId('profile-card');
await expect(card).toHaveScreenshot('profile-card.png');

// With threshold for acceptable pixel difference
await expect(page).toHaveScreenshot('hero.png', {
  maxDiffPixelRatio: 0.01,
});
```

### Disable Animations for Stability

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    // Reduce motion for consistent screenshots
    launchOptions: {
      args: ['--force-prefers-reduced-motion'],
    },
  },
});
```

## CI Integration Patterns

### GitHub Actions (Playwright)

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
```

### GitHub Actions (Cypress)

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: cypress-io/github-action@v6
        with:
          start: npm run dev
          wait-on: 'http://localhost:3000'
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: cypress-screenshots
          path: cypress/screenshots/
          retention-days: 7
```

## Performance Testing Hooks

### Measure Page Load

```typescript
test('dashboard loads within 3 seconds', async ({ page }) => {
  const start = Date.now();
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');
  const loadTime = Date.now() - start;

  expect(loadTime).toBeLessThan(3000);
});
```

### Measure Interaction Time

```typescript
test('search returns results within 1 second', async ({ page }) => {
  await page.goto('/search');
  await page.getByLabel('Search').fill('test query');

  const start = Date.now();
  await page.getByRole('button', { name: 'Search' }).click();
  await page.getByTestId('search-results').waitFor();
  const responseTime = Date.now() - start;

  expect(responseTime).toBeLessThan(1000);
});
```

### Web Vitals via Performance API

```typescript
test('homepage has acceptable LCP', async ({ page }) => {
  await page.goto('/');

  const lcp = await page.evaluate(() => {
    return new Promise<number>((resolve) => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const last = entries[entries.length - 1];
        resolve(last.startTime);
      }).observe({ type: 'largest-contentful-paint', buffered: true });
    });
  });

  expect(lcp).toBeLessThan(2500); // Good LCP threshold
});
```
