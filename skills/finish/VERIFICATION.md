# Finish Skill Verification

## Scenario

A developer has been working on a feature branch `feat/user-profile` with 6 changed files. Some files have `any` types and one test is failing. They invoke `/finish` to wrap up the session cleanly before stepping away.

### Changed Files

| File | Issue |
|------|-------|
| `src/components/UserProfile.tsx` | Contains `any` type for `props` |
| `src/components/UserProfile.spec.ts` | Failing test: "renders avatar correctly" |
| `src/utils/formatUser.ts` | Contains `any` return type |
| `src/utils/formatUser.spec.ts` | Passing |
| `src/hooks/useUserData.ts` | Clean |
| `src/types/user.ts` | Clean |

## Expected Outcome

All tests pass, validation (typecheck + lint + build) passes, a self-review catches the `any` types and they are fixed, the fix is re-validated, and a clean commit is created with user approval.

## Key Checkpoints

### Checkpoint 1: Agent runs tests and identifies the failing test

**Phase:** Test (Phase 2)

The agent runs scoped tests against the changed files and identifies that `UserProfile.spec.ts` has a failing test: "renders avatar correctly."

**Evidence expected:**
```
Tests: 1 failed, 5 passed
FAIL src/components/UserProfile.spec.ts > renders avatar correctly
```

### Checkpoint 2: Agent fixes the failing test (or the code causing it to fail)

**Phase:** Test (Phase 2)

The agent investigates the failure, determines whether the test expectation is wrong or the component code is wrong, and fixes accordingly. After the fix, the agent re-runs the test to confirm it passes.

**Evidence expected:**
```
Tests: 6 passed, 0 failed
```

### Checkpoint 3: Agent performs self-review catching `any` types

**Phase:** Review (Phase 3)

The agent reviews the diff and identifies `any` types in `UserProfile.tsx` (props) and `formatUser.ts` (return type). These are flagged as critical issues that must be fixed before proceeding.

**Evidence expected:**
```
### Review Findings
- CRITICAL: `any` type in UserProfile.tsx (line 12) — props parameter
- CRITICAL: `any` type in formatUser.ts (line 8) — return type
- No security issues found
- No console.log statements found
```

### Checkpoint 4: Agent fixes the `any` types found in review

**Phase:** Review (Phase 3)

The agent replaces `any` types with proper types:
- `UserProfile.tsx`: `any` props replaced with `UserProfileProps` interface
- `formatUser.ts`: `any` return type replaced with `FormattedUser` type

**Evidence expected:**
```
Fixed 2 `any` type issues:
- UserProfile.tsx: props: any -> props: UserProfileProps
- formatUser.ts: return any -> return FormattedUser
```

### Checkpoint 5: Agent runs full validation (typecheck, lint, build)

**Phase:** Validate (Phase 4)

After review fixes, the agent runs the full validation suite to confirm that fixing the `any` types did not introduce new type errors, lint violations, or build failures.

**Evidence expected:**
```
### Validation (post-review)
- Typecheck: PASSED
- Lint: PASSED
- Scoped tests: 6/6 passing
```

### Checkpoint 6: Re-validation confirms all checks pass

**Phase:** Validate (Phase 4)

This is the critical checkpoint. Because review fixes modified source files, validation must be re-run. The agent confirms that all checks pass on the final state of the code.

**Evidence expected:**
```
### Validation (final)
- Typecheck: PASSED (0 errors)
- Lint: PASSED (0 warnings)
- Scoped tests: 6/6 passing
- All checks green — ready to commit
```

### Checkpoint 7: Agent presents completion evidence with all results

**Phase:** Commit (Phase 5)

The agent presents a structured summary showing the results of every phase before proposing the commit.

**Evidence expected:**
```
## Wrap Summary

### Work Assessed
- Branch: feat/user-profile
- Files changed: 6

### Test Coverage
- UserProfile.spec.ts — fixed failing test, 3 tests passing
- formatUser.spec.ts — 3 tests passing

### Review
- Fixed 2 `any` type issues (UserProfile.tsx, formatUser.ts)
- No security issues

### Validation (final)
- Typecheck: PASSED
- Lint: PASSED
- Scoped tests: 6/6 passing

### Commit
- Pending user approval
```

### Checkpoint 8: Agent proposes commit message and waits for approval

**Phase:** Commit (Phase 5)

The agent stages all changes, shows the staged diff, proposes a commit message, and waits for explicit user confirmation before committing.

**Evidence expected:**
```
Ready to commit with message:
feat: add user profile component with avatar and formatting utils

Confirm commit? (yes / edit message / cancel)
```

The agent does NOT commit until the user responds with "yes."

## Anti-Patterns

### 1. Review AFTER validation

**Wrong order:** Test -> Validate -> Review -> Commit

If review happens after validation, the `any` type fixes made during review invalidate the validation results. The committed code may have type errors or lint violations introduced by the review fixes.

**Correct order:** Test -> Review (fix issues) -> Validate -> Commit

### 2. Commit without re-validating after fixes

**Wrong:** Fix `any` types during review, then commit immediately without re-running typecheck.

The type replacements (`any` to `UserProfileProps`) could reference a type that does not exist yet, or the new types could cause downstream type errors. Validation must run after every fix.

### 3. Silently skip `any` type issues

**Wrong:** Review checklist includes "No `any` types" but agent marks it as passing without actually scanning for them, or notes them as "suggestions" rather than critical issues.

`any` types should be treated as critical review findings that must be fixed before commit, unless explicitly documented as a todo with justification.

### 4. Proceed if test creation fails without reporting

**Wrong:** Agent tries to create a missing test file, the test framework is not configured or the code pattern is untestable, and the agent silently moves on to validation.

If a test cannot be created, the agent must report this to the user with the reason, and let the user decide whether to proceed without test coverage for that file.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| Phase ordering | Review was Phase 4 (after Validate Phase 3), so review fixes invalidated validation | Review moved before Validate — flow is now Test -> Review -> Validate -> Commit |
| No re-validation loop | After fixing review issues, no mechanism to re-run validation | Added re-validation step after review fixes with max 3 iterations |
| `any` type handling | No guidance on what to replace `any` with | Added specific guidance: `any` -> `unknown` for truly unknown types, specific types for known shapes |
| Test creation failures | Silent skip when test creation fails | Added requirement to report test creation failures to user |
