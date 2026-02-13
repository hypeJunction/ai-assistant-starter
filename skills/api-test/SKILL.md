---
name: api-test
description: Discover, design, implement, run, and report on API endpoint tests. Ensures every route is tested for status codes, response shapes, auth boundaries, and edge cases.
triggers:
  - test API
  - test endpoints
  - API coverage
  - test routes
---

# API Test

> **Purpose:** Comprehensive API endpoint testing
> **Phases:** Discover → Design → Implement → Run → Report
> **Usage:** `/api-test [scope flags] [description]`

## Iron Laws

1. **TEST EVERY STATUS CODE** — Don't just test 200. Test 400, 401, 403, 404, 500. Every documented status code for an endpoint must have a test.
2. **VALIDATE RESPONSE SHAPE** — Assert the structure, not just the status code. A 200 with a malformed body is still a bug.
3. **TEST AUTH BOUNDARIES** — Every endpoint must be tested with and without valid auth. An unprotected endpoint is a security hole.

## When to Use

- After implementing new API routes or handlers
- When adding authentication or authorization to endpoints
- When modifying request validation or response formats
- When auditing existing API coverage
- Before a release to verify API contract stability

## When NOT to Use

- Unit testing pure functions or utilities -> `/test-coverage`
- Testing UI components -> `/test-coverage` or `/add-story`
- Debugging a specific API bug -> `/debug`
- Full CI validation -> `/validate`
- Load/performance testing -> dedicated performance tools

## Constraints

- Create test files freely in the appropriate test directory
- Do not modify API source files without approval
- Do not call external/production APIs -- mock or use test server
- Every test file MUST include a test plan as a comment
- Tests must be safe to run in CI (no side effects on real data)

## Gate Enforcement

**CRITICAL:** Do not mark any phase as complete without running commands and verifying output.

**Key gates:**
1. Discovery must list all endpoints before designing tests
2. All tests must pass before generating the report
3. Report must include per-endpoint and per-status-code coverage

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Specific route files or directories to test |
| `--route=<path>` | Specific API route pattern (e.g., `/api/users/:id`) |
| `--branch=<name>` | Compare against specific branch (default: main) |

**Examples:**
```bash
/api-test                                    # Test all API routes on current branch
/api-test --files=src/routes/users.ts        # Test specific route file
/api-test --route=/api/users                 # Test specific route pattern
/api-test --files=src/api/ --route=/api/auth # Test auth routes in api directory
```

---

## Phase 1: Discover

**Mode:** Read-only -- detect framework, find routes, list endpoints.

### Step 1.1: Detect API Framework

```bash
# Check package.json for framework
cat package.json | grep -E "(express|fastify|hono|@nestjs|next|nuxt|koa)"

# Check for route file patterns
find src -type f -name "*.ts" | head -30
ls src/routes/ src/api/ src/app/api/ src/pages/api/ 2>/dev/null
```

Identify the framework and its routing convention:

| Framework | Route Pattern |
|-----------|---------------|
| Express | `router.get('/path', handler)` |
| Fastify | `fastify.get('/path', opts, handler)` |
| Next.js App Router | `app/api/**/route.ts` |
| Next.js Pages Router | `pages/api/**/*.ts` |
| Hono | `app.get('/path', handler)` |
| NestJS | `@Get('/path')` decorator |
| Koa | `router.get('/path', handler)` |

### Step 1.2: Find Route Files

```bash
# Scope to --files or --route if provided, otherwise find all
grep -rn --include="*.ts" --include="*.tsx" -E "(router\.(get|post|put|patch|delete)|app\.(get|post|put|patch|delete)|@(Get|Post|Put|Patch|Delete)|export (async )?function (GET|POST|PUT|PATCH|DELETE))" src/
```

### Step 1.3: List Endpoints

```markdown
## Discovered Endpoints

| Method | Route | Handler File | Auth Required | Status |
|--------|-------|--------------|---------------|--------|
| GET | /api/users | src/routes/users.ts:12 | Yes | Untested |
| POST | /api/users | src/routes/users.ts:45 | Yes | Untested |
| GET | /api/users/:id | src/routes/users.ts:78 | Yes | Untested |
| DELETE | /api/users/:id | src/routes/users.ts:102 | Admin | Untested |
```

---

## Phase 2: Design

**Mode:** Read-only -- categorize endpoints, plan test cases.

### Step 2.1: Categorize Endpoints

For each endpoint, determine required test categories:

| Category | Description | Required |
|----------|-------------|----------|
| Happy path | Valid request, expected response | Always |
| Validation errors | Missing/invalid fields -> 400 | If endpoint accepts body/params |
| Auth: no token | Request without auth -> 401 | If auth required |
| Auth: wrong role | Valid auth, insufficient permissions -> 403 | If role-based |
| Not found | Valid request, resource missing -> 404 | If endpoint has path params |
| Conflict | Duplicate creation, stale update -> 409 | If applicable |
| Server error | Internal failure handling -> 500 | Always (mock failure) |

### Step 2.2: Design Test Plan

