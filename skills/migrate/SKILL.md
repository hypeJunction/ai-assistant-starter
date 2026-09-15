---
name: migrate
description: Safe database/schema migration workflow with risk assessment, rollback planning, and ORM-aware generation. Use for schema changes, adding/removing columns, creating tables, adding indexes, or data backfills.
category: process
model: sonnet
effort: high
triggers:
  - database migration
  - schema change
  - add column
  - create table
  - add index
  - data backfill
---

# Migrate

> **Purpose:** Safe database/schema migration workflow
> **Phases:** Assess -> Plan -> Generate -> Review -> Apply -> Validate -> Document Rollback
> **Usage:** `/migrate [scope flags] <description of schema change>`

## Iron Laws

1. **NEVER APPLY WITHOUT REVIEWING GENERATED SQL** -- Always inspect the actual SQL/migration file before running it. Auto-applying migrations leads to data loss.
2. **EVERY DESTRUCTIVE MIGRATION NEEDS A ROLLBACK PLAN** -- Column drops, table drops, type changes must have documented rollback steps before execution.
3. **NEVER MIGRATE PRODUCTION WITHOUT TESTING ON A COPY** -- Test migrations against a clone/staging environment first. Production is not a test environment.

## When to Use

- Schema changes (add/remove/alter columns, tables, indexes)
- Creating new tables or junction tables
- Adding or removing indexes and constraints
- Changing column types or defaults
- Data backfill migrations

## When NOT to Use

- Application code changes (no schema impact) -> `/implement`
- Query optimization without schema changes -> direct edit
- Seeding test/dev data -> direct script
- ORM configuration or connection changes -> `/implement`

## Never Do

- **Never drop a column without first verifying no code references it** -- Search the codebase for all usages before generating the migration
- **Never rename a column in a single migration** -- Use the add-copy-drop pattern (see `references/migration-patterns.md`)
- **Never add a NOT NULL column without a default value** -- Existing rows will fail the constraint; add as nullable, backfill, then add constraint
- **Never run migrations in a transaction with DDL in databases that don't support transactional DDL** -- MySQL and older PostgreSQL versions may auto-commit DDL
- **Never run a data migration and schema migration in the same file** -- Separate concerns for safer rollback
- **Never assume migration order across branches** -- Coordinate with teammates on migration timestamps

## Gate Enforcement

See `ai-assistant-protocol` for valid approval terms and invalid responses.

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Scope Flags

| Flag | Description |
|------|-------------|
| `--orm=<tool>` | Migration tool: `prisma`, `drizzle`, `typeorm`, `knex`, `raw` |
| `--env=<target>` | Target environment: `development` (default), `staging`, `production` |
| `--dry-run` | Generate and review only, do not apply |

**Examples:**
```bash
/migrate --orm=prisma add email_verified boolean to users table
/migrate --orm=drizzle create posts table with title, body, author_id
/migrate --env=staging --orm=knex add composite index on orders(user_id, created_at)
/migrate --dry-run drop legacy_sessions table
```

---

## Phase 1: Assess

**Mode:** Read-only -- detect tooling, review current state, classify risk.

### Step 1.1: Detect ORM / Migration Tool

If `--orm` is not specified, auto-detect by checking for:

```bash
ls prisma/schema.prisma 2>/dev/null        # Prisma
ls drizzle.config.* 2>/dev/null             # Drizzle
ls knexfile.* 2>/dev/null                   # Knex
ls ormconfig.* 2>/dev/null                  # TypeORM
ls src/data-source.* 2>/dev/null            # TypeORM (newer)
ls migrations/ 2>/dev/null                  # Raw SQL
```

If no tool is detected, ask the user.

### Step 1.2: Review Current Schema State

```bash
# Prisma
npx prisma db pull --print 2>/dev/null

# Drizzle -- read schema files
cat src/db/schema.ts 2>/dev/null

# Knex -- check latest migration
ls -la migrations/ 2>/dev/null

# TypeORM -- read entity files
ls src/entities/ 2>/dev/null
```

### Step 1.3: Classify Migration Risk

```markdown
## Migration Assessment

**Tool:** [detected ORM/tool]
**Change:** [description of schema change]

**Risk Classification:**

| Risk Level | Criteria | This Migration |
|------------|----------|----------------|
| Safe | Add column with default, add table, add index | |
| Careful | Rename, type change, add constraint to existing data | |
| Dangerous | Drop column, drop table, data migration on large table | |

**Risk Level: [Safe / Careful / Dangerous]**
**Reason:** [why this risk level]
```

---

## Phase 2: Plan

**Mode:** Read-only -- design migration strategy based on risk level.

### Step 2.1: Design Migration Strategy

**For Safe migrations:** Single migration file.

**For Careful migrations:** Multi-step approach:
1. Add new column/table
2. Backfill data (separate migration)
3. Update application code
4. Drop old column/table (separate migration)

**For Dangerous migrations:** Mandatory rollback plan + user approval before proceeding.

See `references/migration-patterns.md` for detailed patterns.

### Step 2.2: Present Migration Plan

