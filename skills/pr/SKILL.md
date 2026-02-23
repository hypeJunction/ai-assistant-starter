---
name: pr
description: Create a well-documented GitHub pull request with quality checks, proper description, and test plan. Use when pushing a branch, creating a merge request, or preparing code for review.
category: process
triggers:
  - create PR
  - pull request
  - ready for review
  - open PR
---

# Create Pull Request

> **Purpose:** Create a well-documented PR with proper description and test plan
> **Usage:** `/pr`

## Constraints

- All tests must pass before creating PR
- Never force push without explicit request
- Always verify changes are committed before pushing
- Requires `gh` (GitHub CLI) for PR creation
- Flag mixed-concern PRs (feature + refactor) as candidates for splitting

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Workflow

### Step 0: Check for Uncommitted Changes

```bash
git status --porcelain
```

If uncommitted changes are detected, present options and **wait for user response**:

```markdown
Uncommitted changes detected:
  [list of modified/untracked files]

Options:
  (a) Commit these changes first
  (b) Stash them for now
  (c) Abort — resolve manually

Which would you like to do?
```

**Do not proceed with uncommitted changes.** Handle them based on the user's choice before continuing.

### Step 1: Verify GitHub CLI Authentication

```bash
gh auth status
```

If not authenticated, instruct the user:

```markdown
GitHub CLI is not authenticated. Run `gh auth login` to authenticate, then re-run `/pr`.
```

**Do not proceed without authentication** — PR creation and existing PR detection both require it.

### Step 2: Verify Changes

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

git status
git diff $MAIN...HEAD --stat
git log $MAIN..HEAD --oneline
```

**If no commits ahead of base branch and no uncommitted changes:** Report "Nothing to push — branch is up to date with base" and exit.

### Step 3: Validate (with Re-Validation Loop)

Run full validation before creating PR. If issues are found, fix them and re-validate. Maximum 3 iterations. All checks must pass before proceeding.

```bash
npm run typecheck
npm run lint
npm run test
```

**Iteration loop:**

1. Run all validation checks
2. If issues are found (type errors, lint warnings/errors, test failures):
   - Fix the issues
   - Re-run all validation checks
3. Repeat until all checks pass or 3 iterations reached
4. If still failing after 3 iterations, report remaining issues and ask user how to proceed

Report format:

```markdown
### Validation (iteration N)

| Check | Status | Details |
|-------|--------|---------|
| Typecheck | PASSED / FAILED | [N errors] |
| Lint | PASSED / FAILED | [N errors, M warnings] |
| Tests | PASSED / FAILED | [N passed, M failed] |
```

**Do not proceed until all checks pass.**

### Step 4: Security Scan

Run concrete security scan commands against the changed files (see also `../commit/references/pre-commit-verification.md` and `../validate/references/security-scan-patterns.md` for detailed pattern guidance):

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
CHANGED_FILES=$(git diff $MAIN...HEAD --name-only)

# Secrets detection
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" $CHANGED_FILES

# Insecure pattern detection
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|document\.write\()" $CHANGED_FILES

# Raw SQL interpolation (injection risk)
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(\\\$queryRaw\`|\\\$executeRaw\`|\.query\(.*\\\$\{|SELECT.*\\\$\{|INSERT.*\\\$\{|UPDATE.*\\\$\{|DELETE.*\\\$\{)" $CHANGED_FILES

# Command injection patterns
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(child_process|exec\(|execSync\(|spawn\(|execFile\()" $CHANGED_FILES

# Disabled security controls
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(rejectUnauthorized:\s*false|NODE_TLS_REJECT_UNAUTHORIZED|--no-verify)" $CHANGED_FILES
```

**Interpreting results:**
- Secrets in non-test files: **BLOCKER** — do not proceed
- `eval`/`innerHTML`/`dangerouslySetInnerHTML`: Requires justification — flag for review
- Raw SQL with interpolation: **BLOCKER** unless using tagged template literals
- `child_process`/`exec`: Flag for review — verify no user input reaches the command
- Disabled TLS/verification: **BLOCKER** unless in test configuration only

