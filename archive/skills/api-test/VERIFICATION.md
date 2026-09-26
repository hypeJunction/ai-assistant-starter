# API Test Skill Verification

## Scenario

A developer has a REST API with 4 endpoints:

- `GET /api/posts` -- public, no auth required
- `POST /api/posts` -- requires authentication (any logged-in user)
- `GET /api/posts/:id/comments` -- nested resource, public
- `DELETE /api/posts/:id` -- admin role only

The API uses Express with JWT-based auth middleware. Posts have a title and body. Comments belong to a post (foreign key relationship). The project uses Vitest and supertest for testing.

**Invocation:** `/api-test`

## Expected Outcome

The agent discovers all 4 endpoints, detects auth requirements for each, identifies the nested resource relationship between posts and comments, creates test infrastructure (test server, database seeding, auth helpers), presents a test plan for approval, writes comprehensive tests covering status codes, response shapes, auth boundaries, nested resource edge cases, and input validation, then runs all tests to confirm they pass.

## Key Checkpoints

### 1. Agent discovers all API endpoints (route files, handler files)

The agent searches the codebase for route definitions. It finds the route file(s) containing all 4 endpoints and reads the handler implementations to understand request/response shapes.

**Verify:** Discovered endpoints table lists all 4 endpoints with their HTTP methods, paths, handler file locations, and line numbers. No endpoints are missed.

### 2. Agent detects auth requirements for each endpoint (public, auth, admin)

For each endpoint, the agent inspects route middleware and handler code:
- `GET /api/posts` -- no auth middleware attached, classified as **public**
- `POST /api/posts` -- has auth middleware (e.g., `requireAuth`), classified as **authenticated**
- `GET /api/posts/:id/comments` -- no auth middleware, classified as **public**
- `DELETE /api/posts/:id` -- has auth middleware and role check (e.g., `requireRole('admin')`), classified as **admin**

**Verify:** The discovered endpoints table includes an "Auth Required" column showing `Public`, `Auth`, `Public`, and `Admin` respectively. The agent does not guess -- it reads the actual middleware chain.

### 3. Agent identifies nested resource relationship (posts/:id/comments)

The agent recognizes that `GET /api/posts/:id/comments` is a nested resource: comments belong to a specific post. This triggers additional test considerations: valid parent ID, non-existent parent ID, and parent-child relationship integrity.

**Verify:** The agent explicitly calls out the nested resource in the discovery output and plans specific tests for it (not just a standard GET test).

### 4. Agent creates test setup (test server, database seeding, auth helpers)

The agent checks for existing test infrastructure:
- Looks for an existing test setup file, supertest configuration, or test utilities
- If none exist, creates: test server setup (import app, create test instance), auth helpers (token generation for different roles), database seeding (factories or seed functions for posts and comments), and cleanup between tests

**Verify:** Test setup includes `beforeAll` (server + database), `afterAll` (teardown), and `beforeEach` or `afterEach` (cleanup). Auth helpers generate tokens for at least three roles: admin, authenticated user, and unauthenticated (no token).

### 5. Agent tests happy paths for all endpoints

Each endpoint has at least one happy path test:
- `GET /api/posts` -- returns 200 with array of posts, validates post shape
- `POST /api/posts` -- returns 201 with created post, validates response includes id/title/body
- `GET /api/posts/:id/comments` -- returns 200 with array of comments for the given post
- `DELETE /api/posts/:id` -- returns 204 (or 200) on successful deletion by admin

**Verify:** All 4 happy path tests are present with status code assertions AND response shape assertions (not just status codes).

### 6. Agent tests auth boundaries (401 for unauthenticated, 403 for wrong role)

Auth boundary tests:
- `POST /api/posts` without token returns 401
- `POST /api/posts` with expired/malformed token returns 401
- `DELETE /api/posts/:id` without token returns 401
- `DELETE /api/posts/:id` with regular user token (not admin) returns 403
- `GET /api/posts` and `GET /api/posts/:id/comments` work without auth (confirming public access)

**Verify:** At least 5 auth boundary tests are present. Both 401 (unauthenticated) and 403 (wrong role) status codes are tested. Public endpoints are confirmed to work without tokens.

### 7. Agent tests nested resource (comments for non-existent post returns 404)

