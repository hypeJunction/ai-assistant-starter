# Root Cause Tracing

Methodology for tracing from an observed symptom backward through the call stack to the original source of the bug. The goal is to fix at the source, not at the symptom.

## The Backward Trace

Most bugs are discovered at the symptom level — a crash, wrong output, or failed assertion. The root cause is almost never at the symptom. Trace backward:

```
Symptom (what you see)
  ← Immediate cause (what directly produced the symptom)
    ← Upstream cause (what set up the conditions)
      ← Root cause (the original mistake — fix HERE)
```

### Example: "TypeError: Cannot read property 'name' of undefined"

```
Symptom: TypeError at UserProfile.tsx:15 — user.name
  ← Immediate cause: `user` is undefined when component renders
    ← Upstream cause: useQuery returns undefined before data loads
      ← Root cause: Component doesn't handle loading state

Fix at root cause: Add loading guard, not a null check at line 15
```

**Wrong fix:** `user?.name` at line 15 (hides the problem, renders empty)
**Right fix:** Show loading state while `useQuery` is pending

### Example: "Test passes locally, fails in CI"

```
Symptom: Test assertion fails in CI
  ← Immediate cause: Database query returns different results
    ← Upstream cause: Test data wasn't seeded (CI starts with empty DB)
      ← Root cause: Test relies on data from another test (test pollution)

Fix at root cause: Make test self-contained with its own setup/teardown
```

## The Five Whys (Adapted for Code)

Ask "why?" at each level until you reach something you can fix permanently:

1. **Why** did the API return 500? → The database query threw an error
2. **Why** did the query throw? → It received `null` for the `userId` parameter
3. **Why** was `userId` null? → The JWT token didn't contain a `userId` claim
4. **Why** didn't the token have `userId`? → The token was created by an old login flow that uses `sub` instead
5. **Why** wasn't this caught? → The token validation doesn't check for required claims

**Root cause:** Token validation doesn't enforce required claims
**Fix:** Add claim validation to `validateToken()`, not null checks in every consumer

### When to Stop Asking "Why?"

Stop when you reach one of:
- A code change you can make that prevents the entire chain
- An external system boundary (third-party API, OS, hardware)
- A design decision that needs to be revisited (escalate to user)

## Multi-Component Evidence Gathering

Before proposing any fix, instrument the system at each component boundary to build a clear picture.

### The Instrumentation Pattern

```
Request → [Component A] → [Component B] → [Component C] → Response
              ↓                 ↓                 ↓
           Log input          Log input         Log input
           Log output         Log output        Log output
```

Add temporary logging at each boundary to answer:
- What data entered this component?
- What data left this component?
- Where did the data change unexpectedly?

### Example: Debugging a data transformation pipeline

```typescript
// Temporary instrumentation — REMOVE after debugging
function processOrder(input: OrderInput): ProcessedOrder {
  console.log('[DEBUG processOrder] input:', JSON.stringify(input));

  const validated = validateOrder(input);
  console.log('[DEBUG processOrder] after validate:', JSON.stringify(validated));

  const enriched = enrichWithPricing(validated);
  console.log('[DEBUG processOrder] after enrich:', JSON.stringify(enriched));

  const result = calculateTotals(enriched);
  console.log('[DEBUG processOrder] result:', JSON.stringify(result));

  return result;
}
```

This reveals exactly which step corrupts the data — without guessing.

### Instrumentation Rules

1. **Add logging BEFORE forming hypotheses** — Let data guide your thinking
2. **Log at every component boundary** — Don't skip "obvious" ones
3. **Log both input and output** — The bug is where they don't match expectations
4. **Use structured data** — `JSON.stringify` over `console.log(obj)` (avoids `[Object]`)
5. **Remove all instrumentation after debugging** — Temporary logging is not production logging

## Stack Trace Reading

### JavaScript/TypeScript Stack Traces

Read bottom-up for the call chain, top-down for the error location:

```
TypeError: Cannot read properties of undefined (reading 'id')
    at getUserId (src/lib/auth.ts:42:15)           ← Error location
    at handleRequest (src/routes/api.ts:18:10)      ← Called from
    at Layer.handle (node_modules/express/lib/router/layer.js:95:5)  ← Framework
    at next (node_modules/express/lib/router/route.js:144:13)        ← Framework
```

**Focus on:** Lines in YOUR code (not node_modules). The top line is where the error manifested, but trace down through your code to find what passed the bad data.

### Async Stack Traces

Async boundaries break stack traces. If the trace is incomplete:

```typescript
// Enable long stack traces for debugging
Error.stackTraceLimit = 50;

// Or use --async-stack-traces flag in Node.js
// node --async-stack-traces app.js
```

## When the Root Cause Is Unclear

If backward tracing doesn't converge on a single root cause:

1. **Multiple possible causes** → Design experiments to eliminate each one. Change ONE variable at a time.
2. **Intermittent bug** → The root cause likely involves shared mutable state, timing, or external dependencies. See `debugging-techniques.md` for race condition analysis.
3. **Bug disappears when adding logging** → Heisenbug — the observation changes the behavior. Common with timing issues. Use non-invasive techniques (breakpoints, snapshots).
4. **Three failed traces** → Escalate. The bug may be a design problem, not a code problem. Present findings to user and suggest architectural review.
