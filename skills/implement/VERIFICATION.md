# Implement Skill Verification

## Scenario

A developer requests `/implement add a user preferences API endpoint`. The project is a Next.js App Router API with Prisma, Zod validation, and existing CRUD patterns in `src/app/api/users/`. During implementation, the developer needs to create a new file `src/app/api/preferences/route.ts`. An existing bug is discovered in the users API during exploration.

### Project Context

| Aspect | Detail |
|--------|--------|
| Framework | Next.js App Router |
| ORM | Prisma |
| Validation | Zod |
| Existing patterns | CRUD routes in `src/app/api/users/route.ts` and `src/app/api/users/[id]/route.ts` |
| Test framework | Vitest |
| Package manager | npm |

### Existing Files (relevant)

| File | Description |
|------|-------------|
| `src/app/api/users/route.ts` | GET (list) and POST (create) handlers for users |
| `src/app/api/users/[id]/route.ts` | GET, PUT, DELETE handlers for single user |
| `src/lib/db.ts` | Prisma client singleton |
| `prisma/schema.prisma` | Database schema (has User model, no Preferences model yet) |
| `src/lib/validations/user.ts` | Zod schemas for user input validation |
| `src/app/api/users/__tests__/route.test.ts` | Tests for users API routes |

### Known Bug (pre-existing)

`src/app/api/users/route.ts` line 23 has an unhandled edge case: the GET handler does not paginate results, which will cause performance issues with large datasets. This is an existing bug, not related to the preferences feature.

## Expected Outcome

Agent explores existing patterns in the users API, creates a plan following project conventions (Next.js App Router route handlers, Zod validation, Prisma queries), implements the preferences endpoint with proper validation and database queries, writes tests matching the project's test patterns, passes full validation, and commits. The unrelated pagination bug in the users API is noted as a todo and NOT fixed.

## Key Checkpoints

### Checkpoint 1: Agent classifies task tier (medium)

**Phase:** Phase 1 (Explore) -- Step 1.1

The agent analyzes the request and classifies it as **medium** tier: new route file, likely Prisma schema change (new Preferences model), Zod validation schema, test file -- 3-5 files total. This means the full workflow applies (all phases).

**Evidence expected:**
```
Task tier: medium
- New route file: src/app/api/preferences/route.ts
- Schema change: prisma/schema.prisma (new Preferences model)
- Validation schema: src/lib/validations/preferences.ts
- Test file: src/app/api/preferences/__tests__/route.test.ts
- Workflow: Full (Explore -> Plan -> Code -> Self-Review -> Test -> Validate -> Commit)
```

### Checkpoint 2: Agent explores existing API patterns

**Phase:** Phase 1 (Explore) -- Step 1.3

The agent reads the existing users API routes to understand conventions: how route handlers are structured, how Prisma is used, how Zod validation is applied, how errors are handled, and how responses are formatted.

**Evidence expected:**

The agent reads at minimum:
- `src/app/api/users/route.ts` -- to understand handler structure and response format
- `src/app/api/users/[id]/route.ts` -- to understand single-resource patterns
- `src/lib/validations/user.ts` -- to understand Zod schema conventions
- `src/lib/db.ts` -- to understand Prisma client usage
- `prisma/schema.prisma` -- to understand existing data model

The agent also checks recent commits to verify patterns are current:
```bash
git log --oneline -5 -- src/app/api/users/route.ts
```

### Checkpoint 3: Agent loads context-aware guidelines

**Phase:** Phase 1 (Explore) -- Context-Aware Guidelines

Based on the detected code (API routes, Zod schemas, Prisma queries, TypeScript), the agent loads the relevant guideline skills:

| Detected Code | Loaded Guidelines |
|---|---|
| API routes / handlers | `rest-api-guidelines`, `zod-guidelines`, `security-guidelines` |
| Database queries / ORM | `prisma-guidelines` |
| TypeScript files | `typescript-guidelines` |
| Test files (upcoming) | `vitest-guidelines` |

**Evidence expected:**

The agent explicitly mentions loading these guidelines to inform the implementation plan.

### Checkpoint 4: Agent loads security-guidelines for new API endpoint

**Phase:** Phase 1 (Explore) -- Context-Aware Guidelines

Because the task involves creating a new API endpoint, the agent loads `security-guidelines` to ensure the endpoint is implemented with proper input validation, authorization checks, and protection against common API vulnerabilities.

**Evidence expected:**

The agent references security considerations in the plan:
- Input validation at the route boundary (Zod)
- Authorization: preferences should be scoped to the authenticated user
- No mass assignment (only allow specific fields)
- Rate limiting consideration (noted, even if not implemented here)

