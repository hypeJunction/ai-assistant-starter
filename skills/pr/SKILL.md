---
name: pr
description: Create a well-documented GitHub pull request with quality checks, proper description, and test plan. Use when pushing a branch, creating a merge request, or preparing code for review.
---

# Create Pull Request

> **Purpose:** Create a well-documented PR with proper description and test plan
> **Usage:** `/pr`

## Constraints

- All tests must pass before creating PR
- Never force push without explicit request
- Always verify changes are committed before pushing
- Requires `gh` (GitHub CLI) for PR creation

## Workflow

### Step 1: Verify Changes

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

git status
git diff $MAIN...HEAD --stat
git log $MAIN..HEAD --oneline
```

### Step 2: Ensure Quality

Before creating PR, run validation:

```bash
npm run typecheck
npm run lint
npm run test
```

Checklist:
- [ ] All tests pass
- [ ] No type errors
- [ ] Linting passes
- [ ] Changes are committed

### Step 3: Push Branch

```bash
git push -u origin HEAD
```

### Step 4: Create PR

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

## Screenshots (if applicable)

[Add screenshots for UI changes]
EOF
)"
```

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
