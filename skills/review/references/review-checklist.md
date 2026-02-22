# Review Checklist

Comprehensive review checklist organized by domain. Use during Step 4 (Review Each File) to ensure consistent, thorough coverage. Not every item applies to every review — focus on what's relevant to the changed code.

## Correctness

| Check | What to Look For |
|-------|-----------------|
| **Off-by-one errors** | Loop bounds, array indexing, pagination (page 1 vs page 0), range endpoints (inclusive vs exclusive) |
| **Null/undefined handling** | Optional chaining where needed, nullish coalescing, missing checks on function returns |
| **Error handling** | Try/catch covers failure points, errors are actionable (not swallowed), error types are correct |
| **Race conditions** | Concurrent access to shared state, check-then-act without locks, double-submit scenarios |
| **Async correctness** | Missing `await`, unhandled promise rejections, parallel vs sequential when order matters |
| **Type coercion** | `==` vs `===`, string/number confusion, truthy/falsy gotchas (`0`, `""`, `null`) |
| **Boundary conditions** | Empty arrays, empty strings, zero values, max integer, negative numbers, Unicode |
| **State management** | Stale closures in React, mutation of objects passed by reference, missing cleanup in effects |

## Security

Use this in addition to the structured security check in the main SKILL.md.

| Check | What to Look For |
|-------|-----------------|
| **Injection** | User input in SQL, shell commands, templates, regexes, eval |
| **XSS** | `innerHTML`, `dangerouslySetInnerHTML`, `v-html` with user data |
| **Auth bypass** | Missing auth checks on new endpoints, broken object-level authorization (IDOR) |
| **Secrets** | API keys, tokens, passwords in source (not env vars or config) |
| **Input validation** | Missing Zod/validation at API boundaries, trusting client-sent data |
| **SSRF** | User-controlled URLs in server-side fetch calls |
| **Open redirect** | `res.redirect(req.query.url)` without validation |
| **Mass assignment** | `...req.body` spread into database updates without field selection |

## Performance

| Check | What to Look For |
|-------|-----------------|
| **N+1 queries** | Database query inside a loop (should use batch/include) |
| **Missing pagination** | `findMany()` without `take`/`limit` — unbounded result sets |
| **Memory leaks** | Event listeners not cleaned up, closures capturing large objects, growing caches without eviction |
| **Blocking I/O** | Synchronous file reads, `await` in loops that could be `Promise.all` |
| **Expensive operations in hot paths** | Regex compilation in loops, repeated JSON parse/stringify, unnecessary deep clones |
| **Missing indexes** | New queries without corresponding database indexes |
| **Bundle impact** | Large imports that could be tree-shaken or lazy-loaded |

## Testing

| Check | What to Look For |
|-------|-----------------|
| **Coverage gaps** | New code paths without tests, untested error branches, missing edge cases |
| **Test quality** | Tests assert behavior (not implementation), meaningful names, one concept per test |
| **Determinism** | Tests depend on time (`Date.now()`), random values, network, or test execution order |
| **Flakiness risk** | Fixed timeouts instead of condition waits, shared mutable state between tests |
| **Missing regression** | Bug fixes without a test that would catch the bug recurring |
| **Test/prod parity** | Mocks that don't match real API contracts, test-only code paths in production |

## Maintainability

| Check | What to Look For |
|-------|-----------------|
| **Naming clarity** | Variables/functions that don't describe what they hold/do, abbreviations, single letters |
| **Single responsibility** | Functions >50 lines, files >300 lines, components with mixed concerns |
| **Magic numbers/strings** | Unexplained literals (prefer named constants) |
| **Duplication** | Same logic in 3+ places (extract a shared function), copy-pasted code with subtle differences |
| **Dead code** | Unused imports, unreachable branches, commented-out code, unused parameters |
| **API consistency** | New functions that don't follow existing naming/parameter conventions |
| **Error messages** | Generic errors ("Something went wrong") vs actionable errors ("User ID required") |

## TypeScript-Specific

| Check | What to Look For |
|-------|-----------------|
| **`any` usage** | Unnecessary `any` types (prefer `unknown` for truly unknown, or specific types) |
| **Type assertions** | `as` casts that bypass type checking (prefer type guards or narrowing) |
| **Non-null assertions** | `!` postfix — hides potential null at runtime |
| **Optional properties** | Missing handling for optional fields (`user.address?.city`) |
| **Enum vs union** | Runtime enums when union types suffice (`type Status = 'active' \| 'inactive'`) |
| **Import types** | Using `import type` for type-only imports |

## React-Specific

| Check | What to Look For |
|-------|-----------------|
| **Missing deps in hooks** | `useEffect`, `useCallback`, `useMemo` with incomplete dependency arrays |
| **Stale closures** | Event handlers capturing old state values |
| **Unnecessary re-renders** | Missing `memo()` on expensive child components, new object/array references in render |
| **Key prop issues** | Using array index as key for dynamic lists, missing keys |
| **Effect cleanup** | Missing cleanup for subscriptions, timers, event listeners |
| **Prop drilling** | Props passed through 3+ levels (consider context or composition) |
| **Conditional hooks** | Hooks called inside conditionals or loops (violates Rules of Hooks) |

## API-Specific

| Check | What to Look For |
|-------|-----------------|
| **Response shape consistency** | All endpoints return same error format, pagination format |
| **Status codes** | Correct HTTP status (201 for created, 404 for not found, 409 for conflict) |
| **Validation** | Request body validated before processing, query params typed |
| **Rate limiting** | Expensive operations without throttling |
| **Idempotency** | POST/PUT operations safe to retry (idempotency key for payments, deduplication) |
| **Versioning** | Breaking changes to existing endpoints (should use new version) |

## See Also

- [Security Checklists](../../security-review/references/security-checklists.md) — Full OWASP Top 10 and API Security Top 10 checklists for deeper security review
- [WCAG Checklist](../../accessibility-review/references/wcag-checklist.md) — Full WCAG 2.1 AA checklist for accessibility review of UI code
