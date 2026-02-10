---
name: documentation-guidelines
description: Documentation best practices for code comments, JSDoc, READMEs, and API docs. Explains when to comment and when not to. Auto-loaded when writing documentation.
user-invocable: false
---

# Documentation Guidelines

## Core Principles

1. **Code is primary** — Self-documenting code first, comments second
2. **Explain why, not what** — Comments explain intent, not mechanics
3. **Keep in sync** — Outdated docs are worse than no docs
4. **Minimal but sufficient** — Document what's needed, no more

## When to Comment

```typescript
// Good - explains WHY
// Clamp to [-60, 20] range to prevent speaker damage
const clampedGain = Math.max(-60, Math.min(20, totalGain));

// Good - explains non-obvious behavior
// setTimeout(0) defers to next event loop tick, ensuring DOM updated
setTimeout(() => measureHeight(), 0);

// Good - references external context
// Algorithm from https://en.wikipedia.org/wiki/Exponential_backoff
const delay = baseDelay * Math.pow(2, attempt);
```

## When NOT to Comment

```typescript
// Bad - states the obvious
// Increment counter
counter++;

// Bad - paraphrases code
// Check if user is admin
if (user.role === 'admin') { ... }

// Bad - commented-out code (delete it, use git history)
// function oldImplementation() { ... }
```

## TODO Format

```typescript
// TODO(username): description
// TODO(JIRA-123): Migrate to new API before deprecation
// FIXME: Known bug that needs fixing
// HACK: Temporary workaround
```

## JSDoc

```typescript
/**
 * Calculates total price including tax and discounts.
 *
 * @param items - Cart items with price and quantity
 * @param taxRate - Tax rate as decimal (0.08 for 8%)
 * @param discount - Optional discount in dollars
 * @returns Total price after tax and discount
 * @throws {ValidationError} If items array is empty
 *
 * @example
 * calculateTotal([{ price: 10, quantity: 2 }], 0.08, 5);
 * // Returns: 16.6
 */
```

## Interface Documentation

```typescript
export interface User {
  /** Unique identifier (UUID v4) */
  id: string;
  /** User's display name (1-100 characters) */
  name: string;
  /** Email address (must be unique) */
  email: string;
  /**
   * Last login timestamp, or null if never logged in.
   * Updated on each successful authentication.
   */
  lastLoginAt: string | null;
}
```

## Anti-Patterns

- **Redundant docs**: Don't document `getUser(id)` as "Gets the user"
- **Outdated docs**: Wrong docs are worse than no docs
- **Over-documentation**: Don't explain `add(a, b)` in 10 lines
- **Magic numbers**: Use named constants instead of inline comments
