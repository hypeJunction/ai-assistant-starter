# Mocking Patterns

MSW and store/state mocking patterns for Storybook stories.

## MSW for API Mocking

```typescript
import { http, HttpResponse } from 'msw';

export const WithData: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/users', () => {
          return HttpResponse.json([
            { id: 1, name: 'John' },
            { id: 2, name: 'Jane' },
          ]);
        }),
      ],
    },
  },
};

export const WithError: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/users', () => {
          return HttpResponse.json(
            { error: 'Server error' },
            { status: 500 }
          );
        }),
      ],
    },
  },
};
```

## Store/State Mocking

```typescript
// If using decorators for state providers
export const WithAuthenticatedUser: Story = {
  decorators: [
    (Story) => (
      <AuthProvider initialUser={{ id: 1, name: 'John' }}>
        <Story />
      </AuthProvider>
    ),
  ],
};
```
