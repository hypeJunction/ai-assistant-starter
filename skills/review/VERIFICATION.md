# Review Skill Verification

## Scenario

A developer has a branch with 12 changed files totaling 650 lines of diff. Among the changes:

- `src/api/users.controller.ts` has a mass assignment vulnerability: the raw `req.body` is passed directly to `prisma.user.create({ data: req.body })` without field allowlisting.
- `src/services/notification.service.ts` has a missing `await` on an async call: `sendEmail(user.email, template)` is called without `await`, so failures are silently dropped and the caller proceeds before the email is sent.
- `src/services/auth.service.ts` has excellent error handling: custom error classes, proper try/catch boundaries, and actionable error messages.

The remaining 9 files are clean: type definitions, tests, utility functions, and configuration.

They invoke `/review`.

### Changed Files

| File | Lines | Issue |
|------|-------|-------|
| `src/api/users.controller.ts` | +85 | Mass assignment: `prisma.user.create({ data: req.body })` on line 34 |
| `src/services/notification.service.ts` | +62 | Missing `await`: `sendEmail(user.email, template)` on line 47 |
| `src/services/auth.service.ts` | +95 | Excellent error handling (positive finding) |
| `src/types/user.ts` | +30 | Clean |
| `src/types/notification.ts` | +18 | Clean |
| `src/api/users.controller.spec.ts` | +110 | Clean |
| `src/services/notification.service.spec.ts` | +72 | Clean |
| `src/services/auth.service.spec.ts` | +88 | Clean |
| `src/utils/validators.ts` | +35 | Clean |
| `src/middleware/rate-limit.ts` | +25 | Clean |
| `src/config/database.ts` | +15 | Clean |
| `prisma/schema.prisma` | +15 | Clean (schema change — escalation flag) |

**Total:** 12 files, ~650 lines

## Expected Outcome

The review report identifies the mass assignment vulnerability as P0 Critical (with HIGH confidence and evidence from the code), the missing `await` as P1 High (with evidence of what breaks: silently dropped email failures), acknowledges the good error handling in `auth.service.ts` as a Positive Note, flags the 650-line diff as large and asks the user how to proceed, and produces an accurate "Files Reviewed" table covering all 12 files.

## Key Checkpoints

### Checkpoint 1: Agent gathers context (current branch, base branch, PR info if available)

**Phase:** Step 1 (Gather Context)

The agent runs `git branch --show-current` to identify the current branch, determines the base branch via `git symbolic-ref`, and attempts to fetch PR metadata with `gh pr view`. This establishes the review scope before any code is read.

**Evidence expected:**
```
Branch: feat/user-management
Base: main
PR: #42 — "Add user management API and notification service"
```

### Checkpoint 2: Agent gets the full diff and validates scope (flags 650-line diff as large)

**Phase:** Step 2 (Get the Diff) / Step 3 (Validate Scope)

The agent runs `git diff main...HEAD --stat` and sees 12 files, ~650 lines. Since this exceeds the 500-line threshold, the agent warns the user and asks whether to do a full review or focused review. The agent does NOT silently proceed with a partial review.

**Evidence expected:**
```
12 files changed, 650 insertions(+)

This is a large diff (650 lines, >500 threshold).
Would you like:
1. Full review — all files, reviewed in logical groups
2. Focused review — specific areas (e.g., API routes only, tests only)
```

### Checkpoint 3: Agent reads EVERY changed file fully before forming opinions (Iron Law 1)

**Phase:** Step 4 (Review Each File)

After the user selects full review, the agent reads all 12 changed files in their entirety — not just the diff hunks but the full file content for context. The agent does NOT form conclusions after reading only the first few files.

**Evidence expected:**

The agent issues read commands for all 12 files before producing any findings. No interim judgments appear between file reads. The review begins only after all files have been loaded.

### Checkpoint 4: Agent detects mass assignment vulnerability (P0 with HIGH confidence + evidence)

**Phase:** Step 4 (Review Each File — Security checks)

The agent identifies `prisma.user.create({ data: req.body })` in `users.controller.ts:34` as a mass assignment vulnerability. The finding includes HIGH confidence, the specific line, and a concrete explanation of why it is dangerous (an attacker can set `role`, `isAdmin`, or any field the Prisma model accepts).

