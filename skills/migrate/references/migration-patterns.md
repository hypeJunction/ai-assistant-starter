Common migration patterns, ORM-specific commands, and zero-downtime strategies.

## Adding a Column

### Nullable Column (Safe)

```sql
ALTER TABLE users ADD COLUMN bio TEXT;
```

### Column with Default (Safe)

```sql
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
```

### NOT NULL Column on Existing Table (Careful -- 3-step)

```sql
-- Step 1: Add as nullable
ALTER TABLE users ADD COLUMN email_verified BOOLEAN;

-- Step 2: Backfill existing rows
UPDATE users SET email_verified = false WHERE email_verified IS NULL;

-- Step 3: Add NOT NULL constraint
ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;
```

## Renaming a Column (Careful -- 3-step)

Never rename in a single migration. Use the add-copy-drop pattern:

```sql
-- Migration 1: Add new column
ALTER TABLE users ADD COLUMN display_name VARCHAR(100);
UPDATE users SET display_name = username;

-- Deploy code that reads from BOTH columns, writes to BOTH

-- Migration 2: Drop old column (after all code is updated)
ALTER TABLE users DROP COLUMN username;
```

## Changing Column Type

### Safe Type Conversions

```sql
-- Widening (safe): VARCHAR(50) -> VARCHAR(255)
ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(255);

-- Integer widening (safe): INT -> BIGINT
ALTER TABLE orders ALTER COLUMN amount TYPE BIGINT;
```

### Unsafe Type Conversions (Careful -- use add-copy-drop)

```sql
-- String to integer, date format changes, etc.
-- Step 1: Add new column with target type
ALTER TABLE events ADD COLUMN starts_at TIMESTAMP WITH TIME ZONE;

-- Step 2: Backfill with type conversion
UPDATE events SET starts_at = start_date::TIMESTAMP WITH TIME ZONE;

-- Step 3: Drop old column (after code is updated)
ALTER TABLE events DROP COLUMN start_date;
```

## Adding an Index

### Standard Index (brief lock)

```sql
CREATE INDEX idx_users_email ON users(email);
```

### Concurrent Index (no lock -- PostgreSQL)

```sql
-- Does not block reads or writes, but takes longer
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
```

> **Note:** `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block.

### Composite Index

```sql
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);
```

## Dropping a Column (Dangerous)

Always verify no code references the column before dropping:

```bash
# Search for column references in application code
grep -rn "column_name" src/ --include="*.ts" --include="*.js"
grep -rn "column_name" prisma/ drizzle/ 2>/dev/null
```

```sql
-- Only after confirming no references
ALTER TABLE users DROP COLUMN legacy_field;
```

## Creating a Junction Table (Many-to-Many)

```sql
CREATE TABLE user_roles (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_role ON user_roles(role_id);
```

## Data Backfill Patterns

### Batched Updates (for large tables)

```sql
-- Process in batches to avoid long locks
DO $$
DECLARE
  batch_size INT := 1000;
  rows_updated INT;
BEGIN
  LOOP
    UPDATE users
    SET full_name = first_name || ' ' || last_name
    WHERE full_name IS NULL
    AND id IN (
      SELECT id FROM users WHERE full_name IS NULL LIMIT batch_size
    );

    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    EXIT WHEN rows_updated = 0;

    RAISE NOTICE 'Updated % rows', rows_updated;
    COMMIT;
  END LOOP;
END $$;
```

### Backfill with Application Code

```typescript
// For complex transformations, use application logic
const BATCH_SIZE = 1000;
let offset = 0;

while (true) {
  const rows = await db.query(
    `SELECT id, raw_data FROM records WHERE processed_data IS NULL LIMIT $1 OFFSET $2`,
    [BATCH_SIZE, offset]
  );

  if (rows.length === 0) break;

  for (const row of rows) {
    const processed = transformData(row.raw_data);
    await db.query(
      `UPDATE records SET processed_data = $1 WHERE id = $2`,
      [processed, row.id]
    );
  }

  offset += BATCH_SIZE;
  console.log(`Processed ${offset} records`);
}
```

## Zero-Downtime Migration (Expand-Contract)

The expand-contract pattern allows schema changes without downtime:

```
Phase 1: EXPAND -- add new structure alongside old
  - Add new column/table
  - Deploy code that writes to BOTH old and new
  - Backfill new from old

Phase 2: MIGRATE -- shift reads to new structure
  - Deploy code that reads from new, writes to both
  - Verify new structure is correct

Phase 3: CONTRACT -- remove old structure
  - Deploy code that only uses new
  - Drop old column/table
```

### Example: Renaming `username` to `display_name`

```
Step 1: ALTER TABLE users ADD COLUMN display_name VARCHAR(100);
Step 2: UPDATE users SET display_name = username;
Step 3: Deploy code reading both, writing both
Step 4: Deploy code reading display_name only
Step 5: ALTER TABLE users DROP COLUMN username;
```

## ORM-Specific Commands

| Operation | Prisma | Drizzle | Knex | TypeORM |
|-----------|--------|---------|------|---------|
| Generate migration | `npx prisma migrate dev --name <n> --create-only` | `npx drizzle-kit generate` | `npx knex migrate:make <n>` | `npx typeorm migration:generate src/migrations/<N>` |
| Apply migration | `npx prisma migrate dev` | `npx drizzle-kit migrate` | `npx knex migrate:latest` | `npx typeorm migration:run` |
| Rollback migration | `npx prisma migrate reset` | Manual (no built-in rollback) | `npx knex migrate:rollback` | `npx typeorm migration:revert` |
| View status | `npx prisma migrate status` | `npx drizzle-kit check` | `npx knex migrate:status` | `npx typeorm migration:show` |
| Pull current schema | `npx prisma db pull` | N/A (code-first) | N/A | `npx typeorm schema:log` |
| Push schema (no file) | `npx prisma db push` | `npx drizzle-kit push` | N/A | `npx typeorm schema:sync` |
| Generate client | `npx prisma generate` | N/A (auto) | N/A | N/A |

## Raw SQL Migration File Template

```sql
-- migrations/YYYYMMDDHHMMSS_description.sql

-- UP
BEGIN;

-- [migration SQL here]

COMMIT;

-- DOWN (rollback)
-- BEGIN;
-- [reverse SQL here]
-- COMMIT;
```
