Worked example of a fully filled-in todo entry.

## Example Todo

```markdown
---
id: refactor-api-client
title: Refactor API Client to Use Interceptors
priority: medium
category: refactor
status: open
created: 2025-01-15
updated: 2025-01-15
labels: [api, architecture]
---

# Refactor API Client to Use Interceptors

## Description

The current API client handles authentication and error logging inline in each request. This should be refactored to use axios interceptors for cleaner separation of concerns.

## Context

| Aspect | Details |
|--------|---------|
| **Shortcut Taken** | Added auth headers directly in each API call |
| **Reason** | Needed to ship feature quickly, interceptor setup was out of scope |
| **Proper Solution** | Create request/response interceptors for auth, logging, and error handling |

## Affected Files

| File | Changes Needed |
|------|----------------|
| `src/services/api/client.ts` | Add interceptor configuration |
| `src/services/api/auth.ts` | Move auth logic to interceptor |
| `src/services/api/*.ts` | Remove inline auth handling |

## Acceptance Criteria

- [ ] Request interceptor adds auth headers automatically
- [ ] Response interceptor handles common error codes
- [ ] Logging interceptor captures request/response for debugging
- [ ] All API modules cleaned up from inline handling
- [ ] Tests updated for new pattern

## Subtasks

- [ ] `create-interceptors`: Create base interceptor configuration
- [ ] `migrate-auth`: Move auth logic to request interceptor
- [ ] `migrate-errors`: Add response interceptor for error handling
- [ ] `cleanup-modules`: Remove inline handling from API modules
```