```markdown
## Test Plan: [Route Group]

### GET /api/users
| Test Case | Expected Status | Assertions |
|-----------|-----------------|------------|
| List users with valid auth | 200 | Array response, user shape |
| List users without auth | 401 | Error response shape |
| List users with pagination | 200 | Correct page size, metadata |

### POST /api/users
| Test Case | Expected Status | Assertions |
|-----------|-----------------|------------|
| Create user with valid data | 201 | User shape, id assigned |
| Create user without auth | 401 | Error response |
| Create user with missing name | 400 | Validation error, field name |
| Create user with duplicate email | 409 | Conflict error |

**Estimated tests:** N
```

---

## Phase 3: Implement

**Mode:** Full access -- write tests using project's test runner.

### Step 3.1: Set Up Test Utilities

Create or reuse API test helpers:

```typescript
/**
 * Test Plan: API Test Utilities
 *
 * Provides authenticated request helpers, response validators,
 * and test data factories for API endpoint testing.
 */

// Helper for making authenticated requests
function authRequest(method: string, path: string, token?: string) {
  const req = request(app)[method](path);
  if (token) req.set('Authorization', `Bearer ${token}`);
  return req;
}

// Helper for validating error response shape
function expectErrorResponse(res: Response, statusCode: number) {
  expect(res.status).toBe(statusCode);
  expect(res.body).toHaveProperty('error');
  expect(res.body.error).toHaveProperty('message');
}
```

### Step 3.2: Write Tests Per Endpoint

Organize tests by endpoint, with describe blocks per route:

```typescript
describe('GET /api/users', () => {
  describe('authentication', () => {
    it('should return 401 when no auth token provided', async () => {
      const res = await request(app).get('/api/users');
      expect(res.status).toBe(401);
    });

    it('should return 403 when user lacks required role', async () => {
      const res = await request(app)
        .get('/api/users')
        .set('Authorization', `Bearer ${viewerToken}`);
      expect(res.status).toBe(403);
    });
  });

  describe('happy path', () => {
    it('should return 200 with array of users', async () => {
      const res = await request(app)
        .get('/api/users')
        .set('Authorization', `Bearer ${adminToken}`);
      expect(res.status).toBe(200);
      expect(Array.isArray(res.body.data)).toBe(true);
      expect(res.body.data[0]).toMatchObject({
        id: expect.any(String),
        name: expect.any(String),
        email: expect.any(String),
      });
    });
  });

  describe('validation', () => {
    it('should return 400 when page param is negative', async () => {
      const res = await request(app)
        .get('/api/users?page=-1')
        .set('Authorization', `Bearer ${adminToken}`);
      expect(res.status).toBe(400);
    });
  });
});
```

### Step 3.3: Verify Test Isolation

- Each test must set up its own data (use factories or `beforeEach`)
- Clean up created resources in `afterEach` or use transactions
- Never depend on test execution order

---

## Phase 4: Run

**Mode:** Execute tests and collect results.

### Step 4.1: Run Tests

```bash
npm run test -- path/to/api/tests/          # All API tests
npm run test -- path/to/api/tests/users.spec.ts  # Specific endpoint
```

### Step 4.2: Fix Failures

Common API test issues:

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Connection refused | App not started in test | Use `supertest(app)` or test server setup |
| 500 instead of 400 | Validation not implemented | Add input validation to handler |
| Auth test passes without token | Auth middleware not applied | Check middleware registration |
| Flaky timeout | Async cleanup not awaited | Add `await` to teardown |
| Wrong response shape | Serialization mismatch | Check response transformer |

---

## Phase 5: Report

**Mode:** Generate coverage report.

### Step 5.1: Endpoint Coverage Report

```markdown
## API Test Coverage Report

### Summary
- **Endpoints discovered:** N
- **Endpoints tested:** M
- **Total tests:** T
- **Pass rate:** P%

### Coverage by Endpoint

| Method | Route | Tests | Status Codes Covered | Pass |
|--------|-------|-------|----------------------|------|
| GET | /api/users | 5 | 200, 400, 401, 403 | All |
| POST | /api/users | 6 | 201, 400, 401, 409 | All |
| GET | /api/users/:id | 4 | 200, 401, 404 | All |
| DELETE | /api/users/:id | 4 | 204, 401, 403, 404 | All |

### Coverage by Status Code

| Status Code | Meaning | Tests |
|-------------|---------|-------|
| 200 | OK | 8 |
| 201 | Created | 2 |
| 204 | No Content | 1 |
| 400 | Bad Request | 5 |
| 401 | Unauthorized | 4 |
| 403 | Forbidden | 3 |
| 404 | Not Found | 3 |
| 409 | Conflict | 1 |

### Gaps
- [any untested endpoints or status codes]

### Issues Found
- [any issues discovered during testing]
```

---

## Quick Reference

| Phase | Action | Gate |
|-------|--------|------|
| 1. Discover | Detect framework, list endpoints | All routes catalogued |
| 2. Design | Plan test cases per endpoint | Test plan complete |
| 3. Implement | Write tests with test runner | -- |
| 4. Run | Execute and fix failures | **All tests pass** |
| 5. Report | Coverage by endpoint and status code | -- |
