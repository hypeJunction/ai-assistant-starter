# Explore Skill Verification

## Scenario

A new developer joins a large monorepo with 3 packages (`packages/api`, `packages/web`, `packages/shared`). They want a deep understanding of how authentication works across the stack — from the React login form to the API middleware to the shared auth utilities. They invoke `/explore --depth=deep how does authentication work?`

### Monorepo Structure

| Package | Role |
|---------|------|
| `packages/web` | React frontend with login form, auth context, protected routes |
| `packages/api` | Express/Fastify backend with auth middleware, session management, token endpoints |
| `packages/shared` | Shared auth utilities, token types, validation schemas, constants |

### Key Auth Files (expected to be discovered)

| File | Package | Purpose |
|------|---------|---------|
| `packages/web/src/components/LoginForm.tsx` | web | React login form component |
| `packages/web/src/contexts/AuthContext.tsx` | web | Auth state management, token storage |
| `packages/web/src/hooks/useAuth.ts` | web | Auth hook for components |
| `packages/web/src/middleware/protectedRoute.tsx` | web | Route guard checking auth state |
| `packages/api/src/middleware/auth.ts` | api | JWT verification middleware |
| `packages/api/src/routes/auth.ts` | api | Login/logout/refresh endpoints |
| `packages/api/src/services/session.ts` | api | Session store (Redis/DB) |
| `packages/shared/src/types/auth.ts` | shared | Token types, user session types |
| `packages/shared/src/utils/token.ts` | shared | Token validation, decode helpers |
| `packages/shared/src/schemas/auth.ts` | shared | Zod schemas for auth payloads |

## Expected Outcome

A comprehensive exploration report covering: the React login component and auth context, the API auth middleware and session management, shared auth utilities and types, how tokens flow between packages, and a clear dependency map. The report should be structured with the Deep-level template sections: Architecture Overview, Component Map, Data Flow, Dependencies, Key Design Decisions, Security Implications, and Areas for Further Exploration.

## Key Checkpoints

### Checkpoint 1: Agent selects "Deep" exploration level based on --depth flag

**Phase:** Step 1 (Parse Scope and Select Strategy)

The agent parses the `--depth=deep` flag and selects "Deep" as the exploration level. The agent identifies "How does X work?" as the question type and selects the "Trace" strategy as the primary strategy, combined with "Map" for architecture understanding.

**Evidence expected:**
```
Exploration: how does authentication work?
Depth: Deep
Strategy: Trace + Map (combined for deep exploration)
Scope: All packages (monorepo — no --files or --project flag restricts scope)
```

### Checkpoint 2: Agent searches across ALL packages (not just root or first match)

**Phase:** Step 2 (Search for Relevant Files)

The agent searches for auth-related files across the entire monorepo, not stopping after finding files in one package. Searches should include `packages/web`, `packages/api`, and `packages/shared`.

**Evidence expected:**
```
# Agent runs broad searches across all packages
glob: **/auth*
glob: **/*auth*
glob: **/*login*
glob: **/*session*
grep: "authenticate" across packages/
grep: "jwt" or "token" across packages/
grep: "middleware" in packages/api/
```

The agent discovers auth-related files in all 3 packages, not just the first one with results.

### Checkpoint 3: Agent discovers auth-related files in each package

**Phase:** Step 2 (Search for Relevant Files)

The agent identifies distinct auth components in each package layer:
- **web**: Login form, auth context/provider, auth hook, protected route component
- **api**: Auth middleware, auth routes (login/logout/refresh), session service
- **shared**: Auth types, token utilities, auth validation schemas

**Evidence expected:**

A file inventory covering all three packages with at least 2-3 files per package identified as auth-related.

### Checkpoint 4: Agent traces the data flow from login form to session store

**Phase:** Step 3 (Read and Analyze)

The agent reads the key files and traces the complete authentication flow:
1. User submits credentials via `LoginForm.tsx`
2. Form calls auth API endpoint via `useAuth` hook or auth context
3. API route handler in `auth.ts` receives credentials
4. Handler validates credentials and creates session/token
5. Token is returned to the client
6. Client stores token in auth context/localStorage
7. Subsequent requests include token via auth middleware
8. API auth middleware verifies token using shared utilities

**Evidence expected:**

A numbered step-by-step data flow with file:line references showing how a login request moves through the system from the React form to the API and back.

### Checkpoint 5: Agent identifies cross-package dependencies

**Phase:** Step 3 (Read and Analyze)

The agent traces imports to discover how packages depend on each other:
- `packages/web` imports types/schemas from `packages/shared`
- `packages/api` imports types/utilities from `packages/shared`
- `packages/shared` has no dependency on `web` or `api`
- Both `web` and `api` depend on `shared` (hub-and-spoke pattern)

**Evidence expected:**

A dependency map showing import relationships between packages, including specific files and what they import from shared utilities.

### Checkpoint 6: Agent reads relevant files completely (not just function signatures)

**Phase:** Step 3 (Read and Analyze)

For a Deep exploration, the agent reads the full implementation of key files, not just function signatures or exports. This includes reading the body of the auth middleware, the login form's submit handler, and the token validation logic.

