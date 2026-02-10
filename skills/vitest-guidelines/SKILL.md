---
name: vitest-guidelines
description: Testing guidelines for Vitest/Jest including test structure, mocking, async patterns, and Testing Library queries. Auto-loaded when working with test files.
user-invocable: false
---

# Testing Guidelines

## Test Framework

This project uses **{{TEST_FRAMEWORK}}** (e.g., Vitest, Jest).

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from '{{TEST_FRAMEWORK}}';
```

## Test Plan Format

**CRITICAL:** All test files MUST include a test plan as a comment at the top.

### Gherkin Format

```typescript
/**
 * Test Plan: ComponentName
 *
 * Scenario: User can submit the form
 *   Given the form is displayed with empty fields
 *   When the user fills in all required fields
 *   And clicks the submit button
 *   Then the form data is sent to the server
 *   And a success message is displayed
 *
 * Scenario: Validation prevents invalid submission
 *   Given the form is displayed with empty fields
 *   When the user clicks submit without filling required fields
 *   Then validation errors are displayed
 *   And the form is not submitted
 */
```

### Mapping Test Plans to Tests

```typescript
describe('ComponentName', () => {
    describe('Scenario: User can submit the form', () => {
        it('sends form data to server when all fields are valid', async () => {
            // Given
            const { getByRole, getByLabelText } = render(FormComponent);

            // When
            await userEvent.type(getByLabelText('Name'), 'John Doe');
            await userEvent.type(getByLabelText('Email'), 'john@example.com');
            await userEvent.click(getByRole('button', { name: 'Submit' }));

            // Then
            expect(mockSubmit).toHaveBeenCalledWith({
                name: 'John Doe',
                email: 'john@example.com'
            });
        });
    });
});
```

### Browser-Based Test Plans (Agent-Browser Compatible)

For E2E tests, Storybook interaction tests, or DOM-based tests, use this format:

```typescript
/**
 * Test Plan: LoginForm
 *
 * Scenario: User logs in successfully
 *   Given I navigate to "/login"
 *   And I see heading "Sign In"
 *   When I type "user@example.com" into input[label="Email"]
 *   And I type "password123" into input[label="Password"]
 *   And I click button "Sign In"
 *   Then I see text "Welcome back"
 *   And URL contains "/dashboard"
 *
 * Scenario: Form shows validation errors
 *   Given I navigate to "/login"
 *   When I click button "Sign In"
 *   Then I see alert "Email is required"
 *   And button "Sign In" is disabled
 */

