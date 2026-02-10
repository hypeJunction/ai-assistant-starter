---
name: git-conventions
description: Git branch naming, commit message conventions (Conventional Commits), workflow patterns, and common operations. Auto-loaded when working with git.
user-invocable: false
---

# Git Conventions

## Branch Naming

```bash
feature/add-user-authentication
feature/TICKET-123-payment-integration
fix/login-redirect-loop
fix/TICKET-456-null-pointer
hotfix/security-patch-xss
chore/upgrade-dependencies
chore/refactor-api-client
experiment/new-caching-strategy
```

## Commit Messages (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature for users |
| `fix` | Bug fix for users |
| `docs` | Documentation changes |
| `style` | Formatting, no code change |
| `refactor` | Code change, no feature/fix |
| `perf` | Performance improvement |
| `test` | Adding/fixing tests |
| `chore` | Maintenance, deps, config |
| `ci` | CI/CD changes |
| `revert` | Reverting previous commit |

### Subject Line Rules

- Use imperative mood ("add" not "added" or "adds")
- No period at the end
- Max 50 characters (72 for body lines)
- Capitalize first letter
- Reference issues when applicable

### Examples

```bash
feat(auth): add OAuth2 login with Google

Implements Google OAuth2 flow for user authentication.
Users can now sign in with their Google accounts.

Closes #123

fix(cart): prevent duplicate items on rapid clicks

Added debounce to add-to-cart button to prevent
race condition when users click rapidly.

feat(api)!: change user endpoint response format

BREAKING CHANGE: User endpoint now returns nested
address object instead of flat fields.
```

## Workflow Patterns

### Feature Development

```bash
# 1. Start from updated main
git checkout main && git pull

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make atomic commits
git add -p
git commit -m "feat(scope): implement X"

# 4. Keep updated
git fetch origin
git rebase origin/main

# 5. Push and create PR
git push -u origin feature/my-feature
```

## Safety Rules

- **Never rewrite public history** (no force push to main)
- **Never amend pushed commits** (only for unpushed)
- **Never commit sensitive data** (.env, credentials, keys)
- **Use `--force-with-lease`** if force push is needed on feature branch
- **Keep commits atomic** — one logical change per commit
- **Keep PRs small** — under 400 lines ideal

## Common Operations

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Stash changes
git stash push -m "work in progress"
git stash pop

# Cherry-pick
git cherry-pick <commit-hash>

# Interactive rebase (squash WIP commits before PR)
git rebase -i HEAD~3
```
