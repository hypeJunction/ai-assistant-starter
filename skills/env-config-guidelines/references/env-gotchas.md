# Known Gotchas

## Boolean Parsing

```typescript
// Environment variables are always strings
process.env.FEATURE_ENABLED = 'false';

// Bad - always truthy (non-empty string)
if (process.env.FEATURE_ENABLED) { }  // true!

// Good - explicit comparison
if (process.env.FEATURE_ENABLED === 'true') { }

// Best - use Zod coercion
const schema = z.object({
  FEATURE_ENABLED: z.coerce.boolean().default(false),
});
```

## Number Parsing

```typescript
// Bad - NaN if not set
const port = parseInt(process.env.PORT);  // NaN

// Good - with fallback
const port = parseInt(process.env.PORT || '{{DEFAULT_APP_PORT}}', 10);

// Best - with validation
const port = z.coerce.number().default({{DEFAULT_APP_PORT}}).parse(process.env.PORT);
```

## Variable Expansion

```bash
# .env
BASE_URL=https://api.example.com
API_URL=${BASE_URL}/v1

# Requires dotenv-expand
import { expand } from 'dotenv-expand';
expand(config());
```

## Docker Environment

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - NODE_ENV=production
      - PORT=3000
    env_file:
      - .env.production

# Environment takes precedence over env_file
```