describe('LoginForm', () => {
    describe('Scenario: User logs in successfully', () => {
        it('navigates to dashboard after valid login', async () => {
            // Given: I navigate to "/login"
            render(<LoginForm />);

            // And: I see heading "Sign In"
            expect(screen.getByRole('heading', { name: 'Sign In' })).toBeVisible();

            // When: I type "user@example.com" into input[label="Email"]
            await userEvent.type(
                screen.getByRole('textbox', { name: 'Email' }),
                'user@example.com'
            );

            // And: I type "password123" into input[label="Password"]
            await userEvent.type(
                screen.getByLabelText('Password'),
                'password123'
            );

            // And: I click button "Sign In"
            await userEvent.click(
                screen.getByRole('button', { name: 'Sign In' })
            );

            // Then: I see text "Welcome back"
            expect(await screen.findByText('Welcome back')).toBeVisible();
        });
    });
});
```

**Mapping Locators to Testing Library:**

| Test Plan Locator | Testing Library Query |
|-------------------|----------------------|
| `button "Submit"` | `getByRole('button', { name: 'Submit' })` |
| `input[label="Email"]` | `getByRole('textbox', { name: 'Email' })` or `getByLabelText('Email')` |
| `input[placeholder="Search"]` | `getByPlaceholderText('Search')` |
| `text "Welcome"` | `getByText('Welcome')` |
| `heading "Title"` | `getByRole('heading', { name: 'Title' })` |
| `alert "Error"` | `getByRole('alert')` + text check |
| `checkbox "Terms"` | `getByRole('checkbox', { name: 'Terms' })` |
| `combobox "Country"` | `getByRole('combobox', { name: 'Country' })` |
| `[data-testid="id"]` | `getByTestId('id')` |

**Mapping Actions to userEvent:**

| Test Plan Action | userEvent Call |
|------------------|----------------|
| `I click button "X"` | `await userEvent.click(getByRole('button', { name: 'X' }))` |
| `I type "text" into input[label="Y"]` | `await userEvent.type(getByLabelText('Y'), 'text')` |
| `I clear input[label="Y"]` | `await userEvent.clear(getByLabelText('Y'))` |
| `I select "Opt" from combobox "Z"` | `await userEvent.selectOptions(getByRole('combobox', { name: 'Z' }), 'Opt')` |
| `I check checkbox "Terms"` | `await userEvent.click(getByRole('checkbox', { name: 'Terms' }))` |
| `I hover over button "Menu"` | `await userEvent.hover(getByRole('button', { name: 'Menu' }))` |
| `I press "Enter"` | `await userEvent.keyboard('{Enter}')` |

**Mapping Assertions:**

| Test Plan Assertion | Jest/Vitest Expect |
|---------------------|-------------------|
| `I see text "X"` | `expect(screen.getByText('X')).toBeVisible()` |
| `I don't see text "X"` | `expect(screen.queryByText('X')).not.toBeInTheDocument()` |
| `button "X" is visible` | `expect(getByRole('button', { name: 'X' })).toBeVisible()` |
| `button "X" is disabled` | `expect(getByRole('button', { name: 'X' })).toBeDisabled()` |
| `input[label="X"] contains "Y"` | `expect(getByLabelText('X')).toHaveValue('Y')` |
| `I see 3 listitem` | `expect(getAllByRole('listitem')).toHaveLength(3)` |

## Test Structure

### AAA Pattern (Arrange-Act-Assert)

```typescript
it('calculates the correct total', () => {
    // Arrange
    const items = [
        { price: 10, quantity: 2 },
        { price: 5, quantity: 3 }
    ];

    // Act
    const result = calculateTotal(items);

    // Assert
    expect(result).toBe(35);
});
```

### Given-When-Then (for BDD style)

```typescript
it('disables submit button when form is invalid', () => {
    // Given
    const { getByRole } = render(FormComponent);

    // When
    // (form is in initial empty state)

    // Then
    expect(getByRole('button', { name: 'Submit' })).toBeDisabled();
});
```

## Testing Library Queries

### Query Priority (Most to Least Preferred)

1. **getByRole** - Queries based on accessibility roles
2. **getByLabelText** - Queries form elements by label
3. **getByPlaceholderText** - Queries by placeholder
4. **getByText** - Queries by text content
5. **getByTestId** - Last resort, uses data-testid attribute

### Common Roles

```typescript
// Buttons & Inputs
getByRole('button', { name: 'Submit' })
getByRole('textbox', { name: 'Email' })
getByRole('spinbutton', { name: 'Age' })  // number input
getByRole('combobox', { name: 'Country' })  // select
getByRole('checkbox', { name: 'Accept Terms' })

// Messages
getByRole('alert')    // Error messages
getByRole('status')   // Status messages

// Lists & Tables
getByRole('list')
getByRole('listitem')
getByRole('table')
getByRole('row')
```

### Query Variants

```typescript
getByRole()    // Throws if not found or multiple found
queryByRole()  // Returns null if not found
findByRole()   // Async, waits for element
getAllByRole() // Returns array, throws if none found
queryAllByRole() // Returns array, empty if none found
findAllByRole()  // Async array query
```

## Mocking

### Function Mocks

```typescript
import { vi } from 'vitest';

// Mock a function
const mockFn = vi.fn();
mockFn.mockReturnValue('value');
mockFn.mockResolvedValue('async value');
mockFn.mockImplementation((arg) => arg * 2);

// Verify calls
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledWith('arg');
expect(mockFn).toHaveBeenCalledTimes(2);
```

### Module Mocks

```typescript
vi.mock('./module', () => ({
    exportedFunction: vi.fn().mockReturnValue('mocked'),
}));

// Or partial mock
vi.mock('./module', async () => {
    const actual = await vi.importActual('./module');
    return {
        ...actual,
        specificFunction: vi.fn(),
    };
});
```

