# Configuration Validation

## Required vs Optional

```typescript
const envSchema = z.object({
  // Required - no default, must be set
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),

  // Required with default - safe default value
  PORT: z.coerce.number().default({{DEFAULT_APP_PORT}}),
  LOG_LEVEL: z.string().default('info'),

  // Optional - may not be present
  SENTRY_DSN: z.string().url().optional(),

  // Conditionally required
  SMTP_HOST: z.string().optional(),
  SMTP_PASSWORD: z.string().optional(),
}).refine(
  (data) => {
    // If SMTP_HOST is set, SMTP_PASSWORD is required
    if (data.SMTP_HOST && !data.SMTP_PASSWORD) {
      return false;
    }
    return true;
  },
  { message: 'SMTP_PASSWORD required when SMTP_HOST is set' }
);
```

## Startup Validation

```typescript
// Validate all config at startup
function validateConfig() {
  const errors: string[] = [];

  // Required variables
  const required = ['DATABASE_URL', 'JWT_SECRET'];
  for (const key of required) {
    if (!process.env[key]) {
      errors.push(`Missing required environment variable: ${key}`);
    }
  }

  // Format validation
  if (process.env.DATABASE_URL && !process.env.DATABASE_URL.startsWith('postgres://')) {
    errors.push('DATABASE_URL must be a valid PostgreSQL URL');
  }

  // Numeric validation
  const port = Number(process.env.PORT);
  if (process.env.PORT && (isNaN(port) || port < 1 || port > 65535)) {
    errors.push('PORT must be a valid port number (1-65535)');
  }

  if (errors.length > 0) {
    console.error('Configuration errors:');
    errors.forEach(e => console.error(`  - ${e}`));
    process.exit(1);
  }
}

// Call at startup
validateConfig();
```

## Runtime Checks

```typescript
// For optional services, check at runtime
function getRedisClient() {
  if (!config.redis.enabled) {
    throw new Error('Redis is not configured. Set REDIS_URL to enable.');
  }
  return createRedisClient(config.redis.url);
}
```

## Example File

```bash
# .env.example - Commit this file
# Copy to .env.local and fill in values

# Application
NODE_ENV=development
PORT={{DEFAULT_APP_PORT}}
LOG_LEVEL=debug

# Database (required)
DATABASE_URL={{EXAMPLE_DATABASE_URL}}

# Redis (optional)
REDIS_URL=redis://{{DEFAULT_APP_HOST}}:{{DEFAULT_REDIS_PORT}}

# Authentication (required)
JWT_SECRET=your-32-char-secret-here
JWT_EXPIRES_IN=15m

# External Services
STRIPE_API_KEY=sk_test_...
SENDGRID_API_KEY=SG....

# Feature Flags
FEATURE_NEW_DASHBOARD=false
```
