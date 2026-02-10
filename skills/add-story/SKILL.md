---
name: add-story
description: Create comprehensive Storybook stories with test plans, play functions, and validated tests for a component. Use when a component needs Storybook coverage or story files.
---

# Add Story

> **Purpose:** Create comprehensive Storybook stories with test plans, play functions, and validated passing tests
> **Usage:** `/add-story <ComponentName or path>`

## Constraints

- **Do not modify the original component** without explicit permission
- **Do not run full test suites** (`npm test`) -- scope to the component
- **Do not use querySelector** in tests -- use Testing Library queries
- **Do not skip waitFor** for async assertions
- **Test plan must be included** at top of story file
- **Create play functions for all interactive scenarios**
- **Run tests and ensure they pass**
- **Use Testing Library queries** (getByRole, getByLabelText, etc.)
- **Scope tests appropriately** (canvas for component, screen for modals)

## Workflow

### Step 1: Read the Component Structure

- Read the component file to understand props, slots, events, and behavior
- Identify component states and variants
- Note any conditional rendering or dynamic behavior
- List dependencies (API calls, stores, context providers)

### Step 2: Create a Test Plan

Document all meaningful component states to cover:

```typescript
/**
 * Test Plan: ComponentName
 *
 * Scenario: Default rendering
 *   Given the component is mounted with default props
 *   Then it should display correctly
 *
 * Scenario: User interaction
 *   Given the component is mounted
 *   When the user clicks the button
 *   Then the state should update
 *
 * Scenario: Error state
 *   Given invalid input
 *   When validation runs
 *   Then error message appears
 */
```

### Step 3: Review Existing Patterns

Before writing stories:
- Check existing stories in the project for conventions
- Identify mocking requirements (MSW, stores, providers)
- Note the project's Storybook configuration

### Step 4: Write Stories for Visual States

Create stories covering all visual states:

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { MyComponent } from './MyComponent';

const meta: Meta<typeof MyComponent> = {
  title: 'Category/MyComponent',
  component: MyComponent,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

// Default state
export const Default: Story = {
  args: {
    label: 'Default label',
  },
};

// Variant states
export const Disabled: Story = {
  args: {
    ...Default.args,
    disabled: true,
  },
};

export const WithError: Story = {
  args: {
    ...Default.args,
    error: 'Validation failed',
  },
};

export const Loading: Story = {
  args: {
    ...Default.args,
    loading: true,
  },
};
```

### Step 5: Write Play Functions for Interactions

Add play functions for all interactive scenarios:

```typescript
import { expect, userEvent, within, waitFor } from '@storybook/test';

export const UserInteraction: Story = {
  args: Default.args,
  play: async ({ canvasElement, step }) => {
    const canvas = within(canvasElement);

    await step('User clicks button', async () => {
      const button = canvas.getByRole('button', { name: 'Submit' });
      await userEvent.click(button);
    });

    await step('Success state appears', async () => {
      await waitFor(() => {
        expect(canvas.getByText('Success')).toBeInTheDocument();
      });
    });
  },
};
```

### Step 6: Add Mocking If Required

For components with API dependencies:

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

### Step 7: Run Tests and Validate

**Required:** Run tests for the component:

```bash
npm run test-storybook -- --grep "ComponentName"
```

Fix any failures by:
- Checking query selectors match actual DOM
- Ensuring waitFor wraps async assertions
- Validating test data matches component expectations
- Verifying mock setup is correct

Re-run tests until all pass.

## Best Practices

### Story Factory Pattern

For stories sharing common setup:

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

### Testing Library Best Practices

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

### Async Handling

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

## Story File Checklist

Before completing:

- [ ] Test plan documented at top of file
- [ ] Meta configuration complete (title, component, parameters)
- [ ] Default story exists
- [ ] All visual states covered (disabled, loading, error, etc.)
- [ ] Play functions for interactive scenarios
- [ ] MSW handlers for API dependencies (if applicable)
- [ ] Tests pass locally
