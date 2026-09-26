Reference for database migration structure, safe practices, and data migrations.

## Migrations

### Migration Structure

```typescript
// migrations/001_create_users.ts
export async function up(db: Database): Promise<void> {
  await db.query(`
    CREATE TABLE users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email VARCHAR(255) UNIQUE NOT NULL,
      name VARCHAR(100) NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    CREATE INDEX idx_users_email ON users(email);
  `);
}

export async function down(db: Database): Promise<void> {
  await db.query('DROP TABLE users');
}
```

### Safe Migration Practices

```sql
-- Add columns as nullable first
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Then add constraint after backfill
UPDATE users SET phone = 'unknown' WHERE phone IS NULL;
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

-- Add indexes concurrently (no locks)
CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone);

-- Rename with alias period
ALTER TABLE old_name RENAME TO new_name;
-- Keep old name as view temporarily
CREATE VIEW old_name AS SELECT * FROM new_name;
-- Drop view after migration complete
```

### Data Migrations

```typescript
// Separate data migrations from schema migrations
export async function up(db: Database): Promise<void> {
  // Add new column
  await db.query('ALTER TABLE users ADD COLUMN full_name VARCHAR(200)');

  // Backfill in batches
  let processed = 0;
  while (true) {
    const result = await db.query(`
      UPDATE users
      SET full_name = first_name || ' ' || last_name
      WHERE full_name IS NULL
      LIMIT 1000
      RETURNING id
    `);

    processed += result.rowCount;
    if (result.rowCount === 0) break;

    console.log(`Migrated ${processed} users`);
  }
}
```
