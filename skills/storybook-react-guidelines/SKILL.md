---
name: storybook-react-guidelines
description: Storybook guidelines for React including story structure, interaction tests with play functions, and Testing Library queries. Auto-loaded when working with story files.
user-invocable: false
---

# Storybook Guidelines (React)

## Overview

Storybook is used for:
- Component development in isolation
- Visual documentation of component states
- Interaction testing via play functions
- Accessibility auditing
- Visual regression testing

## Story File Structure

### Meta Configuration

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { MyComponent } from './MyComponent';

/**
 * Test Plan: MyComponent
 *
 * Scenario: Default rendering
 *   Given the component is mounted with default props
 *   Then it should display correctly
 *
 * Scenario: User interaction
 *   Given the component is mounted
 *   When the user clicks the button
 *   Then the state should update
 */

const meta: Meta<typeof MyComponent> = {
  title: 'Category/Subcategory/MyComponent',
  component: MyComponent,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'danger'] },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;
```

### Story Title Organization

```typescript
// Pattern: 'Category/Subcategory/ComponentName'
title: 'Components/Forms/TextInput'
title: 'Views/Dashboard/Overview'
title: 'Primitives/Controls/Button'
```

### Basic Stories

```typescript
export const Default: Story = {
  args: { label: 'Click me', variant: 'primary' },
};

export const Secondary: Story = {
  args: { ...Default.args, variant: 'secondary' },
};

// With custom render
export const WithIcon: Story = {
  args: { label: 'Save', icon: 'save' },
  render: (args) => (
    <div style={{ padding: '20px' }}>
      <MyComponent {...args} />
    </div>
  ),
};
```

## Interaction Tests with play()

### Basic Structure

```typescript
import { expect, userEvent, within, waitFor } from '@storybook/test';

export const Interactive: Story = {
  args: { label: 'Submit' },
  play: async ({ canvasElement, step }) => {
    const canvas = within(canvasElement);

    await step('Click the button', async () => {
      const button = canvas.getByRole('button', { name: 'Submit' });
      await userEvent.click(button);
    });

    await step('Verify state change', async () => {
      await waitFor(() => {
        expect(canvas.getByText('Submitted')).toBeInTheDocument();
      });
    });
  },
};
```

### Query Strategies

**Component-scoped queries:**
```typescript
const canvas = within(canvasElement);
const button = canvas.getByRole('button', { name: 'Submit' });
```

**Global queries (for modals, toasts, dropdowns):**
```typescript
import { screen } from '@storybook/test';
const modal = screen.getByRole('dialog');
const toast = screen.getByRole('status');
```

### Testing Library Query Priority

For Testing Library query priority, see `vitest-guidelines`.

## Async Handling

**Always use waitFor for async assertions:**
```typescript
await waitFor(() => {
  expect(canvas.getByText('Success')).toBeInTheDocument();
});
```

**Check for element removal:**
```typescript
await waitFor(() => {
  expect(canvas.queryByRole('alert')).not.toBeInTheDocument();
});
```

## Best Practices

### Story Naming and Organization

```typescript
// Good - descriptive states; visual states first, interactive tests last
export const Default: Story = { ... };
export const Disabled: Story = { ... };
export const WithError: Story = { ... };
export const Loading: Story = { ... };
export const UserFlow: Story = {
  play: async ({ canvasElement, step }) => { ... },
};

// Bad - vague or numbered
export const Story1: Story = { ... };
export const Test: Story = { ... };
```

### Test Plan Alignment

Every story with a `play()` function should have a corresponding test plan (see Meta Configuration example above for format).

## Common Pitfalls

- **Missing waitFor** — Always wrap async assertions in `waitFor()` after user interactions to avoid race conditions
- **Wrong query scope** — Use `within(canvasElement)` for component queries; use `screen` only for teleported elements (modals, toasts)
- **Toast vs Alert roles** — Success notifications use `role="status"`, errors use `role="alert"`
- **Global queries in component scope** — Modals/dropdowns are teleported outside the component; query them via `screen`, not `canvas`

## Running Storybook Tests

```bash
npm run storybook                                    # Start Storybook
npm run test-storybook                               # Run all story tests
npm run test-storybook -- --grep "ComponentName"     # Run specific tests
npm run test-storybook -- --coverage                 # With coverage
```

## Additional References

- [Common Interactions](references/common-interactions.md) — Button clicks, text input, checkboxes, selects, keyboard interactions
- [Mocking Patterns](references/mocking-patterns.md) — MSW API mocking and store/state mocking with decorators
- [Story Parameters](references/story-parameters.md) — Layout, backgrounds, viewport, and control parameters
