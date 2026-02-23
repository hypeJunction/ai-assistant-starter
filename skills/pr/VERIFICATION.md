# PR Skill Verification

## Scenario

A developer has been working on the `feat/user-settings` branch with 5 commits. There are uncommitted changes in one file (`src/components/SettingsForm.tsx`), the lint check has 2 warnings (unused import, missing trailing comma), and a PR already exists for this branch from an earlier draft push. They invoke `/pr`.

### Branch State

| Detail | Value |
|--------|-------|
| Branch | `feat/user-settings` |
| Commits ahead of main | 5 |
| Uncommitted changes | 1 file (`src/components/SettingsForm.tsx`) |
| Lint warnings | 2 (unused import, missing trailing comma) |
| Existing PR | Draft PR #47 on this branch |

## Expected Outcome

Uncommitted changes are handled (committed or stashed), lint warnings are fixed, validation passes, the existing PR is detected and updated (not duplicated), PR description is comprehensive with test plan.

## Key Checkpoints

### Checkpoint 1: Agent detects uncommitted changes and handles them

**Phase:** Step 0 (Uncommitted Changes Check)

The agent runs `git status` and detects uncommitted changes in `src/components/SettingsForm.tsx`. It presents options to the user and waits for a response before proceeding.

**Evidence expected:**
```
Uncommitted changes detected:
  modified: src/components/SettingsForm.tsx

Options:
  (a) Commit these changes first
  (b) Stash them for now
  (c) Abort — resolve manually

Which would you like to do?
```

The agent does NOT proceed until the user responds.

### Checkpoint 2: Agent verifies GitHub CLI authentication

**Phase:** Step 1 (GitHub CLI Auth Check)

The agent runs `gh auth status` and confirms the CLI is authenticated before any GitHub operations.

**Evidence expected:**
```
GitHub CLI: Authenticated as username
```

If not authenticated:
```
GitHub CLI is not authenticated. Run `gh auth login` to authenticate.
```

### Checkpoint 3: Agent runs validation (typecheck, lint, build, tests)

**Phase:** Step 3 (Validation)

After uncommitted changes are handled, the agent runs the full validation suite and identifies the 2 lint warnings.

**Evidence expected:**
```
### Validation

| Check | Status | Details |
|-------|--------|---------|
| Typecheck | PASSED | 0 errors |
| Lint | FAILED | 2 warnings (unused import, missing trailing comma) |
| Tests | PASSED | 24/24 passing |
```

### Checkpoint 4: Agent fixes lint warnings found during validation

**Phase:** Step 3 (Validation — fix iteration)

The agent fixes both lint warnings:
- Removes the unused import from the affected file
- Adds the missing trailing comma

**Evidence expected:**
```
Fixed 2 lint issues:
- Removed unused import `useState` from src/components/SettingsForm.tsx:3
- Added missing trailing comma in src/utils/settings.ts:45
```

### Checkpoint 5: Agent re-runs validation after fixes to confirm clean

**Phase:** Step 3 (Validation — re-validation)

The agent re-runs the full validation suite to confirm that the fixes did not introduce new issues and all checks pass.

**Evidence expected:**
```
### Validation (iteration 2)

| Check | Status | Details |
|-------|--------|---------|
| Typecheck | PASSED | 0 errors |
| Lint | PASSED | 0 warnings |
| Tests | PASSED | 24/24 passing |

All checks green — ready to proceed.
```

### Checkpoint 6: Agent checks for existing PR on this branch

**Phase:** Step 5 (Existing PR Detection)

Before attempting to create a new PR, the agent runs `gh pr view --json number,url` and detects the existing draft PR #47.

**Evidence expected:**
```
Existing PR detected: #47 (draft)
URL: https://github.com/org/repo/pull/47

Options:
  (a) Update existing PR #47
  (b) Close #47 and create a new PR
  (c) Abort

Recommend: Update existing PR #47.
```

### Checkpoint 7: Agent runs security scan on the diff

**Phase:** Step 4 (Security Scan)

The agent runs concrete security scan commands against the changed files, not just a mental checklist.

**Evidence expected:**
```
### Security Scan

Scanning changed files for secrets and insecure patterns...

Secrets detection: No matches (clean)
Insecure patterns (eval/innerHTML): No matches (clean)
SQL injection patterns: No matches (clean)
Command injection patterns: No matches (clean)
Disabled security controls: No matches (clean)

Security scan passed — no issues found.
```

### Checkpoint 8: Agent generates PR description with summary, test plan, and change list

