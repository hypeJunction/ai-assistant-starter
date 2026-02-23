# Iterate PR — Verification Scenario

## Scenario

A developer has PR #42 open. CI is failing (lint error in `src/api/routes.ts`), there is one reviewer comment requesting a type fix in `src/types/user.ts`, and there is a merge conflict in `package-lock.json`. They invoke `/iterate-pr`.

### PR State

| Issue | Type | Details |
|-------|------|---------|
| CI failure | Lint | `no-unused-vars` violation in `src/api/routes.ts:14` — unused `req` parameter |
| Review comment | P1 (type fix) | Reviewer requests replacing `any` with `UserResponse` in `src/types/user.ts:8` |
| Merge conflict | Conflict | `package-lock.json` conflicts with base branch after a dependency update |

## Expected Outcome

The agent fetches PR status, categorizes all issues (CI failure, review feedback, conflict), fixes the lint error, applies the type fix, resolves the merge conflict, runs local validation, pushes, and verifies CI passes.

## Key Checkpoints

### Checkpoint 1: Agent verifies `gh` CLI is authenticated

**Phase:** Preflight

The agent runs `gh auth status` as the very first step. If authentication fails, the agent instructs the user to run `gh auth login` and aborts the workflow.

**Evidence expected:**
```
Verifying GitHub CLI authentication...
gh auth status: Logged in to github.com as developer-user
```

### Checkpoint 2: Agent fetches PR status (CI checks, review comments, conflicts)

**Phase:** Fetch PR Status (Phase 1)

The agent runs `gh pr view`, `gh pr checks`, and the reviews/comments API calls to gather the full picture of PR #42, including CI check results, review comments, and merge conflict state.

**Evidence expected:**
```
## PR #42: Add user profile endpoint

URL: https://github.com/org/repo/pull/42
State: open
Review Decision: changes_requested

### CI Status
| Check | Status | Details |
|-------|--------|---------|
| lint | FAIL | no-unused-vars in src/api/routes.ts:14 |
| typecheck | PASS | |
| tests | PASS | |

### Review Comments
- @reviewer on `src/types/user.ts:8`: Replace `any` with `UserResponse`

### Conflicts
- package-lock.json
```

### Checkpoint 3: Agent categorizes issues by severity (CI failure, review feedback, conflict)

**Phase:** Categorize Findings (Phase 2)

The agent groups all findings into actionable categories: CI failures, review feedback (by severity), and merge conflicts. Conflicts are treated as P0 blockers.

**Evidence expected:**
```
## Findings Summary

**Conflicts:** 1 file (package-lock.json) — must resolve before push
**CI:** 1 failure (lint)
**Reviews:** 1 comment (P1)

Proceed with fixes?
```

### Checkpoint 4: Agent fixes CI failure (lint error)

**Phase:** Address Findings (Phase 3)

The agent reads the lint failure log, identifies the `no-unused-vars` violation in `src/api/routes.ts:14`, fixes it (e.g., prefixing with `_` or removing the unused parameter), and runs the linter locally to confirm the fix.

**Evidence expected:**
```
Fixed lint error: no-unused-vars in src/api/routes.ts:14
  - Renamed unused `req` parameter to `_req`
Local lint check: PASSED
```

### Checkpoint 5: Agent addresses review comment (type fix)

**Phase:** Address Findings (Phase 3)

The agent reads the review comment requesting a type fix in `src/types/user.ts:8`, replaces `any` with `UserResponse`, and runs typecheck locally to confirm the change compiles.

**Evidence expected:**
```
Fixed P1: Replaced `any` with `UserResponse` in src/types/user.ts:8
Local typecheck: PASSED
```

### Checkpoint 6: Agent resolves merge conflict

**Phase:** Address Findings (Phase 3)

The agent fetches the latest base branch, rebases or merges, resolves the `package-lock.json` conflict (by accepting the appropriate version and regenerating if needed), and runs validation after resolution.

**Evidence expected:**
```
Resolving merge conflict in package-lock.json...
  - Fetched latest main branch
  - Merged main into feature branch
  - Resolved package-lock.json conflict (accepted base, regenerated lock file)
Post-merge validation: PASSED
```

