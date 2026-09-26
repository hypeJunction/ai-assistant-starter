Worked example of a fully filled-in todo entry using the canonical template from `SKILL.md` and the `NNN-{name}.md` naming convention (e.g., `001-refactor-api-client.md`).

## Example Todo

```markdown
---
title: Refactor API Client to Use Interceptors
priority: P2
estimated_effort: medium
created: 2025-01-15
context: Found during /implement session — auth headers added inline as a shortcut
---

## Description

The current API client handles authentication and error logging inline in each
request method. This duplicates logic across every API call and makes it easy
to forget auth headers on new endpoints. Should be refactored to use axios
interceptors for cleaner separation of concerns.

## Affected Files

- `src/services/api/client.ts` — add interceptor configuration
- `src/services/api/auth.ts` — move auth logic to request interceptor
- `src/services/api/*.ts` — remove inline auth handling from all modules

## Suggested Approach

1. Create a request interceptor that automatically attaches auth headers
2. Create a response interceptor for common error code handling (401, 403, 500)
3. Add a logging interceptor for request/response debugging
4. Remove inline auth/error handling from all API modules
5. Update tests to verify interceptor behavior

## Acceptance Criteria

- [ ] Request interceptor adds auth headers automatically
- [ ] Response interceptor handles common error codes
- [ ] Logging interceptor captures request/response for debugging
- [ ] All API modules cleaned up from inline handling
- [ ] Tests updated for new pattern
```
