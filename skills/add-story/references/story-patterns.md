# Story Patterns

## Basic Story Structure

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

## Play Functions for Interactions

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

## Story Factory Pattern

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

## Test Plan Format

Document all meaningful component states at the top of the story file:

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
