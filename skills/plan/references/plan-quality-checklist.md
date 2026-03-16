# Plan Quality Checklist

Detailed reference for the plan quality checklist in Step 5. Each item includes what "good" looks like, common mistakes, and examples.

## 1. Every Step Has an Exact File Path

**Good:**
```markdown
Step 1: Add `validateToken()` to `src/lib/auth.ts`
```

**Bad:**
```markdown
Step 1: Add validation to the auth module
```

**Why it matters:** "The auth module" could be 5 files. The implementer shouldn't have to guess which file to edit. Exact paths eliminate ambiguity and enable progress tracking.

**Common mistakes:**
- Using directory names instead of file paths
- Saying "the component" instead of `src/components/UserProfile.tsx`
- Omitting path for new files (specify where the new file should be created)

## 2. Every Step Has a Clear Deliverable

**Good:**
```markdown
Deliverable: `validateToken()` is exported and handles valid, expired, and malformed tokens
```

**Bad:**
```markdown
Deliverable: Token validation works
```

**Why it matters:** The deliverable is how you know the step is done. Vague deliverables lead to ambiguous completion states. Clear deliverables enable verification.

**Template:** "After this step, [specific thing] is true that wasn't true before."

## 3. Code Snippets Show the Shape of Changes

**Good:**
```markdown
```typescript
export function validateToken(token: string): { userId: string } {
  // verify with JWT_SECRET, handle TokenExpiredError
  // return { userId } on success, throw AuthError on failure
}
```
```

**Bad:**
```markdown
Add a function that validates tokens and returns user data.
```

**Why it matters:** Code snippets reveal:
- The function signature (parameters, return type)
- Where it fits in the module (exports, imports needed)
- The approach (not full implementation, but the shape)

**What to include:** Function signatures, type definitions, important conditional branches. Don't write the full implementation — that's the coding phase.

## 4. Edge Cases Have Explicit Handling

**Good:**
```markdown
| Edge Case | Handling |
|-----------|---------|
| Empty input array | Return empty array (not error) |
| Negative price | Throw `ValidationError('Price must be non-negative')` |
| Concurrent requests | Use database transaction to prevent double-charge |
```

**Bad:**
```markdown
Edge cases: handle empty arrays and invalid inputs
```

**Why it matters:** Edge cases are where bugs live. If the plan doesn't address them, the implementer will either handle them inconsistently or miss them entirely.

**How to find edge cases:**
- Empty/null/undefined inputs
- Boundary values (0, -1, MAX_INT)
- Concurrent access
- Network failures / timeouts
- Permission boundaries (what if the user doesn't have access?)

## 5. Test Strategy Names Specific Scenarios

**Good:**
```markdown
### Test Strategy
- `validateToken` with valid token → returns `{ userId }`
- `validateToken` with expired token → throws `AuthError('Token expired')`
- `validateToken` with malformed token → throws `AuthError('Invalid token')`
- `GET /api/protected` without token → returns 401
- `GET /api/protected` with valid token → returns user data
```

**Bad:**
```markdown
### Test Strategy
- Test the token validation
- Test the API endpoint
```

**Why it matters:** Specific scenarios become test cases directly. The implementer knows exactly what to test without interpreting vague instructions.

**Template:** `[function/endpoint] with [input/condition] → [expected result]`

## 6. Risks Have Mitigation Strategies

**Good:**
```markdown
| Risk | Mitigation |
|------|------------|
| JWT_SECRET not set in CI | Add to CI env vars; fail fast with clear error if missing |
| Token rotation breaks active sessions | Implement grace period: accept old tokens for 5 min after rotation |
| Breaking change for API consumers | Version the endpoint: `/api/v2/protected` alongside `/api/v1/protected` |
```

**Bad:**
```markdown
Risks: Token rotation might cause issues.
```

**Why it matters:** Unmitigated risks become production incidents. Every identified risk should have a plan — even if the plan is "we accept this risk because the probability is low and the impact is recoverable."

## 7. Steps Are Ordered by Dependency

**Good:**
```markdown
1. Add `AuthError` class → (no dependencies)
2. Add `validateToken()` using `AuthError` → (depends on step 1)
3. Add auth middleware using `validateToken()` → (depends on step 2)
4. Apply middleware to routes → (depends on step 3)
5. Write tests → (depends on steps 1-4)
```

**Bad:**
```markdown
1. Apply middleware to routes
2. Add validateToken()
3. Add AuthError class
```

**Why it matters:** Out-of-order steps cause typecheck failures and import errors during implementation. Each step should build on the previous, with the typecheck passing after every step.

**How to order:**
- Types and interfaces first
- Pure functions before the code that uses them
- Infrastructure (middleware, config) before features
- Tests after the code they test (unless TDD, then tests first)

## 8. No Step Takes Longer Than 5 Minutes

**Good:**
```markdown
Step 3a: Add `validateToken()` function signature and basic happy path (~3 min)
Step 3b: Add error handling for expired and malformed tokens (~3 min)
Step 3c: Add token refresh logic with race condition prevention (~5 min)
```

**Bad:**
```markdown
Step 3: Implement complete token validation with all edge cases and error handling
```

**Why it matters:** Long steps hide complexity. If a step takes >5 minutes, there are probably multiple decisions and verification points inside it that should be explicit. Short steps enable:
- Frequent verification (typecheck after each step)
- Clear progress tracking
- Easy rollback if something goes wrong

**Splitting heuristic:** If a step description uses "and" or contains multiple verbs, split it.

**TDD granularity:** Each TDD micro-step is its own plan step — "write the failing test" is one step, "run it to verify it fails" is another, "implement the minimal code" is another, "run tests to verify they pass" is another, "commit" is another. Don't collapse these into a single "implement and test" step.

## Complexity-Specific Guidance

### Trivial Plans (1-2 files)

Bullet list is sufficient:
```markdown
- Add `maxRetries` param to `fetchWithRetry()` in `src/lib/http.ts`
- Update call site in `src/api/users.ts` to pass `maxRetries: 3`
- Add test for retry behavior in `src/lib/http.test.ts`
```

### Standard Plans (3-5 files)

Full template with all 8 checklist items. This is the default.

### Complex Plans (6+ files, architectural impact)

Full template plus:
- **Alternatives analysis:** 2-3 approaches with trade-offs, recommended approach with justification
- **Dependency diagram:** Which steps block which (Mermaid if helpful)
- **Rollback plan:** How to undo if the implementation reveals problems
- **Migration strategy:** If changing existing behavior, how to transition

### Risky Plans (breaking changes, data loss potential)

Everything from Complex, plus:
- **Pre-implementation checklist:** What must be verified before coding starts
- **Rollback procedure:** Exact commands to revert (not just "git revert")
- **Data backup plan:** If touching databases, how to preserve data
- **Feature flag option:** Can this be shipped behind a flag first?
- **Communication plan:** Who needs to know about the change?
