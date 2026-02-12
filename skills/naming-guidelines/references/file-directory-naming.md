# File & Directory Naming

## File Names

```typescript
// Components: PascalCase
UserProfile.tsx
OrderSummary.vue
NavigationMenu.svelte

// Utilities/Helpers: camelCase or kebab-case
formatDate.ts
validate-email.ts
useLocalStorage.ts

// Tests: match source file
UserProfile.spec.tsx
formatDate.test.ts

// Index files
index.ts  // Re-exports

// Types: often separate file
types.ts
user.types.ts
```

## Directory Structure

```
src/
├── components/     # React/Vue components
│   ├── common/     # Shared components
│   └── features/   # Feature-specific
├── hooks/          # Custom hooks
├── services/       # API/business logic
├── utils/          # Utility functions
├── types/          # Type definitions
├── constants/      # Constant values
└── pages/          # Page components
```

## CSS/Styling

```css
/* BEM naming */
.block {}
.block__element {}
.block--modifier {}

/* Examples */
.card {}
.card__header {}
.card__body {}
.card--featured {}
.card--compact {}
```

## Environment Variables

```bash
# SCREAMING_SNAKE_CASE
DATABASE_URL=postgres://...
API_KEY=xxx
NODE_ENV=production
FEATURE_FLAG_NEW_UI=true
```
