# Defense in Depth

Post-fix validation methodology. After applying a fix, verify it at multiple layers and audit for the same pattern elsewhere. A fix that only works at one layer is fragile.

## Four-Layer Validation

After every bug fix, validate at each layer:

```
Layer 1: Entry Point Validation
  └─ Does the fix handle the bad input at the system boundary?

Layer 2: Business Logic Validation
  └─ Does the core logic behave correctly with edge cases?

Layer 3: Environment Guards
  └─ Does the fix survive different environments (dev, test, CI, prod)?

Layer 4: Debug Instrumentation
  └─ Can you detect if this bug recurs without a user report?
```

### Example: Fixing a null pointer in user lookup

**Bug:** `user.name` crashes when user is not found in database.

**Layer 1 — Entry point:** Validate that the user ID parameter is present and well-formed before the database lookup.

```typescript
// API route — entry point validation
const userId = req.params.id;
if (!userId || !isValidUUID(userId)) {
  return res.status(400).json({ error: 'Invalid user ID' });
}
```

**Layer 2 — Business logic:** Handle the "not found" case in the service layer.

```typescript
// Service layer — business logic
const user = await db.user.findUnique({ where: { id: userId } });
if (!user) {
  throw new NotFoundError(`User ${userId} not found`);
}
return user; // Now guaranteed to be non-null
```

**Layer 3 — Environment:** Ensure the fix works when the database is empty (fresh CI environment), when the user was recently deleted (race condition), and when the ID format differs across environments.

**Layer 4 — Instrumentation:** Add monitoring/logging so you'll know if this happens again.

```typescript
// Structured logging for observability
if (!user) {
  logger.warn('user_not_found', { userId, source: req.path });
}
```

## Regression Test Quality

A regression test must prove the fix works AND would catch a regression.

### The Revert Test

The gold standard for regression test quality:

1. **Write the test** that reproduces the bug scenario
2. **Apply the fix** — test should pass
3. **Mentally revert the fix** — would the test fail?
4. If the test would still pass without the fix, **the test is not a regression test**

### Good vs. Bad Regression Tests

**Bad:** Tests a happy path that always worked

```typescript
// This test passes with OR without the fix — useless as regression test
it('should return user data', async () => {
  const user = await getUser('valid-id');
  expect(user.name).toBe('Alice');
});
```

**Good:** Tests the exact condition that triggered the bug

```typescript
// This test fails without the fix, passes with it — true regression test
it('should throw NotFoundError when user does not exist', async () => {
  await expect(getUser('nonexistent-id')).rejects.toThrow(NotFoundError);
});

it('should return 400 for malformed user ID', async () => {
  const res = await request(app).get('/api/users/not-a-uuid');
  expect(res.status).toBe(400);
});
```

### Regression Test Checklist

- [ ] Test reproduces the exact input/condition that triggered the bug
- [ ] Test would FAIL if the fix were reverted
- [ ] Test asserts the CORRECT behavior, not just "doesn't crash"
- [ ] Test is named descriptively: `should [correct behavior] when [bug trigger]`
- [ ] Test is in the right file (near the fixed code, not in an unrelated test suite)

## Related Code Audit

After fixing a bug, check if the same pattern exists elsewhere.

### Search for the Pattern

```bash
# If the bug was a missing null check on database results:
grep -rn "findUnique\|findFirst" src/ --include="*.ts"
# Check: do all callers handle the null case?

# If the bug was an unvalidated user input:
grep -rn "req\.params\|req\.query\|req\.body" src/ --include="*.ts"
# Check: is validation present at each entry point?

# If the bug was a missing await:
grep -rn "findMany\|findFirst\|create\|update\|delete" src/ --include="*.ts"
# Check: are all async calls properly awaited?
```

### Audit Scope

| Bug Type | Search Pattern | What to Check |
|----------|---------------|--------------|
| Null/undefined | All callers of the same function | Do they handle null returns? |
| Missing validation | All API route handlers | Do they validate input? |
| Race condition | All similar async operations | Do they use transactions/locks? |
| Missing error handling | All try/catch blocks near the fix | Do they handle the same error type? |
| Type coercion | All similar comparisons | Do they use strict equality? |

### When to Create Todos

If the audit reveals the same pattern in 3+ locations:
- Fix the instance that caused the bug (in scope)
- Create a todo for the remaining instances (out of scope)
- Note the pattern and affected files in the todo for efficient batch fixing later

Don't fix all instances during a debug session — that's scope creep. The current goal is to fix the reported bug and prevent regression.

## See Also

- [Testing Anti-Patterns](../../tdd/references/testing-anti-patterns.md) — Common testing mistakes that lead to low-quality regression tests
