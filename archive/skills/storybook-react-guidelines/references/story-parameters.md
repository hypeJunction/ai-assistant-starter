# Story Parameters

Reference for common Storybook story parameter configurations.

## Layout

```typescript
parameters: {
  layout: 'centered',    // Center in viewport
  layout: 'fullscreen',  // Fill viewport
  layout: 'padded',      // Add padding (default)
}
```

## Backgrounds

```typescript
parameters: {
  backgrounds: {
    default: 'dark',
    values: [
      { name: 'light', value: '#ffffff' },
      { name: 'dark', value: '#1a1a1a' },
    ],
  },
}
```

## Viewport

```typescript
parameters: {
  viewport: {
    defaultViewport: 'mobile1',
  },
}
```

## Disable Controls

```typescript
parameters: {
  controls: { disable: true },
}
```
