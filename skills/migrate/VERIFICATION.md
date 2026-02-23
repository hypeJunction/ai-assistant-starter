# Migrate Skill -- Verification Scenario

## Scenario: Adding a Required `phone` Column to Existing `users` Table

**Setup:** A developer needs to add a required `phone` column (NOT NULL, no default) to an existing `users` table with 50,000 rows. The project uses Prisma with PostgreSQL. They invoke:

```
/migrate add required phone column to users table
```

**Expected Outcome:** The agent detects this as a "Careful" risk migration, proposes a 3-step approach (add nullable, backfill, add NOT NULL constraint), generates separate migration files for each step, reviews the SQL, applies in dev, validates, and documents rollback.

---

## Key Checkpoints

### Phase 1: Assess

1. **Agent detects Prisma as the ORM** -- Finds `prisma/schema.prisma` during auto-detection (Step 1.1). Does not ask the user to specify `--orm`.
2. **Agent classifies risk as "Careful"** -- Adding a NOT NULL column to an existing table with data matches the "Careful" criteria: "add constraint to existing data." The assessment output states `Risk Level: Careful` with a reason referencing the 50,000 existing rows that would fail a NOT NULL constraint.

### Phase 2: Plan

3. **Agent proposes the 3-step pattern:**
   - (a) Add `phone` as a nullable column (`String?` in Prisma)
   - (b) Backfill existing rows with a user-specified value
   - (c) Add the NOT NULL constraint (change `String?` to `String`)
4. **Agent asks the user what the backfill value should be** -- Before generating any migration, the agent asks: what value should existing rows receive for `phone`? It does not assume a value like empty string or placeholder.

### Phase 3: Generate (Step 1 -- Nullable Column)

5. **Agent updates `schema.prisma` for step 1** -- Adds `phone String?` to the User model (nullable).
6. **Agent generates migration with `--create-only`** -- Runs `npx prisma migrate dev --name add_phone_nullable --create-only` so the SQL is generated but not applied.
7. **Agent shows the generated SQL for user review** -- Displays the `ALTER TABLE "users" ADD COLUMN "phone" TEXT` SQL and asks for approval before applying.

### Phase 4: Review + Apply (Step 1)

8. **Agent applies the migration in development** -- After user approves the SQL, runs `npx prisma migrate dev` to apply.

### Phase 3-5 (Step 2 -- Backfill)

9. **Agent creates a backfill migration as a separate file** -- Creates a standalone SQL file (e.g., `prisma/backfill-phone.sql`) with an `UPDATE users SET phone = '<user-specified-value>' WHERE phone IS NULL;` statement. This is NOT a Prisma schema migration. Applies with `npx prisma db execute --file ./prisma/backfill-phone.sql`.

### Phase 3-5 (Step 3 -- NOT NULL Constraint)

10. **Agent creates the constraint migration as a separate file** -- Updates `schema.prisma` to change `phone String?` to `phone String`, then runs `npx prisma migrate dev --name make_phone_required --create-only`. The generated SQL contains `ALTER TABLE "users" ALTER COLUMN "phone" SET NOT NULL`. Agent shows SQL for review, then applies.

### Phase 6: Validate

11. **Agent runs tests and typecheck** -- Executes the project's test suite and `npx tsc --noEmit` (or equivalent). Reports pass/fail for each.

### Phase 7: Document Rollback

12. **Agent documents rollback for each step** -- Provides reverse SQL and Prisma commands for all three steps:
    - Step 3 rollback: `ALTER TABLE "users" ALTER COLUMN "phone" DROP NOT NULL`
    - Step 2 rollback: `UPDATE users SET phone = NULL` (or note that data loss is acceptable)
    - Step 1 rollback: `ALTER TABLE "users" DROP COLUMN "phone"`
    - Each rollback is applied via `npx prisma db execute --file ./rollback.sql` and resolved with `npx prisma migrate resolve --rolled-back <name>`

---

## Anti-patterns

These are behaviors the agent must NOT exhibit during this scenario:

- **Must not add NOT NULL column without default in a single migration** -- This would fail on the 50,000 existing rows. The agent must detect this and use the 3-step pattern.
- **Must not combine schema migration and data migration in one file** -- The backfill (step 2) must be a separate SQL file from the schema changes (steps 1 and 3).
- **Must not skip the backfill value question** -- The agent must ask the user what value to use for existing rows. Backfilling with empty string, "unknown", or any arbitrary value without user input violates the skill instructions.
- **Must not apply without showing the SQL first** -- Every generated migration must be displayed for user review before applying. The `--create-only` flag must be used for Prisma migration generation.
- **Must not use `prisma migrate dev` without `--create-only` first** -- The generate step must always create the migration file first for review, then apply separately.
- **Must not suggest `npx prisma migrate reset` as the rollback command** -- `migrate reset` drops the entire database. The correct Prisma rollback approach is to write reverse SQL, apply with `npx prisma db execute --file`, and mark as rolled back with `npx prisma migrate resolve --rolled-back <name>`.

---

## Known Gaps (Pre-Improvement)

These gaps existed in the skill before improvements were applied:

1. **Prisma-specific workflow not spelled out** -- The 3-step NOT NULL pattern was described in generic SQL in `references/migration-patterns.md`, but the SKILL.md did not specify which Prisma commands to use for each step (e.g., when to use `--create-only`, how to run the backfill SQL file, how to update `schema.prisma` between steps).
2. **No backfill value guidance** -- The skill said "backfill" but did not instruct the agent to ask the user what value to use for existing rows, or warn against using empty/arbitrary values.
3. **Rollback command conflict** -- `SKILL.md` Phase 7 and `references/migration-patterns.md` listed `npx prisma migrate reset` as the Prisma rollback command, while `references/rollback-cookbook.md` correctly warned that this drops the entire database and recommended the manual 4-step approach (`db execute` + `migrate resolve`). The inconsistency could lead the agent to suggest a destructive rollback.
