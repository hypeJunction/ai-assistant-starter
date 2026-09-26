Detailed testing patterns including Testing Library query variants, async testing, user interactions, test isolation, test data factories, snapshots, and coverage.

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
