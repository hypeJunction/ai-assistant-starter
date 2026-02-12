# Secrets Management

## Never Commit Secrets

```gitignore
# .gitignore
.env.local
.env.*.local
.env.production
*.key
*.pem
credentials.json
```

## Secret Sources by Environment

```typescript
// Development: .env.local file
// CI/CD: GitHub Secrets, GitLab CI Variables
// Production: Secret manager (AWS Secrets Manager, Vault, etc.)

// Example: AWS Secrets Manager
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

async function loadSecrets() {
  if (process.env.NODE_ENV !== 'production') {
    return; // Use .env in development
  }

  const client = new SecretsManager({ region: 'us-east-1' });
  const response = await client.getSecretValue({
    SecretId: 'app/production/secrets',
  });

  const secrets = JSON.parse(response.SecretString!);

  // Inject into process.env
  Object.assign(process.env, secrets);
}
```

## Secret Rotation

```typescript
// Support multiple keys during rotation
const API_KEYS = (process.env.API_KEYS || '').split(',').filter(Boolean);

function validateApiKey(key: string): boolean {
  return API_KEYS.includes(key);
}

// Graceful handling during rotation
const DB_PASSWORDS = [
  process.env.DATABASE_PASSWORD,
  process.env.DATABASE_PASSWORD_OLD,
].filter(Boolean);

async function connectWithFallback() {
  for (const password of DB_PASSWORDS) {
    try {
      return await connect({ password });
    } catch (error) {
      continue;
    }
  }
  throw new Error('All database passwords failed');
}
```
