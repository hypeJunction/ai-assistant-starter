# Plan Skill Verification

## Scenario

A developer needs to add OAuth2 (Google + GitHub) login to an existing email/password auth system. The project uses Next.js App Router with NextAuth.js v4. There are existing auth middleware, user model, and session utilities. They invoke `/plan add OAuth2 login with Google and GitHub providers`.

### Existing Auth System

| File | Purpose |
|------|---------|
| `src/app/api/auth/[...nextauth]/route.ts` | NextAuth route handler with CredentialsProvider (email/password) |
| `src/lib/auth.ts` | Session utilities (`getServerSession`, `authOptions`) |
| `src/middleware.ts` | Auth middleware protecting `/dashboard/*` routes |
| `prisma/schema.prisma` | User model with `email`, `hashedPassword`, `name`, `role` fields |
| `src/components/LoginForm.tsx` | Email/password login form |
| `src/app/(auth)/login/page.tsx` | Login page rendering `LoginForm` |
| `src/app/(auth)/register/page.tsx` | Registration page |
| `src/lib/session.ts` | Session token creation and validation |

### Task Complexity

This is a **Complex** plan (6+ files, architectural impact):
- Multiple providers must be added to NextAuth configuration
- Database schema must change to support linked accounts (NextAuth Account model)
- UI must add social login buttons alongside existing email/password form
- Session management must handle both credential and OAuth sessions
- Migration strategy needed for existing users and active sessions
- Security implications around OAuth token storage, CSRF, and redirect validation

## Expected Outcome

A detailed implementation plan that covers: NextAuth provider configuration, callback URLs, database schema changes for linked accounts, UI changes for social login buttons, migration strategy from existing sessions, security considerations connected to specific plan steps, and an alternatives analysis (NextAuth v4 providers vs v5 migration vs custom OAuth). The plan is specific enough to hand off to `/implement` with exact file paths, code shapes, edge cases, and a dependency-ordered step sequence. The agent presents the plan for user approval before any implementation.

## Key Checkpoints

### Checkpoint 1: Agent explores the existing auth system before planning

**Phase:** Step 3 (Explore Relevant Code)

The agent reads the existing auth files to understand the current implementation before designing the plan. This includes the NextAuth configuration, the Prisma schema, the middleware, session utilities, and the login UI. The agent does NOT start planning based on assumptions about the codebase.

**Evidence expected:**

The agent issues read commands for the existing auth-related files. It identifies:
- The current NextAuth configuration (CredentialsProvider only)
- The Prisma User model fields and relations
- The middleware's route protection logic
- The session token format and validation approach
- The login UI structure and form handling

```
Exploring existing auth system...

- src/app/api/auth/[...nextauth]/route.ts — CredentialsProvider with email/password,
  JWT strategy, custom session callback
- prisma/schema.prisma — User model with email, hashedPassword, name, role.
  No Account or Session models (NextAuth adapter tables not present)
- src/middleware.ts — Protects /dashboard/* routes, checks for session token
- src/lib/auth.ts — Exports authOptions and getServerSession wrapper
- src/lib/session.ts — Custom JWT token creation, no database sessions
- src/components/LoginForm.tsx — Client component with email/password inputs,
  calls signIn("credentials", ...)
```

### Checkpoint 2: Agent identifies all files that will need to change

**Phase:** Step 5 (Create Plan — Files to Modify table)

After exploring the codebase, the agent produces a complete list of files that will be created or modified, with the nature of each change and estimated scope. No file is omitted.

**Evidence expected:**

```
### Files to Modify
| File | Change | Lines |
|------|--------|-------|
| `prisma/schema.prisma` | Add Account, Session models for NextAuth adapter | ~30 |
| `src/app/api/auth/[...nextauth]/route.ts` | Add Google and GitHub providers, add PrismaAdapter | ~25 |
| `src/lib/auth.ts` | Update authOptions with adapter config, update callbacks | ~20 |
| `src/components/LoginForm.tsx` | Add social login buttons alongside existing form | ~30 |
| `src/components/SocialLoginButtons.tsx` | New: Google and GitHub OAuth buttons | ~25 |
| `src/app/(auth)/login/page.tsx` | Import and render SocialLoginButtons | ~5 |
| `src/middleware.ts` | Handle OAuth callback routes in matcher | ~5 |
| `.env.local` | Add GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GITHUB_ID, GITHUB_SECRET | ~4 |
| `.env.example` | Add placeholder OAuth env vars | ~4 |
| `prisma/migrations/NNNN_add_oauth_accounts/migration.sql` | Generated migration for Account/Session tables | ~20 |
```

