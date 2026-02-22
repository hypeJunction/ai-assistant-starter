# Plan Template

Reference template for Phase 2 (Plan). Every implementation plan should follow this structure. The key principle: **every step is bite-sized (2-5 minutes), targets one file, includes actual code, and has a verifiable outcome.**

## Template

```markdown
## Implementation Plan: [Feature Name]

### Goal
[1-2 sentences: what the user will be able to do after this is implemented]

### Architecture
[Which layers/modules are involved, how data flows, what patterns to follow]

### Files to Modify
| # | File | Change | ~Lines |
|---|------|--------|--------|
| 1 | `src/lib/auth.ts` | Add `validateToken()` function | ~20 |
| 2 | `src/routes/login.ts` | Call `validateToken()` in POST handler | ~10 |
| 3 | `src/lib/auth.test.ts` | Test `validateToken()` with valid/invalid/expired tokens | ~40 |

### Steps

#### Step 1: Write failing test for token validation
**File:** `src/lib/auth.test.ts`
**Action:** Add test cases for `validateToken()`
**Code:**
```typescript
describe('validateToken', () => {
  it('should return user data for valid token', () => {
    const token = createTestToken({ userId: '123', exp: future() });
    const result = validateToken(token);
    expect(result).toEqual({ userId: '123' });
  });

  it('should throw for expired token', () => {
    const token = createTestToken({ userId: '123', exp: past() });
    expect(() => validateToken(token)).toThrow('Token expired');
  });

  it('should throw for malformed token', () => {
    expect(() => validateToken('not-a-token')).toThrow('Invalid token');
  });
});
```
**Verify:** `npm run test -- auth.test.ts` → 3 tests FAIL (function doesn't exist yet)
**Deliverable:** Failing tests that define the expected behavior

#### Step 2: Implement token validation
**File:** `src/lib/auth.ts`
**Action:** Add `validateToken()` function
**Code:**
```typescript
import { verify } from 'jsonwebtoken';

export function validateToken(token: string): { userId: string } {
  try {
    const payload = verify(token, process.env.JWT_SECRET!) as JwtPayload;
    return { userId: payload.userId };
  } catch (error) {
    if (error instanceof TokenExpiredError) throw new AuthError('Token expired');
    throw new AuthError('Invalid token');
  }
}
```
**Verify:** `npm run typecheck` → passes, then `npm run test -- auth.test.ts` → 3 tests PASS
**Deliverable:** All 3 tests green

#### Step 3: Integrate into login route
**File:** `src/routes/login.ts`
**Action:** Add token validation to POST handler
**Code:**
```typescript
import { validateToken } from '../lib/auth';

app.post('/api/protected', (req, res) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'Missing token' });

  const user = validateToken(token);
  // ... rest of handler
});
```
**Verify:** `npm run typecheck` → passes
**Deliverable:** Route uses the new validation function

#### Step 4: Write integration test for protected route
**File:** `src/routes/login.test.ts`
**Action:** Test the protected endpoint with/without valid token
**Verify:** `npm run test -- login.test.ts` → passes
**Deliverable:** Integration test confirms end-to-end behavior

### Edge Cases
- Empty Authorization header → 401
- Expired token → 401 with "Token expired" message
- Token with wrong secret → 401 with "Invalid token"

### Commit
`feat(auth): add JWT token validation for protected routes`
```

## Key Principles

### Every Step Must Have

1. **Exact file path** — not "the auth module" but `src/lib/auth.ts`
2. **Specific code** — actual implementation, not "add validation logic"
3. **Verify command** — exact command to run and what output to expect
4. **Deliverable** — what's true after this step that wasn't true before

### Step Granularity

| Too coarse | Just right |
|-----------|------------|
| "Implement auth" | "Add `validateToken()` to `src/lib/auth.ts`" |
| "Write tests" | "Write 3 test cases for valid/expired/malformed tokens" |
| "Update routes" | "Call `validateToken()` in POST `/api/protected` handler" |
| "Set up database" | "Add `users` table migration with id, email, password_hash columns" |

**Rule of thumb:** If a step takes >5 minutes or touches >1 file, split it.

### TDD-Default vs Enhancement Mode

**TDD-default (new functions/modules):**
1. Write failing test
2. Verify test fails for the right reason
3. Implement minimal code to pass
4. Verify test passes
5. Refactor if needed
6. Commit

**Enhancement mode (modifying existing code):**
1. Read existing code and tests
2. Implement the change
3. Verify typecheck passes
4. Write/update tests
5. Verify tests pass
6. Commit

Use TDD-default when creating new exports. Use enhancement mode when modifying existing behavior where the test surface already exists.

### Plan Quality Checklist

Before presenting the plan, verify:

- [ ] Every step has an exact file path
- [ ] Every step has actual code (not descriptions of code)
- [ ] Every step has a verify command with expected output
- [ ] Steps are ordered so each builds on the previous
- [ ] No step touches more than 1-2 files
- [ ] Edge cases are listed with handling approach
- [ ] Commit message follows conventional commit format
- [ ] Total estimated changes match the task tier (nano: 1-2 lines, small: <100, medium: <500)