### Checkpoint 7: Agent runs local validation (typecheck, lint, tests) before pushing

**Phase:** Pre-push Validation (Phase 4)

Before pushing any changes, the agent runs full local validation: typecheck, lint, and tests. The agent does not push code that fails locally.

**Evidence expected:**
```
### Pre-push Validation
- Typecheck: PASSED
- Lint: PASSED
- Tests: PASSED (24/24)
All checks green — safe to push.
```

### Checkpoint 8: Agent pushes fixes

**Phase:** Commit and Push (Phase 4)

The agent creates separate commits for functional fixes and pushes them. No force push is used.

**Evidence expected:**
```
Committed: fix: resolve lint error and apply type fix from review
Committed: chore: resolve merge conflict with main
Pushed to origin/feat/user-profile
```

### Checkpoint 9: Agent verifies CI passes after push (or reports if still failing)

**Phase:** Verify and Reply (Phase 5)

The agent watches CI checks after push and reports the results. If CI still fails, the agent reports what is still failing rather than silently moving on.

**Evidence expected:**
```
## Iteration 1 Result

CI after push:
| Check | Status |
|-------|--------|
| lint | PASS |
| typecheck | PASS |
| tests | PASS |

All CI checks passing. Replied to resolved review threads.
```

### Checkpoint 10: Agent handles the case where fixing one issue introduces another

**Phase:** Loop or Exit (Phase 6)

If fixing the lint error or type change introduces a new issue (e.g., the type fix causes a downstream type error), the agent detects this in local validation, fixes the cascading issue before pushing, and reports the chain of fixes. The agent does not push code that fails locally.

**Evidence expected:**
```
Pre-push validation found new issue:
  - Typecheck error: Property 'data' does not exist on type 'UserResponse'
  - Root cause: Type fix in user.ts changed the shape expected downstream
  - Fix: Updated src/api/routes.ts:22 to use UserResponse.data field
  - Re-validation: PASSED
```

## Anti-Patterns

### 1. Pushing without running local validation first

**Wrong:** Fix the lint error and type issue, then immediately `git push` without running typecheck, lint, or tests locally.

The type fix could introduce downstream type errors, or the lint fix could break a test. Local validation must pass before any push.

### 2. Ignoring merge conflicts

**Wrong:** Agent sees the merge conflict in `package-lock.json` but proceeds to push fixes for lint and review feedback, leaving the conflict unresolved.

Merge conflicts block the PR from being merged regardless of CI status. Conflicts must be resolved as part of the iteration.

### 3. Skipping `gh auth` verification

**Wrong:** Agent jumps directly to `gh pr view` without first verifying authentication. The command fails with an auth error mid-workflow, wasting work already done.

Authentication must be verified as the first step so failures are caught early.

### 4. Blindly dismissing review comments

**Wrong:** Agent resolves review threads by posting "Acknowledged" without actually making the requested change, or marks comments as resolved without pushing a fix.

Review threads should only be replied to after a corresponding fix is pushed. The reply should reference the commit SHA.

### 5. Pushing repeatedly without checking results

**Wrong:** Agent pushes, sees CI still failing, pushes another fix, sees CI still failing, pushes again — without analyzing why CI keeps failing or whether the fixes are addressing the right issue.

Each push-and-check cycle must include analysis of what failed and why. Maximum 3 iterations before escalating to the user.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No gh auth preflight | Agent assumed `gh` was authenticated, leading to mid-workflow failures | Added `gh auth status` as mandatory first step with abort on failure |
| No explicit CI failure fixing sequence | Agent had no structured approach to reading failure logs and fixing root causes | Added sequence: read log, identify cause, fix locally, verify locally, then proceed |
| No local validation before push | Agent could push code that fails typecheck, lint, or tests | Added mandatory pre-push validation gate — no push until all local checks pass |
| No conflict handling guidance | Merge conflicts were not mentioned in the workflow | Added conflict detection, resolution steps, and post-merge validation |
| No iteration limit enforcement | Agent could loop indefinitely pushing broken code | Added maximum 3 push-and-check cycles with escalation to user after limit |