**Evidence expected:**

The agent's analysis references specific implementation details — such as which token fields are verified, how session expiry is handled, what happens on invalid credentials — not just "this file handles authentication."

### Checkpoint 7: Agent produces structured report with Deep-level sections

**Phase:** Step 4 (Summarize Findings)

The agent produces a report using the Deep exploration template with all required sections.

**Evidence expected:**
```markdown
## Deep Exploration: How Does Authentication Work?

### Architecture Overview
[High-level description of the auth system across packages]

### Component Map
| File | Package | Role |
|------|---------|------|
[All discovered auth files with their purpose]

### Data Flow
[Numbered steps: login form -> API call -> middleware -> session -> response]

### Dependencies
[Cross-package import map, external libraries (jsonwebtoken, bcrypt, etc.)]

### Key Design Decisions
[Token type (JWT vs session), storage strategy, refresh mechanism]

### Security Implications
[Token storage concerns, CSRF, XSS, session fixation, etc.]

### Areas for Further Exploration
[Password reset flow, OAuth integration, role-based access, rate limiting]
```

### Checkpoint 8: Agent includes a dependency/data flow diagram

**Phase:** Step 4 (Summarize Findings)

The Deep exploration includes a visual representation (ASCII or Mermaid) of how data flows through the auth system and how packages depend on each other.

**Evidence expected:**
```
LoginForm (web) --> POST /auth/login (api) --> validateCredentials (api)
                                            --> createSession (api)
                                            --> signToken (shared)
                <-- { token, user } <-------
AuthContext (web) stores token
ProtectedRoute (web) --> GET /api/resource (api) --> authMiddleware (api)
                                                  --> verifyToken (shared)
```

### Checkpoint 9: Agent notes security implications of the auth design

**Phase:** Step 4 (Summarize Findings)

The agent identifies security-relevant aspects of the authentication design without proposing fixes (read-only skill).

**Evidence expected:**

Observations such as:
- Where tokens are stored (localStorage vs httpOnly cookies) and the XSS implications
- Whether CSRF protection is present on auth endpoints
- Token expiry and refresh strategy
- Password hashing algorithm used
- Rate limiting on login attempts

### Checkpoint 10: Agent suggests related areas for further exploration

**Phase:** Step 4 (Summarize Findings)

The agent provides actionable next steps for the developer to continue learning about the codebase.

**Evidence expected:**

Suggestions such as:
- Password reset / forgot password flow
- OAuth / social login integration
- Role-based access control (RBAC)
- API rate limiting and brute-force protection
- Session invalidation / logout across devices

## Anti-Patterns

### 1. Stop after finding auth in one package

**Wrong:** Agent finds `packages/api/src/middleware/auth.ts`, reads it, and produces a report based on only the API layer.

In a monorepo, authentication spans multiple packages. Stopping at one package gives an incomplete picture and misses the client-side auth context, the shared types, and the cross-package data flow. Deep exploration requires covering all layers.

### 2. Give a surface-level overview for a Deep exploration

**Wrong:** Agent lists the files and says "LoginForm handles login, auth middleware verifies tokens, shared has types" without tracing data flow, reading implementations, or identifying design decisions.

The `--depth=deep` flag explicitly requests comprehensive analysis. A Deep exploration must include architecture overview, full data flow tracing, dependency mapping, security implications, and design decisions — not just file summaries.

### 3. Modify any files (violating read-only)

**Wrong:** Agent discovers a security issue in the auth implementation and edits a file to fix it, or creates a summary document in the repo.

The explore skill is strictly read-only. The agent must never edit, create, or delete any file. If issues are found, they should be noted in the report as observations, not acted upon.

### 4. Skip the cross-package dependency tracing

**Wrong:** Agent reads files in each package independently but never traces how they connect — missing that `packages/api` imports `verifyToken` from `packages/shared`, or that `packages/web` uses types from `packages/shared`.

Cross-package dependencies are essential for understanding how a feature works in a monorepo. The agent must trace imports across package boundaries to map the full dependency graph.

### 5. Read only function signatures without tracing implementation

**Wrong:** Agent sees `export function verifyToken(token: string): DecodedToken` and reports "verifyToken verifies tokens" without reading what algorithm it uses, what claims it checks, or how it handles expiry.

Deep exploration requires reading implementation details, not just signatures. The developer wants to understand how authentication works, not just what functions exist.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No Deep-level section templates | Deep explorations had no structured report template, leading to inconsistent and incomplete reports | Added Deep Exploration template with 7 required sections: Architecture Overview, Component Map, Data Flow, Dependencies, Key Design Decisions, Security Implications, Areas for Further Exploration |
| No cross-strategy techniques for Deep | Deep explorations used a single strategy, missing the comprehensive analysis that requires combining search, trace, and map approaches | Added cross-strategy guidance: grep/glob to find all files, read key files fully, trace imports for dependencies, follow data flow end-to-end, check tests for behavior documentation |
| No monorepo guidance | No instruction to search across package boundaries, leading to single-package explorations in monorepos | Added monorepo guidance: search ALL packages, identify cross-package imports, map package ownership of feature parts, note shared types/utilities |