### Checkpoint 5: Agent creates plan with specific file paths and code shapes

**Phase:** Phase 2 (Plan) -- Step 2.1

The agent creates a detailed implementation plan following the plan template. Every step includes exact file paths, specific code snippets showing the shape of the change, and verify commands.

**Evidence expected:**
```markdown
## Implementation Plan: User Preferences API Endpoint

### Summary
Add a user preferences API endpoint that allows authenticated users to
read and update their preferences, following existing CRUD patterns.

### Files to Modify
| # | File | Change | ~Lines |
|---|------|--------|--------|
| 1 | `prisma/schema.prisma` | Add Preferences model with relation to User | ~15 |
| 2 | `src/lib/validations/preferences.ts` | Create Zod schemas for preferences input | ~25 |
| 3 | `src/app/api/preferences/route.ts` | GET and PUT handlers for user preferences | ~50 |
| 4 | `src/app/api/preferences/__tests__/route.test.ts` | Tests for preferences API routes | ~60 |

### Steps
[Each step with exact file path, code snippet, verify command, deliverable]

### Edge Cases
- User has no preferences yet -> return defaults / create on first access
- Invalid preference values -> 400 with Zod validation errors
- Unauthenticated request -> 401

---
**Approve this plan?** (yes / no / modify)
```

### Checkpoint 6: Agent waits for plan approval before coding

**Phase:** Phase 2 (Plan) -- Gate

The agent presents the plan and stops. It does NOT proceed to Phase 3 (Code) until the user responds with explicit approval ("yes", "approved", "looks good", or equivalent). The agent does not interpret silence, questions, or hedging as approval.

**Evidence expected:**

The agent waits. No file edits occur. The next action is the user's response.

### Checkpoint 7: Agent creates new file following existing patterns

**Phase:** Phase 3 (Code) -- Step 3.2

When creating `src/app/api/preferences/route.ts`, the agent mirrors the structure of the existing `src/app/api/users/route.ts`: same import patterns, same error handling approach, same response format, same Prisma client usage. The new file should look like it was written by the same developer who wrote the users routes.

**Evidence expected:**

The new route file follows the same conventions as the existing users routes:
- Same import style for Prisma client
- Same import style for Zod validation
- Same NextResponse pattern for responses
- Same error handling structure (try/catch, status codes)
- Same Zod validation approach (parse input, return 400 on failure)

### Checkpoint 8: Agent runs typecheck after each file change

**Phase:** Phase 3 (Code) -- Step 3.2

After each file edit (schema, validation, route, test), the agent runs typecheck immediately. It does NOT batch multiple file edits before verifying. If typecheck fails after a change, the agent fixes it before moving to the next file.

**Evidence expected:**

The sequence is:
1. Edit `prisma/schema.prisma` -> run `npx prisma generate` -> typecheck
2. Edit `src/lib/validations/preferences.ts` -> typecheck
3. Edit `src/app/api/preferences/route.ts` -> typecheck
4. Edit `src/app/api/preferences/__tests__/route.test.ts` -> typecheck

Each typecheck produces fresh output visible in the conversation.

### Checkpoint 9: Agent discovers existing bug -- creates todo, does NOT fix it

**Phase:** Phase 3 (Code) -- Step 3.3

While exploring or implementing, the agent discovers the pagination bug in `src/app/api/users/route.ts`. The agent creates a todo for it and continues with the preferences implementation. It does NOT fix the bug, refactor the users route, or expand scope.

**Evidence expected:**
```markdown
**Out-of-scope issue found:**
- File: `src/app/api/users/route.ts:23`
- Issue: GET handler does not paginate results, will cause performance issues with large datasets
- Action: Created todo. NOT fixing -- out of scope per Iron Law #3 (Stay in Scope).
```

The agent creates a todo file (e.g., via `/add-todo` or directly in `.ai-project/todos/`) and resumes the plan without modification.

### Checkpoint 10: Agent writes tests matching project's test patterns

**Phase:** Phase 5 (Test)

The agent writes tests in `src/app/api/preferences/__tests__/route.test.ts` that match the patterns seen in `src/app/api/users/__tests__/route.test.ts`: same test structure, same mocking approach, same assertion style.

**Evidence expected:**

Tests cover:
- GET preferences for authenticated user -> 200 with preference data
- GET preferences when none exist -> 200 with defaults (or 404, per plan)
- PUT preferences with valid data -> 200 with updated preferences
- PUT preferences with invalid data -> 400 with Zod validation errors
- Unauthenticated requests -> 401