### Checkpoint 3: Agent considers alternatives (NextAuth v4 providers vs v5 migration vs custom OAuth)

**Phase:** Step 4 (Assess Complexity) / Step 5 (Create Plan — Alternatives section)

Because this is a Complex plan with architectural impact, the agent presents 2-3 alternative approaches with trade-offs before recommending one. The alternatives are concrete, with specific pros, cons, and effort estimates.

**Evidence expected:**

```
### Alternatives Considered
| Option | Pros | Cons | Effort |
|--------|------|------|--------|
| A: Add providers to NextAuth v4 | Minimal breaking changes, well-documented, adapter ecosystem | v4 is in maintenance mode, migration to v5 eventually needed | ~4 hours |
| B: Migrate to NextAuth v5 (Auth.js) then add providers | Future-proof, better App Router support, Edge runtime compatible | Larger scope, v5 has breaking API changes, migration risk for existing users | ~8-12 hours |
| C: Custom OAuth implementation (no library) | Full control, no dependency on NextAuth release cycle | Must handle PKCE, token refresh, CSRF manually; higher security risk | ~16+ hours |
**Recommended:** Option A because the project already uses NextAuth v4, the scope is contained, and providers can be added without disrupting existing email/password auth. Migrate to v5 as a separate planned effort later.
```

### Checkpoint 4: Agent presents alternatives with trade-offs and recommendation

**Phase:** Step 5 (Create Plan — Alternatives section)

The recommendation includes reasoning that connects to the project's current state (already on v4, existing users, session strategy). The agent does not just pick the easiest option — it explains why it is the right choice given the constraints.

**Evidence expected:**

The recommendation references:
- The project already uses NextAuth v4 (switching to v5 is a separate migration)
- Existing users have credential-based sessions that must continue working
- Custom OAuth introduces security risk without justification
- The effort delta between Option A (4 hours) and Option B (8-12 hours) is not justified when v5 migration can be done later

### Checkpoint 5: Agent creates step-by-step plan with specific file paths and code shapes

**Phase:** Step 5 (Create Plan — Steps section)

Every plan step includes an exact file path, a specific description of the change, a code shape showing the structure (not full implementation), and a clear deliverable. Steps are ordered by dependency.

**Evidence expected:**

```
**Step 1: Add Account and Session models to Prisma schema** (~3 min)
- File: `prisma/schema.prisma`
- Change: Add NextAuth-required Account and Session models with relations to User
- Code shape:
  ```prisma
  model Account {
    id                String  @id @default(cuid())
    userId            String
    type              String
    provider          String
    providerAccountId String
    refresh_token     String? @db.Text
    access_token      String? @db.Text
    // ... standard NextAuth fields
    user              User    @relation(fields: [userId], references: [id], onDelete: Cascade)
    @@unique([provider, providerAccountId])
  }
  ```
- Deliverable: Prisma schema validates (`npx prisma validate`) with Account and Session models

**Step 2: Generate and apply Prisma migration** (~2 min)
- File: `prisma/migrations/NNNN_add_oauth_accounts/migration.sql` (generated)
- Change: Run `npx prisma migrate dev --name add_oauth_accounts`
- Deliverable: Migration applied, Account and Session tables exist in dev database

**Step 3: Add OAuth environment variables** (~2 min)
- Files: `.env.local`, `.env.example`
- Change: Add Google and GitHub OAuth credentials
- Code shape:
  ```env
  GOOGLE_CLIENT_ID=your-google-client-id
  GOOGLE_CLIENT_SECRET=your-google-client-secret
  GITHUB_ID=your-github-id
  GITHUB_SECRET=your-github-secret
  ```
- Deliverable: Env vars present in .env.local (real values) and .env.example (placeholders)
- Security: Verify .env.local is in .gitignore

**Step 4: Add PrismaAdapter and OAuth providers to NextAuth config** (~5 min)
- File: `src/app/api/auth/[...nextauth]/route.ts`
- Change: Import PrismaAdapter, add GoogleProvider and GitHubProvider alongside existing CredentialsProvider
- Code shape:
  ```typescript
  import { PrismaAdapter } from "@auth/prisma-adapter";
  import GoogleProvider from "next-auth/providers/google";
  import GitHubProvider from "next-auth/providers/github";

  export const authOptions: NextAuthOptions = {
    adapter: PrismaAdapter(prisma),
    providers: [
      CredentialsProvider({ /* existing config */ }),
      GoogleProvider({
        clientId: process.env.GOOGLE_CLIENT_ID!,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      }),
      GitHubProvider({
        clientId: process.env.GITHUB_ID!,
        clientSecret: process.env.GITHUB_SECRET!,
      }),
    ],
    callbacks: {
      // Preserve existing session/jwt callbacks, add account linking logic
    },
  };
  ```
- Deliverable: NextAuth config includes all three providers, app starts without errors
- Security: Validate redirect URL against allowlist in signIn callback, use state parameter for CSRF prevention (NextAuth handles this by default — verify it is not disabled)
```