**Evidence expected:**
```
### P0 Critical

1. **Mass assignment vulnerability** — `src/api/users.controller.ts:34` — Confidence: HIGH
   - **Evidence:** `prisma.user.create({ data: req.body })` passes the entire request body
     directly to Prisma without field selection. An attacker can set any field accepted
     by the User model (e.g., `role`, `isAdmin`, `emailVerified`) by including extra
     fields in the POST body.
   - **Fix:** Use explicit field mapping or Prisma `select`:
     ```typescript
     prisma.user.create({
       data: {
         name: req.body.name,
         email: req.body.email,
         // Only allowed fields
       }
     })
     ```
```

### Checkpoint 5: Agent detects missing await (P1 with evidence of what breaks)

**Phase:** Step 4 (Review Each File — Correctness checks)

The agent identifies the missing `await` on `sendEmail(user.email, template)` in `notification.service.ts:47`. The finding explains the concrete impact: email send failures are silently swallowed, the calling function returns before the email is actually sent, and any error in `sendEmail` becomes an unhandled promise rejection.

**Evidence expected:**
```
### P1 High

1. **Missing await on async call** — `src/services/notification.service.ts:47` — Confidence: HIGH
   - **Evidence:** `sendEmail(user.email, template)` is an async function called without
     `await`. The caller proceeds immediately, so: (a) email failures are silently dropped
     (no error handling), (b) the function's return value suggests the email was sent when
     it may not have been, (c) in test environments, the process may exit before the email
     promise resolves.
   - **Fix:** Add `await`: `await sendEmail(user.email, template)` and ensure the
     surrounding try/catch covers the email send failure.
```

### Checkpoint 6: Agent checks for mitigation before reporting

**Phase:** Step 4 (Review Each File — before finalizing severity)

Before finalizing the mass assignment as P0, the agent checks whether mitigations exist: Does the Prisma User model use `select` to limit returned fields? Is there input validation middleware (e.g., Zod schema) that strips unknown fields before `req.body` reaches the controller? Is there a DTO layer that maps only specific fields?

**Evidence expected:**

The agent reads the Prisma schema (`prisma/schema.prisma`), checks for validation middleware in the route chain, and looks at `src/utils/validators.ts` for relevant Zod schemas. If no mitigation is found, the P0 stands at HIGH confidence. If a Zod schema strips unknown fields upstream, confidence might be adjusted to MEDIUM with a note that the mitigation exists but defense-in-depth is recommended.

### Checkpoint 7: Agent acknowledges good error handling pattern (Positive Notes)

**Phase:** Step 5 (Generate Report — Positive Notes section)

The agent calls out the excellent error handling in `auth.service.ts` as a positive finding. The praise is specific — not generic "good job" but identifies what patterns make it good (custom error classes, proper try/catch boundaries, actionable error messages).

**Evidence expected:**
```
### Positive Notes

- **Excellent error handling in auth.service.ts** — Custom error classes (e.g.,
  `AuthenticationError`, `TokenExpiredError`) with proper try/catch boundaries.
  Error messages are actionable for callers without leaking internal details.
  This is a good pattern to follow in other services.
```

### Checkpoint 8: Agent generates structured report with all severity sections

**Phase:** Step 5 (Generate Report)

The agent produces the full report following the template: Summary, P0 Critical, P1 High, P2 Medium, P3 Low, Positive Notes, Escalation Flags, Files Reviewed table, Areas Not Covered, Residual Risks, and Recommendation. The Files Reviewed table includes all 12 files with accurate status indicators.

**Evidence expected:**

The report contains all sections from the template. The Files Reviewed table has 12 rows. The Escalation Flags section mentions the Prisma schema change. The Recommendation is "Request Changes" due to the P0 finding.

```
### Files Reviewed
| File | Status | Notes |
|------|--------|-------|
| src/api/users.controller.ts | RED | Mass assignment vulnerability (P0) |
| src/services/notification.service.ts | YELLOW | Missing await (P1) |
| src/services/auth.service.ts | GREEN | Excellent error handling |
| src/types/user.ts | GREEN | Clean type definitions |
| ... | ... | ... |

### Escalation Flags
- Prisma schema change in `prisma/schema.prisma` — review for migration impact

---
**Recommendation:** Request Changes (P0 mass assignment must be fixed before merge)
```

### Checkpoint 9: Agent presents action menu

