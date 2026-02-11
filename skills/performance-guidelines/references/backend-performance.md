Additional backend performance techniques covering caching, connection pooling, and async processing patterns.

### Caching Strategies

```typescript
// In-memory cache with TTL
const cache = new Map<string, { value: unknown; expires: number }>();

function getCached<T>(key: string): T | undefined {
  const entry = cache.get(key);
  if (entry && entry.expires > Date.now()) {
    return entry.value as T;
  }
  cache.delete(key);
  return undefined;
}

function setCache<T>(key: string, value: T, ttlMs: number): void {
  cache.set(key, { value, expires: Date.now() + ttlMs });
}

// Usage with cache-aside pattern
async function getUser(id: string): Promise<User> {
  const cacheKey = `user:${id}`;

  const cached = getCached<User>(cacheKey);
  if (cached) return cached;

  const user = await db.users.findUnique({ where: { id } });
  if (user) {
    setCache(cacheKey, user, 5 * 60 * 1000); // 5 minutes
  }

  return user;
}
```

### Connection Pooling

```typescript
// Database connection pool
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,           // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Query with pool
async function query<T>(sql: string, params?: unknown[]): Promise<T[]> {
  const client = await pool.connect();
  try {
    const result = await client.query(sql, params);
    return result.rows;
  } finally {
    client.release();
  }
}
```

### Async Processing

```typescript
// Move heavy work to background jobs
import { Queue } from 'bull';

const emailQueue = new Queue('email', process.env.REDIS_URL);

// Instead of processing inline
app.post('/register', async (req, res) => {
  const user = await createUser(req.body);

  // Queue email instead of sending inline
  await emailQueue.add('welcome', { userId: user.id });

  res.status(201).json({ data: user });
});

// Process in background
emailQueue.process('welcome', async (job) => {
  const user = await db.users.findUnique({ where: { id: job.data.userId } });
  await sendWelcomeEmail(user);
});
```
