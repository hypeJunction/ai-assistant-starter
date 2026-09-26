Reference for connection pooling, query performance optimization, and database security practices.

## Connection Management

### Connection Pooling

```typescript
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,  // Maximum connections in pool
  idleTimeoutMillis: 30000,  // Close idle connections after 30s
  connectionTimeoutMillis: 2000,  // Timeout for new connections
});

// Use pool for queries
export async function query<T>(
  text: string,
  params?: unknown[]
): Promise<T[]> {
  const result = await pool.query(text, params);
  return result.rows;
}

// For transactions, get dedicated client
export async function withTransaction<T>(
  fn: (client: PoolClient) => Promise<T>
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}
```

### Connection Limits

```typescript
// Configure based on environment
const poolConfig = {
  development: { max: 5 },
  test: { max: 2 },
  production: { max: 20 },
};

// Calculate: connections = (cores * 2) + effective_spindle_count
// For cloud: check provider limits
```

## Performance

### Query Analysis

```sql
-- Use EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE user_id = '123'
ORDER BY created_at DESC
LIMIT 10;

-- Look for:
-- - Seq Scan (might need index)
-- - High actual rows vs estimated
-- - Sort operations (might need index)
```

### Common Optimizations

```sql
-- Use EXISTS instead of COUNT for existence checks
-- Bad
SELECT COUNT(*) FROM orders WHERE user_id = $1;
if (count > 0) { ... }

-- Good
SELECT EXISTS(SELECT 1 FROM orders WHERE user_id = $1);

-- Use LIMIT for single row queries
-- Bad
SELECT * FROM users WHERE email = $1;

-- Good
SELECT * FROM users WHERE email = $1 LIMIT 1;

-- Batch inserts
-- Bad
INSERT INTO logs (message) VALUES ('msg1');
INSERT INTO logs (message) VALUES ('msg2');

-- Good
INSERT INTO logs (message) VALUES ('msg1'), ('msg2'), ('msg3');
```

## Security

### Least Privilege

```sql
-- Create application user with minimal permissions
CREATE USER app_user WITH PASSWORD 'xxx';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Separate user for migrations
CREATE USER migration_user WITH PASSWORD 'xxx';
GRANT ALL PRIVILEGES ON DATABASE app TO migration_user;
```

### Row Level Security

```sql
-- Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy for user access
CREATE POLICY documents_user_policy ON documents
  FOR ALL
  USING (user_id = current_setting('app.current_user_id')::uuid);

-- Set user context
SET app.current_user_id = 'user-123';
SELECT * FROM documents;  -- Only sees own documents
```