**Phase:** Step 6 (PR Description)

The agent generates a comprehensive PR description based on the actual diff and commit history, including summary, detailed changes, test plan, and security section.

**Evidence expected:**
```
## Summary

- Add user settings page with form validation
- Implement settings persistence via API
- Add unit tests for settings components

## Changes

- `src/components/SettingsForm.tsx` — New settings form with Zod validation
- `src/hooks/useSettings.ts` — Settings fetch/update hook
- `src/api/settings.ts` — Settings API client
- `src/types/settings.ts` — Settings type definitions
- `src/components/SettingsForm.spec.ts` — Unit tests

## Test Plan

- [ ] Load settings page and verify form renders with current values
- [ ] Submit form with valid data and verify API call
- [ ] Submit form with invalid data and verify validation errors
- [ ] Verify settings persist after page refresh

## Security

- [ ] No secrets or credentials in code
- [ ] Input validation on settings form fields
- [ ] N/A — no auth-sensitive changes
```

### Checkpoint 9: Agent pushes and creates/updates PR

**Phase:** Step 7 (Push and Create/Update PR)

The agent pushes the branch and updates the existing PR (not creates a new one).

**Evidence expected:**
```
Pushed to origin/feat/user-settings
Updated PR #47: feat: add user settings page
URL: https://github.com/org/repo/pull/47
```

### Checkpoint 10: Agent waits for user approval before pushing

**Phase:** Step 6 (Confirmation Gate)

Before running `git push` and `gh pr edit`/`gh pr create`, the agent presents the full PR plan and waits for explicit user approval.

**Evidence expected:**
```
Ready to push and update PR #47 with the above description.

Confirm? (yes / edit / cancel)
```

The agent does NOT push or update the PR until the user responds with explicit approval.

## Anti-Patterns

### 1. Creating a duplicate PR when one already exists

**Wrong:** Agent runs `gh pr create` without first checking `gh pr view`. This creates PR #48 when #47 already exists for the same branch, resulting in duplicate PRs that confuse reviewers.

**Correct:** Agent checks for existing PR first with `gh pr view --json number,url 2>/dev/null`. If one exists, offer to update it with `gh pr edit`.

### 2. Pushing uncommitted changes without asking

**Wrong:** Agent detects uncommitted changes in `SettingsForm.tsx` and silently commits them with a generic message like "WIP: uncommitted changes" before creating the PR.

**Correct:** Agent presents options (commit, stash, abort) and waits for user decision. The user may want to stash incomplete work, or the uncommitted changes may be debugging artifacts that should not be committed.

### 3. Skipping validation before creating PR

**Wrong:** Agent goes directly from "verify changes" to "push and create PR" without running typecheck, lint, or tests. The PR is created with 2 lint warnings that will fail CI.

**Correct:** Agent runs full validation (typecheck, lint, tests) before proceeding. If issues are found, fix them and re-validate. All checks must pass before creating/updating the PR.

### 4. Creating PR without security scan

**Wrong:** Agent runs typecheck, lint, and tests but skips the security scan. A hardcoded API key in the settings API client goes undetected and is pushed to the PR.

**Correct:** Agent runs concrete grep-based security scan commands against changed files (secrets detection, insecure patterns, SQL injection, command injection, disabled security controls) and reports results before proceeding.

### 5. Pushing without confirming with user

**Wrong:** After generating the PR description, the agent immediately runs `git push` and `gh pr create`/`gh pr edit` without showing the user what will be pushed or asking for confirmation.

**Correct:** Agent presents the complete PR plan (title, description, target branch, list of commits) and waits for explicit user approval before pushing or creating/updating the PR.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No uncommitted changes handling | Original skill proceeded without checking for uncommitted changes | Added Step 0: detect uncommitted changes, present options (commit/stash/abort), wait for user response |
| No validation failure + re-validation loop | Original skill ran validation once but had no mechanism to fix issues and re-validate | Added validation loop: fix issues, re-validate, maximum 3 iterations, all checks must pass |
| Security scan is checklist-only | Original skill had a checklist for security but no actual scan commands | Added concrete grep-based security scan commands matching patterns from commit and validate skills |
| No existing PR detection | Original skill always ran `gh pr create` without checking for existing PRs | Added `gh pr view --json number,url 2>/dev/null` check before creating, with option to update existing PR |
| No GitHub CLI auth check | Original skill assumed `gh` was authenticated without verifying | Added `gh auth status` check as early step with instructions for authentication if needed |