**Phase:** Step 6 (Action Menu)

The agent presents the action menu exactly as defined in the skill: Fix all, Fix P0-P1 only, Fix specific items, No changes. The menu appears after the full report is presented.

**Evidence expected:**
```
**What would you like to do?**
1. **Fix all** — Apply fixes for all P0-P2 findings
2. **Fix P0-P1 only** — Critical and high issues only
3. **Fix specific items** — Choose which (e.g., "P0.1, P1.1")
4. **No changes** — Keep as read-only review
```

### Checkpoint 10: Agent waits for user selection before making any changes

**Phase:** Step 6 (Action Menu — gate)

The agent stops after presenting the menu. No files are modified. No `git` commands are run. The agent waits for the user to respond with their selection.

**Evidence expected:**

The agent's response ends with the action menu. No file writes, no code edits, no git operations follow. The next action is the user's choice.

## Anti-Patterns

### 1. Agent forms opinions after reading only some files

**Wrong:** Agent reads `users.controller.ts`, immediately reports the mass assignment, then continues reading other files.

Iron Law 1 requires reading ALL changed files before forming any opinion. The remaining files might contain mitigating factors (e.g., a validation middleware, a DTO layer) that change the severity or confidence of findings. Partial-read conclusions lead to false positives and missed context.

### 2. Agent reports theoretical issues without evidence

**Wrong:** Agent reports "There might be SQL injection if user input reaches the database" without identifying a specific line where this occurs.

Iron Law 2 requires evidence for every P0/P1 finding. Every finding must cite the specific file, line, and code, and explain concretely why it is a real problem — not a hypothetical "could happen if" scenario. Theoretical concerns without code evidence should not appear above P2.

### 3. Agent misses the mass assignment because it is not in the inline checklist

**Wrong:** Agent runs through the inline security checklist in Step 4, which (before the improvement) did not include mass assignment. Since the checklist did not mention it, the agent does not flag `prisma.user.create({ data: req.body })`.

The review checklist in `references/review-checklist.md` already included mass assignment, but if the agent only uses the inline checklist in SKILL.md, the vulnerability is missed. Both checklists should be consulted. The improvement adds mass assignment to the inline checklist to prevent this gap.

### 4. Agent skips the action menu and jumps to fixing

**Wrong:** Agent detects P0 and P1 issues, immediately starts editing files to fix them without presenting the action menu or waiting for user confirmation.

The review is read-only through Steps 1-5. The action menu in Step 6 is a mandatory gate. The user may want to fix issues themselves, may disagree with a finding, or may want to discuss before changes are made. Skipping the menu violates the user's control over their codebase.

### 5. Agent makes changes in read-only mode

**Wrong:** During the review (Steps 1-5), the agent modifies a file to "test a theory" about whether a bug is real, or runs `npm test` to verify test coverage.

The review mode is strictly read-only. No file modifications, no command execution beyond git/gh for context gathering, and no test runs during the review phase. Write operations are only permitted after the user selects a fix option from the action menu.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| Mass assignment not in inline security checklist | The inline security checks in Step 4 of SKILL.md did not include mass assignment. The `references/review-checklist.md` had it, but an agent using only the inline list would miss it. | Added mass assignment check to the inline security checklist: "No mass assignment — request body should not be passed directly to ORM create/update without field allowlisting." |
| No mitigation search before reporting | The skill instructed the agent to find issues and report them, but did not instruct the agent to search for existing mitigations before setting severity and confidence. This leads to false positives when validation or field filtering exists upstream. | Added mitigation search instruction: before reporting P0/P1, search for existing mitigations (ORM field selection, input validation, middleware). Adjust confidence based on mitigation presence. |
| No large diff review strategy | Step 3 flagged large diffs (>500 lines) but provided no guidance on how to actually review them. The agent would either silently do a partial review or attempt everything without structure. | Added large diff strategy: ask user for full or focused review, review in logical groups, prioritize security-sensitive files, track which files have been reviewed. |
| Read-only/fix mode transition not clarified | The skill starts as read-only but the action menu offers fix options. There was no explicit instruction about when the mode transition happens, leading to agents making changes during the review phase or being confused about permissions. | Added explicit mode transition rule: Steps 1-5 are strictly read-only. Write mode begins only after user selects a fix option. Fixes applied in priority order (P0 first) with typecheck and lint after each. |
