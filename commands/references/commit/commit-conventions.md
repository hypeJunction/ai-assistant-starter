# Commit Conventions

> **Attribution:** Commit message formats in this document follow the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specification, licensed under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).

Extended commit format reference for edge cases beyond the standard `type(scope): description` pattern.

## Breaking Changes

When a commit introduces a breaking change (API change, removed feature, changed behavior that requires consumers to update):

### Format

```
feat(api)!: change authentication to use JWT tokens

Migrate from session-based auth to JWT tokens.
All API consumers must update their auth headers.

BREAKING CHANGE: The /api/login endpoint now returns a JWT token
instead of setting a session cookie. Clients must include the token
in the Authorization header as "Bearer <token>".

Migration steps:
1. Update auth client to store JWT from login response
2. Add Authorization header to all API requests
3. Remove cookie-based session handling
```

### Rules

- Add `!` after the scope: `type(scope)!: description`
- Include `BREAKING CHANGE:` footer with migration instructions
- Describe what changed AND how consumers should adapt
- Both the `!` and the footer are required (belt and suspenders)

## Revert Commits

When reverting a previous commit:

### Format

```
revert: feat(auth): add OAuth2 login flow

Reverts commit abc1234.

Reason: OAuth2 integration causes redirect loop on Safari.
Will re-implement after fixing the callback URL handling.
```

### Rules

- Subject: `revert: <original commit subject>`
- Body: `Reverts commit <hash>.` followed by the reason
- Always include WHY the revert is needed
- Reference the original commit hash for traceability

## Multi-Issue References

### Syntax

| Keyword | Effect on Merge |
|---------|----------------|
| `Fixes #123` | Closes issue #123 |
| `Closes #123` | Closes issue #123 (same as Fixes) |
| `Resolves #123` | Closes issue #123 (same as Fixes) |
| `Refs #123` | Links to issue without closing |
| `Part of #123` | Links without closing (partial work) |

### Multiple Issues

```
feat(checkout): add payment validation

Validate payment details before processing checkout.

Fixes #123
Fixes #456
Refs #789
```

### Cross-Repo References

```
Fixes org/repo#123
```

## Scope Conventions

### By Project Type

**Monorepo (package-based):**
```
feat(web): add dark mode toggle
fix(api): handle null response from payment service
chore(shared): update TypeScript to 5.4
```

**Feature-based:**
```
feat(auth): add password reset flow
fix(checkout): correct tax calculation for EU
refactor(dashboard): extract chart components
```

**Layer-based:**
```
feat(routes): add /api/v2/users endpoint
fix(middleware): handle expired JWT gracefully
refactor(models): normalize user schema
```

### Scope Discovery

Choose scope based on what the project already uses:

```bash
# See what scopes have been used before
git log --oneline -50 | grep -oP '\(\K[^)]+' | sort | uniq -c | sort -rn
```

If no convention exists, use the most specific directory or module name.

## Commit Message Examples

### Good Messages

```
feat(search): add fuzzy matching for product names

Use Fuse.js for client-side fuzzy search. Matches on product name
and description with configurable threshold.

Refs #234
```

```
fix(auth): prevent token refresh race condition

Multiple concurrent requests could trigger simultaneous token refreshes,
causing all but the first to fail with 401. Add a mutex to ensure only
one refresh happens at a time while others wait for the result.

Fixes #567
```

```
refactor(api): replace manual SQL with Prisma queries

Migrate 12 raw SQL queries to Prisma Client. No behavior change.
Reduces SQL injection surface and improves type safety.
```

```
perf(images): lazy-load below-fold product images

Reduce initial page load by 2.3s (LCP) by deferring image loads
for products not in the viewport. Uses Intersection Observer.
```

### Bad Messages (and Why)

| Message | Problem |
|---------|---------|
| `update code` | Says nothing about what or why |
| `fix bug` | Which bug? What was wrong? |
| `changes` | Not a commit message |
| `WIP` | Don't commit work in progress (stash instead) |
| `feat: add stuff` | What stuff? Be specific. |
| `fix: fix the thing` | Circular — describes nothing |
| `refactor` | Missing scope and description |
| `address PR feedback` | What feedback? What changed? |

## Co-Author Attribution

For pair programming or mob sessions:

```
feat(auth): add two-factor authentication

Co-authored-by: Alice Smith <alice@example.com>
Co-authored-by: Bob Jones <bob@example.com>
```

For AI-assisted commits, follow the project's `config.yaml` setting for `git.ai_attribution`. If the setting is false or unset, do NOT add a co-author trailer.

## Commit Atomicity

### One Concern Per Commit

Each commit should contain exactly one logical change:

| Scenario | Approach |
|----------|----------|
| Feature + unrelated fix | Two commits: `feat:` then `fix:` |
| Feature + its tests | One commit (tests are part of the feature) |
| Refactor + behavior change | Two commits: `refactor:` then `feat:`/`fix:` |
| Multiple bug fixes | One commit per fix (unless they share a root cause) |
| Dependency update + code change | Two commits: `chore:` then the code change |

### When to Squash

Consider squashing when:
- Multiple small "fixup" commits that should be one logical change
- WIP commits on a feature branch before merging
- The branch has a clean logical sequence but messy intermediate commits

Don't squash across concern boundaries — keep the logical separation.
