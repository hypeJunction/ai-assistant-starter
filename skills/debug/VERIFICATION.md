# Debug Skill Verification

## Scenario: Production-Only 500 Error on User List API

**Setup:** A developer reports: "The user list API endpoint works locally but returns 500 in production. The error started after last week's deployment." The API uses Prisma with PostgreSQL. The production database has a different schema version (missing a column added in a recent migration that wasn't applied). The error only shows in server logs, not in the API response.

**Expected Outcome:** Agent traces the error from symptom to root cause (missing migration in production), proposes applying the migration (not a code fix), writes a regression test that verifies the API handles the missing column gracefully, and documents the production-only debugging approach.

---

## Key Checkpoints

### Phase 1: Reproduce

1. **Agent gathers symptoms** -- 500 error, production-only, after deployment, error only in server logs.
   - Agent asks: What's happening? When does it occur? Reproduction steps? Recent changes?
   - Agent notes: cannot reproduce locally (critical signal).

2. **Agent confirms understanding and waits for user confirmation.**
   ```
   Issue: User list API returns 500 in production but works locally
   Conditions: Production environment only, started after last week's deployment
   Impact: All users unable to load user list in production

   Confirm understanding: (yes / correct / clarify)
   ```
   - GATE: Agent does not proceed without user confirmation.

### Phase 2: Analyze

3. **Agent forms hypotheses** covering multiple categories:
   - H1: Environment difference -- missing migration in production database
   - H2: Environment variables -- different config between local and production
   - H3: Code regression -- new code incompatible with production state
   - H4: Connection/infra issue -- database connectivity or permissions

4. **Agent uses "Production-only failure" strategy from the decision tree.**
   - Checks database schema/migration state (compares local vs production)
   - Checks environment variables
   - Checks connection strings
   - Checks Node.js version
   - Checks dependency versions
   - Analyzes server logs for full stack trace

5. **Agent investigates environment differences.**
   - Requests production server logs (the error is only in logs, not the API response)
   - Compares `prisma migrate status` output between environments
   - Identifies that the production database is missing a column added in a recent migration
   - Finds the Prisma query referencing the missing column in the stack trace

### Phase 3: Narrow

6. **Agent identifies missing migration as root cause with evidence.**
   ```
   Root Cause: Migration 20240115_add_user_column was not applied to production database
   Location: Production database schema (infrastructure, not code)
   Problem: Prisma query references column `new_field` which does not exist in production schema
   Evidence: (a) local `prisma migrate status` shows all migrations applied,
             (b) production shows pending migration,
             (c) stack trace shows column-not-found error
   ```

### Phase 4: Fix

7. **Agent does NOT propose a code fix** -- the fix is applying the migration.
   ```
   Fix Plan:
   Root Cause: Missing database migration in production
   Solution: Apply pending migration to production database
   Command: prisma migrate deploy (in production environment)
   Regression Test: Test that API handles schema mismatch gracefully (returns proper error, not 500)
   Risks: Migration may require downtime; verify migration is backward-compatible

   Approve fix? (yes / no / modify)
   ```
   - GATE: Agent waits for user approval before any action.

8. **Agent proposes the correct fix** -- apply the migration, not change the code.

9. **Agent writes a regression test** for graceful handling of schema mismatch.
   ```typescript
   it('should return a descriptive error when database schema is out of date', async () => {
     // Arrange: simulate a query against a missing column
     vi.spyOn(prisma.user, 'findMany').mockRejectedValue(
       new PrismaClientKnownRequestError('Column not found', { code: 'P2022', clientVersion: '5.0.0' })
     );

     // Act: call the user list endpoint
     const response = await request(app).get('/api/users');

     // Assert: returns 500 with useful error, not a raw stack trace
     expect(response.status).toBe(500);
     expect(response.body).toHaveProperty('error');
     expect(response.body.error).toMatch(/database|schema|migration/i);
   });
   ```

### Phase 5: Verify

10. **Agent documents the production-only debugging approach** for future reference.
    - How to obtain and analyze production logs
    - How to compare migration state across environments
    - How to verify schema compatibility before deployment
    - Recommendation: add `prisma migrate status` check to deployment pipeline

---

## Anti-Patterns to Watch For

| Anti-Pattern | Why It's Wrong | What Should Happen |
|---|---|---|
| Agent proposes a code fix (e.g., add try-catch, remove the column reference) | The root cause is infrastructure, not code | Agent identifies the fix as applying the migration |
| Agent skips hypothesis phase and jumps to fixing | Violates Iron Law #2 (Analyze First, Fix Second) | Agent forms at least 3 hypotheses before investigating |
| Agent makes multiple changes at once | Violates Iron Law principle (one change at a time) | Agent proposes one fix: apply the migration |
| Agent suppresses the error (catch and ignore) | Violates "Never Do" rule (never suppress an error) | Agent ensures the error is properly surfaced |
| Agent gives up before 3 attempts | Premature escalation | Agent exhausts hypothesis list systematically |
| Agent tries to reproduce locally and stops when it works | "Works on my machine" rationalization | Agent recognizes production-only pattern and investigates environment differences |

---

## Known Gaps Addressed

This scenario exposed three gaps in the debug skill, which have been addressed in SKILL.md:

1. **No production-only bug guidance.** The decision tree entry "Works locally, fails in CI" only mentioned env vars and Node version. Now expanded to "Production-only failure" with database schema, migration state, connection strings, server logs, and dependency versions.

2. **No database/ORM debugging references.** The context-aware reference table had no entry for database or ORM errors. Now includes `prisma-guidelines` and `references/debugging-techniques.md` (Schema Drift Detection) for database-related failures.

3. **No escalation report template.** When 3 attempts fail, the skill said "STOP. Present architectural concerns." but gave no structure. Now includes a full escalation report template with hypotheses tested, remaining theories, suggested next steps, and architectural concerns.