### Checkpoint 6: Agent includes security checklist items connected to specific plan steps

**Phase:** Step 5 (Create Plan — Security Considerations)

Security considerations are not listed as a separate generic checklist. Instead, they are connected to the specific plan steps where they apply. Each security item references the step it belongs to and describes the concrete mitigation.

**Evidence expected:**

```
### Security Considerations

- **Step 3 (Env vars):** Verify `.env.local` is in `.gitignore`. Never commit OAuth client secrets.
- **Step 4 (Provider config):** NextAuth generates `state` parameter for CSRF prevention by default — verify it is not disabled in provider config. Validate `callbackUrl` in the `signIn` callback against an allowlist of permitted redirect URLs.
- **Step 4 (Callbacks):** OAuth tokens (`access_token`, `refresh_token`) are stored in the Account table — ensure database is encrypted at rest. Do not expose raw tokens in the JWT or client-side session.
- **Step 5 (Account linking):** When an existing user links an OAuth account, verify email ownership. An attacker could create a Google account with a victim's email to hijack their account. Require email verification or explicit user consent before linking.
- **Step 7 (UI):** Social login buttons must use NextAuth's `signIn()` function (which handles CSRF tokens) — do not construct OAuth URLs manually.
- **Step 7 (UI):** Validate that the OAuth redirect URI registered in Google/GitHub console matches the exact callback URL (`/api/auth/callback/google`, `/api/auth/callback/github`).
```

### Checkpoint 7: Agent identifies edge cases (existing user links account, email conflict between providers)

**Phase:** Step 5 (Create Plan — Edge Cases table)

The agent identifies edge cases specific to adding OAuth to an existing email/password system. Each edge case has explicit handling, not just a mention.

**Evidence expected:**

