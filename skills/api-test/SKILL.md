---
name: api-test
description: Discover, design, implement, run, and report on API endpoint tests. Ensures every route is tested for status codes, response shapes, auth boundaries, and edge cases.
category: process
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

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

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

### Step 1.4: Detect Auth Requirements

For each endpoint, detect auth requirements by reading the route definition and middleware chain:

1. **Check for auth middleware on the route** — Look for middleware like `requireAuth`, `authenticate`, `isAuthenticated`, `@UseGuards(AuthGuard)`, or similar patterns applied to the route or router group.
2. **Check for role/permission checks** — Look for role guards like `requireRole('admin')`, `@Roles('admin')`, permission middleware, or inline role checks in the handler.
3. **Classify each endpoint:**
   - **Public** — No auth middleware. Accessible without a token.
   - **Authenticated** — Auth middleware present, but no role restriction. Any logged-in user can access.
   - **Role-restricted** — Auth middleware + role/permission check. Only specific roles can access (e.g., admin, editor).

Auth boundaries **MUST** be tested. Update the "Auth Required" column in the endpoints table with the detected classification (Public / Auth / Admin / etc.).

### Step 1.5: Identify Nested Resources

Check for nested route patterns (e.g., `/posts/:id/comments`, `/users/:id/orders`). For each nested resource:

1. Identify the parent-child relationship (e.g., comments belong to a post)
2. Note the parent ID parameter name
3. Flag for additional test cases: valid parent, non-existent parent (404), parent-child relationship integrity

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
| Nested resource | Parent-child relationship integrity | If nested route (e.g., /posts/:id/comments) |
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

### Step 2.3: Nested Resource Test Cases

For nested resources (e.g., `/posts/:id/comments`):

1. **Valid parent ID** — Test with a parent that exists and has children. Assert the response contains only children of the specified parent.
2. **Non-existent parent ID** — Test with a parent ID that does not exist. Should return 404.
3. **Parent-child relationship integrity** — Verify that resources only return children of the specified parent, not children of other parents.

```markdown
### GET /api/posts/:id/comments
| Test Case | Expected Status | Assertions |
|-----------|-----------------|------------|
| List comments for valid post | 200 | Array of comments, all belong to post |
| List comments for non-existent post | 404 | Error response |
| List comments for invalid post ID format | 400 | Validation error |
| Verify comments only belong to parent post | 200 | No comments from other posts |
```

### Step 2.4: Approval Gate

**CRITICAL:** Present the test plan to the user before writing any tests.

```markdown
## API Test Plan

| Endpoint | Auth | Tests Planned |
|----------|------|--------------|
| GET /api/posts | Public | happy path, empty state, pagination |
| POST /api/posts | Auth | happy path, 401 unauth, validation errors |
| GET /api/posts/:id/comments | Public | happy path, non-existent parent 404, invalid ID |
| DELETE /api/posts/:id | Admin | happy path, 401 unauth, 403 wrong role, 404 not found |

Estimated tests: N
```

**GATE: User must approve test plan before proceeding.** If the user requests changes to the test plan, update it and present again.

---

## Phase 3: Implement

**Mode:** Full access -- write tests using project's test runner.

See `references/api-test-patterns.md` for request/response testing patterns, auth testing helpers, and error response validation. See `references/api-mock-patterns.md` for external service mocking strategies, database setup, and test data factories.

### Step 3.0: Verify Test Infrastructure

Before writing tests, verify test infrastructure is in place:

1. **Check for existing test setup** — Look for existing test utilities (supertest configuration, test helpers, factories, auth helpers). If they exist, reuse them.
2. **If no test setup exists, create one:**
   - **Test server:** Import the app/server, create a test instance. Do not start on a real port -- use supertest or equivalent in-process testing.
   - **Test database:** Configure a test database (in-memory, transaction rollback, or isolated test DB). See `references/api-mock-patterns.md` for strategies.
   - **Auth helpers:** Create token generation helpers for each role needed (admin, user, unauthenticated). See `references/api-mock-patterns.md` for auth helper patterns.
   - **Data factories:** Create factory functions for test entities (posts, comments, users) with sensible defaults and easy overrides.
3. **Ensure proper setup/teardown:**
   - `beforeAll` — Start test server, connect to test database, run migrations/seed
   - `afterAll` — Disconnect database, clean up server
   - `beforeEach` / `afterEach` — Reset database state between tests (truncate tables or rollback transactions)

### Step 3.1: Set Up Test Utilities (see `references/api-mock-patterns.md` for database strategies, MSW setup, factories, and contract testing)

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

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| API-T1 | Positive | "Test the API endpoints" | Skill triggers |
| API-T2 | Positive | "API coverage for the users route" | Skill triggers |
| API-T3 | Positive | "Test all routes for status codes" | Skill triggers |
| API-T4 | Negative | "Write unit tests for this utility" | Does NOT trigger (-> /test-coverage) |
| API-T5 | Negative | "End-to-end test the login flow" | Does NOT trigger (-> /e2e) |
| API-T6 | Negative | "Debug the 500 error on /api/users" | Does NOT trigger (-> /debug) |
| API-T7 | Boundary | "Test this endpoint" | Context-dependent — if API endpoint, trigger; if UI component, route to /test-coverage |

## Quick Reference

| Phase | Action | Gate |
|-------|--------|------|
| 1. Discover | Detect framework, list endpoints, detect auth requirements, identify nested resources | All routes catalogued with auth classification |
| 2. Design | Plan test cases per endpoint, nested resource cases | **User approves test plan** |
| 3. Implement | Verify test infrastructure, write tests with test runner | -- |
| 4. Run | Execute and fix failures | **All tests pass** |
| 5. Report | Coverage by endpoint and status code | -- |
