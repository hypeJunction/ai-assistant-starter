# Common Interactions Catalogue

Reference for Storybook play function interaction patterns using `@storybook/test`.

## Button Click

```typescript
await step('Click submit button', async () => {
  const button = canvas.getByRole('button', { name: 'Submit' });
  await userEvent.click(button);
});
```

## Text Input

```typescript
await step('Enter email', async () => {
  const input = canvas.getByRole('textbox', { name: 'Email' });
  await userEvent.clear(input);
  await userEvent.type(input, 'test@example.com');
});
```

## Number Input

```typescript
await step('Enter quantity', async () => {
  const input = canvas.getByRole('spinbutton', { name: 'Quantity' });
  await userEvent.clear(input);
  await userEvent.type(input, '5');
});
```

## Checkbox/Toggle

```typescript
await step('Toggle checkbox', async () => {
  const checkbox = canvas.getByRole('checkbox', { name: 'Accept terms' });
  await userEvent.click(checkbox);
  expect(checkbox).toBeChecked();
});
```

## Select/Dropdown

```typescript
await step('Select option', async () => {
  const select = canvas.getByRole('combobox', { name: 'Country' });
  await userEvent.click(select);

  const option = screen.getByRole('option', { name: 'United States' });
  await userEvent.click(option);
});
```

## Keyboard Interaction

```typescript
await step('Submit with Enter key', async () => {
  const input = canvas.getByRole('textbox');
  await userEvent.type(input, 'test{Enter}');
});
```