Exclude test files and example/documentation files from blocking — flag as informational only.

### Step 5: Check for Mixed Concerns

Review the diff for mixed-concern changes. If commits include both feature work and refactoring, or both bug fixes and cleanup, suggest splitting into separate PRs for faster review.

### Step 6: Check for Existing PR

Before creating a new PR, check if one already exists for this branch:

```bash
gh pr view --json number,url,title,state 2>/dev/null
```

**If a PR exists:**

```markdown
Existing PR detected: #[number] ([state])
Title: [title]
URL: [url]

Options:
  (a) Update existing PR #[number]
  (b) Close #[number] and create a new PR
  (c) Abort

Recommend: Update existing PR.
```

**Wait for user response.** If updating, use `gh pr edit` instead of `gh pr create`.

### Step 7: Confirm Before Pushing

Present the full PR plan and **wait for explicit user approval** before pushing or creating/updating the PR:

```markdown
**Branch:** [branch name]
**Target:** [base branch]
**Commits:** [N commits]
**Action:** [Create new PR / Update existing PR #N]

**Proposed title:** [type]: [description]

[Full PR body preview]

Confirm push and [create/update] PR? (yes / edit / cancel)
```

**GATE: Do NOT push or create/update the PR until user responds with explicit approval.**

### Step 8: Push and Create/Update PR

```bash
git push -u origin HEAD
```

**If creating a new PR:**

```bash
gh pr create --title "[Type]: Brief description" --body "$(cat <<'EOF'
## Summary

[1-3 bullet points describing what this PR does]

## Changes

- [Specific change 1]
- [Specific change 2]

## Test Plan

- [ ] [How to test change 1]
- [ ] [How to test change 2]

## Security

- [ ] No secrets or credentials in code
- [ ] Input validation on new endpoints/handlers
- [ ] Auth checks on protected operations
- [ ] N/A — no security-sensitive changes

## Screenshots (if applicable)

[Add screenshots for UI changes]
EOF
)"
```

**If updating an existing PR:**

```bash
gh pr edit [number] --title "[Type]: Brief description" --body "$(cat <<'EOF'
[same body template as above]
EOF
)"
```

### Step 9: Report

```markdown
**PR:** #[number] — [title]
**URL:** [url]
**Status:** [Created / Updated]
**Branch:** [branch] → [base]
**Commits:** [N]

**Next:** Wait for CI checks, request reviewers, or continue working.
```

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| PR-T1 | Positive | "Create a pull request" | Skill triggers |
| PR-T2 | Positive | "Ready for review" | Skill triggers |
| PR-T3 | Positive | "Open a PR for this branch" | Skill triggers |
| PR-T4 | Negative | "Commit my changes" | Does NOT trigger (-> /commit) |
| PR-T5 | Negative | "Review the code" | Does NOT trigger (-> /review) |
| PR-T6 | Negative | "Fix the CI failures on my PR" | Does NOT trigger (-> /iterate-pr) |
| PR-T7 | Boundary | "Commit and create a PR" | Triggers (PR is the final intent) |
| PR-T8 | Early-exit | No commits ahead of base branch | Reports "Nothing to push" and exits |

## PR Title Conventions

```
feat: add user authentication
fix: resolve login issue with special characters
refactor: extract validation logic
docs: update API documentation
test: add tests for auth module
chore: update dependencies
```

## Example PR Body

```markdown
## Summary

- Add JWT-based authentication to API endpoints
- Implement login and registration endpoints
- Protect existing routes with auth middleware

## Changes

- `src/middleware/auth.ts` - New auth middleware
- `src/routes/auth.ts` - Login/register endpoints
- `src/models/User.ts` - User model with password hashing

## Test Plan

- [ ] Register new user with valid credentials
- [ ] Login with correct credentials returns token
- [ ] Protected routes reject requests without token

## Breaking Changes

None - new endpoints only.
```