### Spies

```typescript
const spy = vi.spyOn(object, 'method');
spy.mockReturnValue('mocked');

// Restore original
spy.mockRestore();
```

## Async Testing

### Waiting for Elements

```typescript
// Use findBy for async elements
const button = await findByRole('button', { name: 'Submit' });

// Or waitFor for assertions
await waitFor(() => {
    expect(getByText('Success')).toBeInTheDocument();
});

// With timeout
await waitFor(() => {
    expect(getByText('Loaded')).toBeInTheDocument();
}, { timeout: 5000 });
```

### Async Functions

```typescript
it('fetches data successfully', async () => {
    const result = await fetchData();
    expect(result).toEqual({ id: 1, name: 'Test' });
});
```

## User Interactions

### Using userEvent

```typescript
import userEvent from '@testing-library/user-event';

const user = userEvent.setup();

// Click
await user.click(button);

// Type
await user.type(input, 'Hello');

// Clear and type
await user.clear(input);
await user.type(input, 'New value');

// Select option
await user.selectOptions(select, 'option-value');

// Keyboard
await user.keyboard('{Enter}');
await user.keyboard('{Shift>}A{/Shift}'); // Shift+A
```

## Test Isolation

### Setup and Teardown

```typescript
describe('Component', () => {
    beforeEach(() => {
        // Reset state before each test
        vi.clearAllMocks();
    });

    afterEach(() => {
        // Cleanup after each test
        vi.restoreAllMocks();
    });

    beforeAll(() => {
        // One-time setup
    });

    afterAll(() => {
        // One-time cleanup
    });
});
```

### Avoiding Test Pollution

- Reset mocks between tests
- Don't share mutable state between tests
- Each test should be independent and runnable in isolation
- Use factories for test data

## Test Data

### Factories

```typescript
// Create test data factories
function createUser(overrides: Partial<User> = {}): User {
    return {
        id: 'user-1',
        name: 'Test User',
        email: 'test@example.com',
        ...overrides,
    };
}

// Usage
const user = createUser({ name: 'Custom Name' });
```

### Builders (for complex objects)

```typescript
class UserBuilder {
    private user: User = {
        id: 'user-1',
        name: 'Test User',
        email: 'test@example.com',
    };

    withName(name: string): this {
        this.user.name = name;
        return this;
    }

    withEmail(email: string): this {
        this.user.email = email;
        return this;
    }

    build(): User {
        return { ...this.user };
    }
}

// Usage
const user = new UserBuilder()
    .withName('John')
    .withEmail('john@example.com')
    .build();
```

## Snapshot Testing

**Use sparingly and intentionally:**

```typescript
it('renders correctly', () => {
    const { container } = render(Component);
    expect(container).toMatchSnapshot();
});
```

**When to use snapshots:**
- UI regression testing
- Serializable output verification

**When NOT to use snapshots:**
- Logic testing
- Frequently changing content

## Coverage

### Running Coverage

```bash
npm run test:coverage
```

### Coverage Targets

Aim for meaningful coverage, not 100%:
- Focus on critical paths and edge cases
- Don't test implementation details
- Test behavior, not code

## Best Practices

### Do

- Write tests that describe behavior
- Use descriptive test names
- Keep tests focused and small
- Test edge cases
- Make tests deterministic

### Don't

- Don't test implementation details
- Don't test private methods directly
- Don't make tests dependent on each other
- Don't ignore flaky tests (fix them)
- Don't over-mock

## Common Gotchas

### Async/Await

Always `await` async operations:

```typescript
// Wrong - test passes before async completes
it('loads data', () => {
    render(Component);
    expect(screen.getByText('Data')).toBeInTheDocument(); // May fail
});

// Correct
it('loads data', async () => {
    render(Component);
    expect(await screen.findByText('Data')).toBeInTheDocument();
});
```

### Timer Mocking

```typescript
beforeEach(() => {
    vi.useFakeTimers();
});

afterEach(() => {
    vi.useRealTimers();
});

it('debounces input', async () => {
    // ... trigger debounced action
    vi.advanceTimersByTime(500);
    // ... assert result
});
```
