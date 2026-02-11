Browser-based test plan format and mapping tables for agent-browser compatible E2E and DOM-based tests.

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