```
### Edge Cases
| Case | Handling |
|------|----------|
| Existing user with email@example.com signs in with Google using the same email | Link the Google account to the existing user automatically (NextAuth `allowDangerousEmailAccountLinking` or custom `signIn` callback). Log the linking event. |
| User's Google email differs from their registered email | Create a new account (do not merge). User can link accounts later from settings. |
| GitHub user has no public email | Fall back to GitHub API to fetch primary email. If no email available, prompt user to provide one. |
| User revokes OAuth access from Google/GitHub side | NextAuth refresh token becomes invalid. On next sign-in attempt, re-prompt OAuth consent. Handle `OAuthAccountNotLinked` error gracefully. |
| Existing session cookie after migration | Existing JWT sessions remain valid. Users with password-only auth continue to work. No forced re-login required. |
| Two providers return the same email for different people | Rely on provider + providerAccountId unique constraint. Do not auto-link based on email alone without verification. |
| Rate limiting on OAuth callback endpoint | NextAuth callback routes should be covered by existing rate limiting middleware. Verify `/api/auth/callback/*` is included in rate limit scope. |
```

### Checkpoint 8: Agent presents plan for user approval before any implementation

**Phase:** Step 6 (Wait for Approval)

The plan ends with an explicit approval gate. The agent does NOT start writing code, editing files, or running commands beyond read-only exploration. The agent waits for the user to approve, modify, or reject the plan.

**Evidence expected:**

```
---
**Approve this plan?** (yes / no / modify)
```

The agent's response ends here. No file writes, no code edits, no `npm install` commands follow. The next action is the user's response.

### Checkpoint 9: Plan connects security considerations to specific implementation steps

**Phase:** Step 5 (Create Plan — integrated throughout)

Security considerations are not a standalone section at the bottom of the plan that the implementer might skip. They are woven into the relevant plan steps as inline notes, so when `/implement` executes Step 4, the security requirements for that step are immediately visible.

**Evidence expected:**

Each security-sensitive step has a "Security:" annotation directly within the step description (see Checkpoint 5 example, Step 4). The separate Security Considerations section cross-references step numbers. A reader can trace from any security concern to the exact step where it must be addressed.

### Checkpoint 10: Plan is detailed enough to hand off to /implement

**Phase:** Step 5 (Create Plan) — overall assessment

The plan satisfies all quality checklist items:
- Every step has an exact file path
- Every step has a clear deliverable
- Code snippets show the shape of changes (function signatures, model definitions, component structure)
- Edge cases have explicit handling strategies
- Test strategy names specific scenarios
- Risks have mitigation strategies
- Steps are ordered by dependency (schema first, then config, then UI)
- No step takes longer than 5 minutes of focused work

**Evidence expected:**

The plan could be copy-pasted into `/implement` and executed step by step without the implementer needing to ask clarifying questions. File paths are absolute (within the project), code shapes show imports and signatures, and deliverables are verifiable.

## Anti-Patterns

### 1. Agent plans without first exploring the existing code

**Wrong:** Agent reads the task description ("add OAuth2 login"), assumes a standard Next.js + NextAuth setup, and produces a generic plan without reading any existing files.

The plan would miss project-specific details: the existing CredentialsProvider config, the custom session utilities, the middleware's route protection logic, and the Prisma schema's current structure. A plan built on assumptions rather than code exploration will have wrong file paths, miss existing patterns, and conflict with the codebase's conventions.

### 2. Agent skips alternatives analysis for a significant architectural decision

**Wrong:** Agent immediately plans for "add Google and GitHub providers to NextAuth v4" without considering whether to migrate to v5 first or build custom OAuth.

For Complex plans (6+ files, architectural impact), the skill requires presenting 2-3 alternative approaches with trade-offs. Adding OAuth providers is an architectural decision with long-term implications (library lock-in, migration path, security surface). Skipping alternatives analysis means the developer cannot make an informed choice.

### 3. Agent creates a plan too vague to implement

**Wrong:** Plan step says "Update the NextAuth config to support OAuth providers" without specifying which file, what the code looks like, or what the deliverable is.

Vague plans violate Iron Law 2 ("EVERY STEP MUST BE ACTIONABLE"). If an `/implement` agent cannot execute the step without asking clarifying questions, the plan is not detailed enough. Every step must have a file path, change description, code shape, and deliverable.

### 4. Agent ignores security implications of OAuth

**Wrong:** Agent plans the OAuth integration as purely a feature addition (add providers, add buttons, done) without addressing token storage, CSRF protection, redirect validation, or account linking vulnerabilities.

OAuth introduces significant security surface: redirect URL validation prevents open redirect attacks, state parameters prevent CSRF, email verification before account linking prevents account hijacking, and token storage requires encryption. A plan that omits security is incomplete and dangerous.

### 5. Agent starts implementation after creating the plan

**Wrong:** After producing the plan, the agent starts writing code — editing the Prisma schema, installing packages, or modifying the NextAuth config — without waiting for user approval.

Iron Law 3 states: "NO PLAN WITHOUT APPROVAL." The plan skill is read-only. Implementation is `/implement`'s job. The agent must present the plan and wait for explicit approval. Even after approval, the plan skill only persists todos (Step 7) and offers execution handoff (Step 8) — it does not write code.

### 6. Agent lists security considerations as a disconnected generic checklist

**Wrong:** Agent produces a "Security Considerations" section at the bottom of the plan with generic items like "Validate user input" and "Use HTTPS" that are not connected to any specific plan step.

Generic security checklists are ignored during implementation because they are not actionable in context. Security considerations must be connected to specific steps: "Step 4: Add OAuth callback handler — Security: validate redirect URL against allowlist, verify state parameter is not disabled." This ensures the security requirement is visible when the implementer reaches that step.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No alternatives analysis template | The skill mentioned alternatives for Complex/Risky plans but provided no template for how to structure the analysis, leading to inconsistent or skipped alternatives. | Added structured alternatives analysis template with columns for Option, Pros, Cons, Effort, and a Recommended row with reasoning. |
| Security checklist disconnected from plan steps | Security considerations were listed as a standalone section at the end of the plan, making them easy to skip during implementation and impossible to trace to specific steps. | Added instruction to connect security considerations to specific plan steps with inline "Security:" annotations and cross-references by step number. |
| Plan/implement boundary unclear | The skill did not clearly define when planning ends and implementation begins, leading to agents that start writing code after producing a plan or plans that are too vague because the agent expects to "figure it out during implementation." | Added explicit boundary definition: the plan is complete when every step has a file path, code shapes show the structure, edge cases are identified, and the user has approved. Implementation is /implement's job — /plan does not write code. |