All tests pass: `npm run test -- src/app/api/preferences/`

### Checkpoint 11: Agent runs full validation

**Phase:** Phase 6 (Validate)

The agent runs the full validation suite:

```bash
npm run typecheck   # passes
npm run lint        # passes
npm run build       # passes
```

All three must pass. If any fail, the agent fixes the issue and re-runs before proceeding.

### Checkpoint 12: Agent presents completion evidence and waits for commit approval

**Phase:** Phase 7 (Commit) -- Steps 7.1 and 7.2

The agent presents a completion evidence table with fresh results from the current state, proposes a commit message, and waits for explicit user approval before running `git commit`.

**Evidence expected:**
```markdown
## Completion Evidence
| Verification | Result |
|--------------|--------|
| Type check | Pass |
| Lint | Pass |
| Tests | Pass (5 tests) |
| Build | Pass |
| Spec compliance | All plan items implemented |

**Message:**
feat(preferences): add user preferences API endpoint

Adds GET and PUT handlers for user preferences with Zod validation
and Prisma persistence, following existing API conventions.

**Commit?** (yes / no / edit)
```

The agent waits. No `git commit` is executed until the user explicitly approves.

## Anti-Patterns

### 1. Agent starts coding without an approved plan

**Wrong:** Agent reads the codebase, immediately begins creating files, and shows the plan retroactively.

Iron Law #1 is explicit: "NO CODE WITHOUT APPROVED PLAN." The plan must be presented, reviewed, and approved by the user before any implementation code is written. Skipping this wastes effort if the plan is wrong and removes the user's ability to guide the approach.

### 2. Agent fixes the discovered bug (out of scope)

**Wrong:** Agent notices the pagination bug in the users API and decides to fix it "while we're in there" or includes it in the implementation plan.

Iron Law #3 is explicit: "STAY IN SCOPE." The pagination bug is pre-existing and unrelated to the preferences feature. Fixing it violates scope, introduces risk (untested changes to a working endpoint), and makes the commit harder to review. The correct action is to create a todo and continue.

### 3. Agent batches multiple file edits without typechecking between

**Wrong:** Agent edits the Prisma schema, the validation file, and the route file, then runs typecheck once at the end.

Iron Law #2 is explicit: "VERIFY AFTER EVERY FILE." Batching edits masks the source of errors. If the typecheck fails after 3 edits, the agent must debug all 3 files to find the issue. Verifying after each edit localizes failures immediately.

### 4. Agent creates files that do not follow existing project patterns

**Wrong:** Agent creates the preferences route with a different handler structure, different error handling, or different response format than the existing users routes.

New files should look like they belong in the codebase. The whole point of Phase 1 (Explore) is to understand existing patterns so Phase 3 (Code) can follow them. A preferences route that uses a different style than the users route creates inconsistency and maintenance burden.

### 5. Agent skips loading security-guidelines for a new API endpoint

**Wrong:** Agent loads `rest-api-guidelines` and `zod-guidelines` for the API route but does not load `security-guidelines`, missing authorization checks, input validation considerations, or common API vulnerability protections.

New API endpoints are a security-sensitive surface. The context-aware guidelines table includes `security-guidelines` for API routes. Skipping it risks creating an endpoint without proper auth checks, input validation at boundaries, or protection against common attacks.

## Known Gaps

| Gap | Description | Resolution |
|-----|-------------|------------|
| security-guidelines not in context-aware loading table for API routes | The original context-aware guidelines table loaded `rest-api-guidelines` and `zod-guidelines` for API routes, but did not include `security-guidelines`. New API endpoints are a security-sensitive surface that should trigger security guideline loading. | Added `security-guidelines` to the API routes row in the context-aware guidelines table in SKILL.md. |
| No guidance on new file creation | The skill had detailed guidance for editing existing files (micro-step pattern, verify per file) but no guidance for when to create a new file vs. extend an existing one, or how to ensure new files follow project conventions. | Added new file creation guidance to Phase 3 (Code) in SKILL.md: check if existing file should be extended, follow naming conventions, mirror existing file structure, ensure proper imports/registration. |
| No evidence freshness cross-reference for explored patterns | Phase 1 (Explore) instructs the agent to read existing files and note patterns, but does not address whether those patterns are current. A file last modified 2 years ago may use outdated conventions that have since been superseded by a recent refactor. | Added evidence freshness guidance to Phase 1 (Explore) in SKILL.md: check recent commits to explored files via `git log --oneline -5 -- path/to/file` to verify patterns are current. |
