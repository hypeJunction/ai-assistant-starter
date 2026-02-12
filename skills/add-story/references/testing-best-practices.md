# Testing Best Practices

## MSW Mocking for API Dependencies

```typescript
import { http, HttpResponse } from 'msw';

export const WithApiData: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/data', () => {
          return HttpResponse.json({ items: [...] });
        }),
      ],
    },
  },
};

export const WithApiError: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/data', () => {
          return HttpResponse.json({ error: 'Failed' }, { status: 500 });
        }),
      ],
    },
  },
};
```

## Testing Library Query Priority

```typescript
// Preferred - accessibility-first queries
canvas.getByRole('button', { name: 'Submit' });
canvas.getByRole('textbox', { name: 'Email' });
canvas.getByRole('checkbox', { name: 'Accept' });

// For teleported elements (modals, toasts)
import { screen } from '@storybook/test';
screen.getByRole('dialog');
screen.getByRole('status'); // Toast notifications
screen.getByRole('alert');  // Error messages
```

## Async Handling

```typescript
// Always wrap state changes in waitFor
await userEvent.click(button);
await waitFor(() => {
  expect(screen.getByText('Updated')).toBeInTheDocument();
});

// Check element removal
await waitFor(() => {
  expect(canvas.queryByRole('alert')).not.toBeInTheDocument();
});
```

## Story Factory Pattern for Tests

```typescript
const createStory = (args: Partial<Props>, config: Partial<Story> = {}): Story => ({
  args: { ...defaultArgs, ...args },
  ...config,
});

export const Default: Story = createStory({});
export const Disabled: Story = createStory({ disabled: true });
export const WithPlay: Story = createStory({}, {
  play: async ({ canvasElement }) => { ... },
});
```

## Running Tests

```bash
npm run test-storybook -- --grep "ComponentName"
```

Fix failures by:
- Checking query selectors match actual DOM
- Ensuring waitFor wraps async assertions
- Validating test data matches component expectations
- Verifying mock setup is correct

Re-run tests until all pass.

## Example Workflow Execution

```
1. User: "Add story for LoginForm"

2. Read LoginForm.tsx:
   - Props: onSubmit, initialEmail, loading, error
   - States: default, loading, error, success
   - Behavior: validates email, submits form

3. Create test plan:
   - Scenario 1: Default rendering
   - Scenario 2: Submit with valid credentials
   - Scenario 3: Submit with invalid credentials
   - Scenario 4: Loading state
   - Scenario 5: Error state

4. Write LoginForm.stories.tsx:
   - Import component and types
   - Configure meta with title, component, parameters
   - Create Default story
   - Create Loading story
   - Create WithError story

5. Write play functions:
   - SubmitValid: enter valid email/password, click submit, verify success
   - SubmitInvalid: enter invalid data, click submit, verify error

6. Run tests:
   npm run test-storybook -- --grep "LoginForm"

7. Fix failures if any, re-run tests

8. All tests pass - done
```