```markdown
## Migration Plan

**Change:** [what will change]
**Risk:** [Safe / Careful / Dangerous]
**Steps:**

1. [Step 1 description]
2. [Step 2 description]
3. [Step N description]

**Rollback Strategy:** [how to undo if something goes wrong]

**Estimated Impact:**
- Tables affected: [list]
- Rows affected: [estimate if data migration]
- Downtime required: [none / brief lock / extended]

---
**Approve plan?** (yes / no / modify)
```

**GATE: Wait for explicit approval before generating migration files.**

---

## Phase 3: Generate

**Mode:** Write access -- create migration files using the project's tooling.

### Step 3.1: Generate Migration File

Use the detected ORM tool to generate the migration:

**Prisma:**
```bash
# Update schema.prisma first, then generate
npx prisma migrate dev --name <descriptive_name> --create-only
```

**Drizzle:**
```bash
# Update schema file first, then generate
npx drizzle-kit generate
```

**Knex:**
```bash
npx knex migrate:make <descriptive_name>
# Then edit the generated file with migration logic
```

**TypeORM:**
```bash
npx typeorm migration:generate src/migrations/<DescriptiveName>
```

**Raw SQL:**
Create a timestamped migration file:
```bash
# Format: YYYYMMDDHHMMSS_description.sql
touch migrations/$(date +%Y%m%d%H%M%S)_<description>.sql
```
Then write the up and down SQL in the file.

### Prisma: Adding NOT NULL Column to Existing Table

When adding a NOT NULL column to a table with existing data, use a 3-step migration. Never add it in a single migration -- existing rows will fail the constraint.

**Step 1 -- Add nullable column:**
- Update `schema.prisma`: add the field as optional (e.g., `phone String?`)
- Generate: `npx prisma migrate dev --name add_phone_nullable --create-only`
- Review the generated SQL (`ALTER TABLE ... ADD COLUMN`)
- Apply: `npx prisma migrate dev`

**Step 2 -- Backfill existing rows:**
- Create a standalone SQL file (e.g., `prisma/backfill-phone.sql`) -- this is NOT a Prisma schema migration
- Write the UPDATE statement with the user-specified value
- Apply: `npx prisma db execute --file ./prisma/backfill-phone.sql`

**Step 3 -- Add NOT NULL constraint:**
- Update `schema.prisma`: remove the `?` to make the field required (e.g., `phone String`)
- Generate: `npx prisma migrate dev --name make_phone_required --create-only`
- Review the generated SQL (`ALTER TABLE ... SET NOT NULL`)
- Apply: `npx prisma migrate dev`

Each step is a separate migration file. Never combine schema and data migrations.

### Backfill Value Guidance

When a migration requires backfilling existing rows, always ask the user before proceeding:

1. **What default value should existing rows receive?** (e.g., a literal value like `"unknown"`, `0`, `false`)
2. **Should it be a computed value?** (e.g., derived from another column, a UUID, a timestamp)
3. **Is there a business rule?** (e.g., "use the user's email domain", "set to the team default")

Never backfill with empty string, placeholder values, or arbitrary defaults without explicit user input. The backfill value is a business decision, not a technical default.

### Step 3.2: Verify File Was Created

```bash
# List recent migration files
ls -lt migrations/ | head -5
# or for Prisma
ls -lt prisma/migrations/ | head -5
```

---

## Phase 4: Review

**Mode:** Read-only -- inspect generated SQL before applying.

### Step 4.1: Read Generated Migration

Read the generated migration file and display its contents.

### Step 4.2: Verify SQL Matches Intent

```markdown
## Migration Review

**File:** [path to migration file]

**SQL Operations:**
1. [operation 1 -- e.g., CREATE TABLE ...]
2. [operation 2 -- e.g., ADD COLUMN ...]

**Safety Checks:**
- [ ] SQL matches the intended change
- [ ] No unexpected DROP or ALTER operations
- [ ] Default values are correct
- [ ] Indexes are appropriate
- [ ] No data loss risk

**Dangerous Operations Found:** [none / list any DROP, ALTER TYPE, TRUNCATE]
```

### Step 4.3: Present for User Review

```markdown
## Generated SQL

\`\`\`sql
[actual SQL content]
\`\`\`

**Does this look correct?** (yes / no / edit)
```

**GATE: Wait for explicit approval before applying the migration.**

---

## Phase 5: Apply

**Mode:** Write access -- run migration in the target environment.

### Step 5.1: Confirm Environment

```markdown
**Applying migration to: [development / staging]**
```

> If `--env=production`, **STOP** and warn:
> ```
> WARNING: You are about to apply a migration to PRODUCTION.
> This should be tested on staging first.
> **Confirm:** Type `APPLY PRODUCTION` to proceed.
> ```

### Step 5.2: Run Migration

**Delegate to a subagent** — Run this via the `Agent` tool (an independent subagent), never directly in the main agent's shell. Give the subagent the exact command(s) and require full raw output back; read that output yourself before reporting results. See `ai-assistant-protocol` § Validation Execution.

