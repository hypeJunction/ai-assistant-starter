---
name: env-config-guidelines
description: Environment configuration guidelines for Node.js including variable naming, type-safe loading with Zod, secrets management, and feature flags. Auto-loaded when working with environment config.
user-invocable: false
---

# Environment Configuration Guidelines

## Core Principles

1. **Fail fast** - Validate configuration at startup
2. **No secrets in code** - All secrets from environment
3. **Type safety** - Parse and validate env vars
4. **Defaults where safe** - Sensible defaults for non-sensitive values
5. **Documentation** - Every variable documented

## Environment Variable Naming

### Naming Convention

```bash
# Format: SCOPE_CATEGORY_NAME

# Application config
APP_PORT={{DEFAULT_APP_PORT}}
APP_HOST={{DEFAULT_APP_HOST}}
APP_LOG_LEVEL=info

# Database
DATABASE_URL={{EXAMPLE_DATABASE_URL}}
DATABASE_POOL_SIZE=10
DATABASE_SSL_ENABLED=true

# External services
REDIS_URL=redis://{{DEFAULT_APP_HOST}}:{{DEFAULT_REDIS_PORT}}
STRIPE_API_KEY=sk_test_xxx
SENDGRID_API_KEY=SG.xxx

# Feature flags
FEATURE_NEW_DASHBOARD=true
FEATURE_BETA_API=false
```

### Naming Rules

```bash
# Use SCREAMING_SNAKE_CASE
DATABASE_URL        # Good
databaseUrl         # Bad
database-url        # Bad

# Be specific
SMTP_HOST           # Good
HOST                # Bad - ambiguous

# Include units when relevant
CACHE_TTL_SECONDS=300
REQUEST_TIMEOUT_MS=5000
MAX_FILE_SIZE_MB=10
```

## Configuration Loading

### Type-Safe Configuration with Zod

```typescript
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default({{DEFAULT_APP_PORT}}),
  HOST: z.string().default('{{DEFAULT_APP_HOST}}'),
  DATABASE_URL: z.string().url(),
  STRIPE_API_KEY: z.string().startsWith('sk_'),
  FEATURE_NEW_DASHBOARD: z.coerce.boolean().default(false),
});

function loadConfig() {
  const result = envSchema.safeParse(process.env);
  if (!result.success) {
    console.error('Invalid environment configuration:');
    console.error(result.error.format());
    process.exit(1);
  }
  return result.data;
}

export const config = loadConfig();
export type Config = z.infer<typeof envSchema>;
```

## Environment Files

### File Structure

```bash
.env                  # Default values (committed, no secrets)
.env.local            # Local overrides (not committed)
.env.development      # Development defaults
.env.production       # Production defaults (no secrets)
.env.test             # Test environment
.env.example          # Template with all variables documented
```

### Loading Order

```typescript
// Load in order, later files override earlier
// 1. .env
// 2. .env.local
// 3. .env.{NODE_ENV}
// 4. .env.{NODE_ENV}.local
// 5. Process environment (highest priority)

import { config } from 'dotenv';
import { expand } from 'dotenv-expand';

const env = process.env.NODE_ENV || 'development';

[
  '.env',
  '.env.local',
  `.env.${env}`,
  `.env.${env}.local`,
].forEach(file => {
  expand(config({ path: file, override: true }));
});
```

## References

- [Secrets Management](references/secrets-management.md) - Gitignore rules, AWS SDK integration, secret rotation patterns
- [Feature Flags](references/feature-flags.md) - Simple and typed feature flag implementations
- [Configuration Patterns](references/config-patterns.md) - Per-environment config, config namespacing
- [Configuration Validation](references/config-validation.md) - Required vs optional, startup validation, runtime checks, example file
- [Known Gotchas](references/env-gotchas.md) - Boolean/number parsing, variable expansion, Docker environment
