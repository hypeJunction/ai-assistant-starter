---
name: vitest-guidelines
description: Testing guidelines for Vitest/Jest including test structure, mocking, async patterns, and Testing Library queries. Auto-loaded when working with test files.
category: guideline
user-invocable: false
---

# Testing Guidelines

## Test Framework

This project uses **Vitest** as the test runner.

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
```

## Test Structure

```typescript
describe('ComponentName', () => {
    it('sends form data to server when all fields are valid', async () => {
        const { getByRole, getByLabelText } = render(FormComponent);

        await userEvent.type(getByLabelText('Name'), 'John Doe');
        await userEvent.type(getByLabelText('Email'), 'john@example.com');
        await userEvent.click(getByRole('button', { name: 'Submit' }));

        expect(mockSubmit).toHaveBeenCalledWith({
            name: 'John Doe',
            email: 'john@example.com'
        });
    });
});
```

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

## Testing Library Queries

### Query Priority (Most to Least Preferred)

> **Note:** This is the canonical query priority reference. Other skills (e.g., `storybook-react-guidelines`) cross-reference this section.

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

- [Test Patterns](references/test-patterns.md) — Testing Library query details, async testing, user interactions, test isolation, test data, snapshots, and coverage
