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

## Additional References

- [Browser-Based Test Plans](references/browser-test-plans.md) — Agent-browser compatible test plan format with locator, action, and assertion mapping tables
- [Test Patterns](references/test-patterns.md) — Testing Library query details, async testing, user interactions, test isolation, test data, snapshots, and coverage
