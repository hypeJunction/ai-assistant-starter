# Feature Flags

## Simple Feature Flags

```typescript
// Environment-based flags
const features = {
  newDashboard: process.env.FEATURE_NEW_DASHBOARD === 'true',
  betaApi: process.env.FEATURE_BETA_API === 'true',
  darkMode: process.env.FEATURE_DARK_MODE === 'true',
};

// Usage
if (features.newDashboard) {
  return <NewDashboard />;
}
return <Dashboard />;
```

## Typed Feature Flags

```typescript
const featureFlagSchema = z.object({
  FEATURE_NEW_DASHBOARD: z.coerce.boolean().default(false),
  FEATURE_BETA_API: z.coerce.boolean().default(false),
  FEATURE_MAX_ITEMS: z.coerce.number().default(100),
});

export const features = featureFlagSchema.parse(process.env);

// Type-safe access
if (features.FEATURE_NEW_DASHBOARD) {
  // ...
}
```