Nested resource tests:
- `GET /api/posts/:id/comments` with valid post ID returns only comments belonging to that post
- `GET /api/posts/:id/comments` with non-existent post ID returns 404
- `GET /api/posts/:id/comments` with invalid ID format (e.g., `abc` instead of a number) returns 400

**Verify:** At least 3 nested resource tests are present. The non-existent parent test explicitly asserts 404. The response is verified to only contain comments for the specified parent post.

### 8. Agent tests edge cases (invalid ID format, missing required fields)

Edge case tests:
- `POST /api/posts` with missing title returns 400 with validation error
- `POST /api/posts` with empty body field returns 400
- `DELETE /api/posts/:id` with non-existent ID returns 404
- `DELETE /api/posts/:id` with invalid ID format returns 400
- `GET /api/posts` with empty database returns 200 with empty array

**Verify:** At least 4 edge case tests are present. Validation error responses include field-level detail (not just a generic 400).

### 9. Agent shows test plan to user for approval before writing tests

Before writing any test files, the agent presents a structured test plan:

```
## API Test Plan
| Endpoint | Auth | Tests Planned |
|----------|------|--------------|
| GET /api/posts | Public | happy path, empty state, pagination |
| POST /api/posts | Auth | happy path, 401 unauth, validation errors |
| GET /api/posts/:id/comments | Public | happy path, non-existent parent 404, invalid ID |
| DELETE /api/posts/:id | Admin | happy path, 401 unauth, 403 wrong role, 404 not found |

Estimated tests: ~18
```

The agent waits for user approval before proceeding to implement.

**Verify:** The test plan is presented as a table. The agent explicitly asks for approval and does not proceed until it receives it. The plan includes estimated test count.

### 10. Agent runs tests and they pass

The agent executes all written tests:
```bash
npm run test -- path/to/api/tests/posts.spec.ts
```

If any tests fail, the agent diagnoses and fixes them. Common issues: test server not started, database not seeded, auth token not configured.

**Verify:** Final test output shows all tests passing. If there were failures, the agent fixed them and re-ran successfully.

### 11. Agent links to api-test-patterns.md for reference

The agent references `references/api-test-patterns.md` for request/response testing patterns, auth testing helpers, and error response validation. It also references `references/api-mock-patterns.md` for database strategies and test data factories.

**Verify:** The agent consults reference files during the Implement phase. Test code follows the patterns from the reference files (e.g., consistent error response shape validation, factory pattern for test data).

## Anti-patterns

| Anti-pattern | Why it's wrong | What to do instead |
|---|---|---|
| Skip auth boundary testing | Leaves security holes undetected; an unprotected endpoint is a vulnerability | Test every endpoint with and without valid auth, and with wrong roles for role-restricted endpoints |
| Ignore nested resources | Nested resources have unique failure modes (non-existent parent, wrong parent-child relationship) that flat resource tests do not cover | Test nested resources with valid parent, non-existent parent (404), and verify parent-child relationship |
| Write tests without discovering endpoints first | Tests may miss endpoints, test wrong routes, or make incorrect assumptions about request/response shapes | Always run discovery phase first; read route files and handler code before designing tests |
| Hardcode test data without setup/teardown | Tests become order-dependent and flaky; data from one test leaks into another | Use factories with `beforeEach`/`afterEach` for data setup and cleanup |
| Skip approval gate before writing tests | Wastes time writing tests the user did not want or that cover the wrong scenarios | Present the test plan as a table and wait for explicit approval before writing any test files |
| Test only happy paths | Misses the most common production failures: auth bypass, invalid input, missing resources | Test at minimum: happy path, auth boundaries, validation errors, and not-found cases for every endpoint |
| Guess auth requirements instead of reading middleware | Leads to incorrect test expectations (testing auth on a public endpoint or missing auth tests on a protected one) | Read the actual route definition and middleware chain to determine auth requirements |

## Known Gaps (addressed in this update)

| Gap | Status |
|-----|--------|
| No auth requirement detection step | Fixed: added explicit auth detection step in Phase 1 discovery |
| No nested resource testing guidance | Fixed: added nested resource testing section in Phase 2 and Phase 3 |
| No approval gate before writing tests | Fixed: added approval gate at end of Phase 2 |
| `api-test-patterns.md` not linked from main workflow | Fixed: added reference links in Phase 3 Implement |
| Test server setup not covered in main skill | Fixed: added test infrastructure verification step in Phase 3 |
