# Configuration Patterns

## Per-Environment Config

```typescript
interface DatabaseConfig {
  url: string;
  poolSize: number;
  ssl: boolean;
}

const databaseConfigs: Record<string, Partial<DatabaseConfig>> = {
  development: {
    poolSize: 5,
    ssl: false,
  },
  production: {
    poolSize: 20,
    ssl: true,
  },
  test: {
    poolSize: 1,
    ssl: false,
  },
};

export function getDatabaseConfig(): DatabaseConfig {
  const env = process.env.NODE_ENV || 'development';
  const defaults = databaseConfigs[env] || {};

  return {
    url: process.env.DATABASE_URL!,
    poolSize: Number(process.env.DATABASE_POOL_SIZE) || defaults.poolSize || 10,
    ssl: process.env.DATABASE_SSL === 'true' ?? defaults.ssl ?? false,
  };
}
```

## Config Namespacing

```typescript
// Organized config object
export const config = {
  app: {
    env: process.env.NODE_ENV || 'development',
    port: Number(process.env.PORT) || {{DEFAULT_APP_PORT}},
    host: process.env.HOST || '{{DEFAULT_APP_HOST}}',
  },
  database: {
    url: process.env.DATABASE_URL!,
    poolSize: Number(process.env.DATABASE_POOL_SIZE) || 10,
  },
  redis: {
    url: process.env.REDIS_URL,
    enabled: Boolean(process.env.REDIS_URL),
  },
  auth: {
    jwtSecret: process.env.JWT_SECRET!,
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '15m',
  },
  features: {
    newDashboard: process.env.FEATURE_NEW_DASHBOARD === 'true',
  },
} as const;
```
