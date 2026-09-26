# Rollback Cookbook

ORM-specific rollback commands, expand-contract rollback patterns, data restoration, and emergency rollback procedures.

## ORM-Specific Rollback Commands

### Prisma

```bash
# Rollback all migrations (reset to empty database)
npx prisma migrate reset
# WARNING: This drops all data. Use only in development.

# Rollback to a specific migration
npx prisma migrate resolve --rolled-back <migration_name>
# Then manually apply the reverse SQL

# View migration status
npx prisma migrate status

# Re-apply after rollback
npx prisma migrate dev
```

**Prisma limitations:**
- No built-in single-migration rollback
- `migrate reset` drops the entire database and re-applies all migrations
- For selective rollback, write reverse SQL manually and apply with `prisma.$executeRaw`

**Recommended approach for Prisma rollback:**
1. Write the reverse migration SQL manually
2. Apply it: `npx prisma db execute --file ./rollback.sql`
3. Mark the migration as rolled back: `npx prisma migrate resolve --rolled-back <name>`
4. Delete the migration directory from `prisma/migrations/`

### Drizzle

```bash
# Drizzle has no built-in rollback command
# You must write reverse migrations manually

# View current state
npx drizzle-kit check

# Push schema changes (bypasses migration files)
npx drizzle-kit push
```

**Drizzle rollback approach:**
1. Revert the schema file changes in code (`git checkout -- src/db/schema.ts`)
2. Generate a new migration: `npx drizzle-kit generate`
3. Apply it: `npx drizzle-kit migrate`

### Knex

```bash
# Rollback the last batch of migrations
npx knex migrate:rollback

# Rollback all migrations
npx knex migrate:rollback --all

# Rollback to a specific migration
npx knex migrate:down <migration_name>.ts

# View migration status
npx knex migrate:status

# Re-apply after rollback
npx knex migrate:latest
```

**Knex advantages:**
- Every migration has `up()` and `down()` functions
- `down()` is the rollback — always write it when creating migrations
- Batch rollback: rolls back all migrations in the last batch together

### TypeORM

```bash
# Revert the last migration
npx typeorm migration:revert

# Run again to revert the one before that
npx typeorm migration:revert

# View migration status
npx typeorm migration:show

# Re-apply after rollback
npx typeorm migration:run
```

**TypeORM advantages:**
- Every migration has `up()` and `down()` methods
- Single-migration revert with clear ordering
- Can revert multiple migrations by running `revert` repeatedly

### Raw SQL

```bash
# Apply rollback SQL manually
psql -d $DATABASE_URL -f migrations/rollback_<timestamp>.sql

# Or with a specific database
psql -h localhost -U postgres -d mydb -f rollback.sql

# MySQL equivalent
mysql -u root -p mydb < rollback.sql
```

**Always write DOWN SQL when writing UP SQL:**
```sql
-- UP
ALTER TABLE users ADD COLUMN bio TEXT;

-- DOWN (save alongside or in the same file)
ALTER TABLE users DROP COLUMN bio;
```

## Expand-Contract Rollback

When using the expand-contract pattern, rollback depends on which phase you're in:

### Rolling Back Phase 1 (EXPAND)

You added new structures alongside old ones. Code still uses old structures.

```
Rollback: Drop the new column/table. No data loss (new structure was empty or had copies).
```

```sql
-- Rolled back: drop the new column
ALTER TABLE users DROP COLUMN display_name;
```

**Risk:** Low — no production data in the new structure yet.

### Rolling Back Phase 2 (MIGRATE)

Code reads from new structure, writes to both. Rollback is more complex.

```
Rollback:
1. Revert application code to read from old structure only
2. Backfill any data written to new structure back to old (if formats differ)
3. Keep new structure for now (clean up later)
```

**Risk:** Medium — data may have been written to new structure that needs to be preserved.

### Rolling Back Phase 3 (CONTRACT)

Old structure has been dropped. This is the hardest to rollback.

```
Rollback:
1. Re-create the old column/table
2. Backfill from new structure to old
3. Revert application code to use old structure
4. This is essentially a new migration forward, not a true rollback
```

**Risk:** High — requires a forward migration to restore the old structure. Consider whether a forward fix is safer.

## Data Restoration Patterns

### Point-in-Time Recovery (PostgreSQL)

```bash
# If continuous archiving is configured
pg_restore --target-time="2025-01-15 14:30:00" -d mydb backup.dump

# From a full backup
pg_restore -d mydb --clean --if-exists latest_backup.dump
```

### Table-Level Backup Before Migration

```sql
-- Before running a dangerous migration, backup the affected table
CREATE TABLE users_backup_20250115 AS SELECT * FROM users;

-- After verifying migration succeeded, drop the backup
DROP TABLE users_backup_20250115;

-- If rollback needed, restore from backup
INSERT INTO users SELECT * FROM users_backup_20250115;
```

### Row-Level Backup for Data Migrations

```sql
-- Before a data transformation, save original values
ALTER TABLE users ADD COLUMN _old_email TEXT;
UPDATE users SET _old_email = email;

-- After migration succeeds, drop the backup column
ALTER TABLE users DROP COLUMN _old_email;

-- If rollback needed
UPDATE users SET email = _old_email;
ALTER TABLE users DROP COLUMN _old_email;
```

## Emergency Rollback Checklist

When a migration has gone wrong in production:

### 1. Assess Impact
- [ ] Is the application still running?
- [ ] Are users affected?
- [ ] Is data being corrupted or lost?
- [ ] Can the application function with the new schema?

### 2. Decide: Rollback or Forward-Fix?

| Scenario | Recommendation |
|----------|---------------|
| Application is down, schema is broken | Rollback immediately |
| Application works but data is wrong | Forward-fix (correct the data) |
| Performance degradation from new index | Drop the index (targeted rollback) |
| New column has wrong default | Update the default (forward-fix) |
| Dropped column that code still references | Restore from backup (emergency rollback) |

### 3. Execute Rollback
- [ ] Notify the team that rollback is in progress
- [ ] Apply rollback SQL or run ORM rollback command
- [ ] Verify schema state matches pre-migration state
- [ ] Verify application starts and responds correctly
- [ ] Check for data integrity (row counts, critical records)
- [ ] Monitor error rates for 15 minutes

### 4. Post-Rollback
- [ ] Document what went wrong
- [ ] Update the migration to fix the issue
- [ ] Test on staging before re-applying to production
- [ ] Schedule post-mortem if the issue caused downtime

## When NOT to Rollback

Sometimes rolling forward is safer than rolling back:

| Situation | Why Forward is Better |
|-----------|----------------------|
| Data has been transformed irreversibly | Rollback would lose transformed data |
| Phase 3 (contract) already completed | Re-creating old structure is a new migration |
| Other migrations depend on this one | Rollback would cascade to dependent migrations |
| The fix is a one-line default value change | Faster to fix than to rollback and retry |
| Users have already written data to new schema | Rolling back would lose their data |

**Rule of thumb:** If rollback requires more steps than the fix, fix forward.