**Prisma:**
```bash
npx prisma migrate dev
```

**Drizzle:**
```bash
npx drizzle-kit push
# or
npx drizzle-kit migrate
```

**Knex:**
```bash
npx knex migrate:latest
```

**TypeORM:**
```bash
npx typeorm migration:run
```

**Raw SQL:**
```bash
# Use project's migration runner or apply directly
psql -d $DATABASE_URL -f migrations/<file>.sql
```

### Step 5.3: Report Result

```markdown
## Migration Applied

**Status:** [Success / Failed]
**Output:**
\`\`\`
[migration command output]
\`\`\`
```

**If failed:** Do NOT proceed. Analyze the error and present options:
1. Fix and retry
2. Rollback to previous state
3. Abort

---

## Phase 6: Validate

**Mode:** Read-only + testing -- verify schema and application integrity.

### Step 6.1: Verify Schema State

**Prisma:**
```bash
npx prisma db pull --print
```

**Other tools:**
```bash
# Verify table/column exists as expected
# Tool-specific schema inspection commands
```

### Step 6.2: Run Tests

```bash
npm run test -- [affected-test-pattern]
npm run typecheck
```

### Step 6.3: Validation Report

```markdown
## Validation

| Check | Status |
|-------|--------|
| Schema matches intent | [Pass / Fail] |
| Existing tests | [Pass / Fail ({N} tests)] |
| Type check | [Pass / Fail] |
| Application connects | [Pass / Fail] |

**Issues found:** [none / list]
```

**GATE: All checks must pass before documenting rollback and committing.**

---

## Phase 7: Document Rollback

**Mode:** Write access -- create rollback documentation.

### Step 7.1: Generate Rollback Steps

For every migration, document the reverse operation. See `references/rollback-cookbook.md` for ORM-specific rollback commands, expand-contract rollback patterns, and the emergency rollback checklist.

```markdown
## Rollback Plan

**Migration:** [migration name/file]
**To rollback, run:**

\`\`\`bash
[rollback command -- see ORM-specific instructions below]
\`\`\`

**Manual rollback SQL (if needed):**

\`\`\`sql
[reverse SQL statements]
\`\`\`

**Post-rollback steps:**
1. [any code changes needed]
2. [any cache clearing needed]
3. [verification steps]
```

**ORM-specific rollback commands:**

| ORM | Rollback Command | Notes |
|-----|-----------------|-------|
| Prisma | Write reverse SQL, apply with `npx prisma db execute --file ./rollback.sql`, then `npx prisma migrate resolve --rolled-back <name>` | `prisma migrate reset` drops the entire database -- never use it as a targeted rollback |
| Knex | `npx knex migrate:rollback` | Rolls back the last batch; each migration has a `down()` function |
| TypeORM | `npx typeorm migration:revert` | Reverts the last migration; run repeatedly for multiple |
| Drizzle | Revert schema file, `npx drizzle-kit generate`, `npx drizzle-kit migrate` | No built-in rollback command |
| Raw SQL | `psql -d $DATABASE_URL -f rollback.sql` | Always write DOWN SQL alongside UP SQL |

See `references/rollback-cookbook.md` for detailed rollback procedures, expand-contract rollback patterns, and the emergency rollback checklist.

### Step 7.2: Commit

```markdown
## Ready to Commit

**Files changed:**
- [migration file path]
- [schema file path if updated]

**Message:**
\`\`\`
feat(db): [migration description]

[details of what changed]
Risk level: [safe/careful/dangerous]
Rollback: [brief rollback instructions]
\`\`\`

**Commit?** (yes / no / edit)
```

**GATE: User must approve before committing.**

---

## Quick Reference

| Phase | Mode | Gate |
|-------|------|------|
| 1. Assess | Read-only | Risk classified |
| 2. Plan | Read-only | **User approves plan** |
| 3. Generate | Write | Migration file created |
| 4. Review | Read-only | **User approves generated SQL** |
| 5. Apply | Write | Migration succeeds |
| 6. Validate | Testing | All checks pass |
| 7. Document Rollback | Write | **User approves commit** |

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| MIG-T1 | Positive | "Add a new column to the users table" | Skill triggers |
| MIG-T2 | Positive | "Create a posts table" | Skill triggers |
| MIG-T3 | Positive | "Database migration for adding indexes" | Skill triggers |
| MIG-T4 | Negative | "Fix the query performance" | Does NOT trigger (-> /debug or direct edit) |
| MIG-T5 | Negative | "Change the API response format" | Does NOT trigger (-> /implement) |
| MIG-T6 | Negative | "Seed the database with test data" | Does NOT trigger (direct script) |
| MIG-T7 | Boundary | "Rename the email column to user_email" | Triggers (schema change, uses add-copy-drop pattern) |

## References

- [Migration Patterns](references/migration-patterns.md) -- Common migration patterns, ORM command reference, and zero-downtime strategies
- [Rollback Cookbook](references/rollback-cookbook.md) -- ORM-specific rollback commands, expand-contract rollback, and emergency procedures
