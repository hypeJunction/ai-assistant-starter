---
name: error-handling-guidelines
description: Error handling guidelines for TypeScript including custom error classes, try-catch patterns, error boundaries, API error handling, and recovery patterns. Auto-loaded when working with error handling code.
user-invocable: false
---

# Error Handling Guidelines

## Core Principles

1. **Fail fast** - Detect errors early, don't let them propagate silently
2. **Fail gracefully** - Provide meaningful feedback, don't crash unnecessarily
3. **Be specific** - Use typed errors with clear messages
4. **Don't swallow errors** - Always log or handle, never ignore
5. **User-friendly messages** - Technical details for logs, human messages for users

## Error Types

### Custom Error Classes

```typescript
// Base application error
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    public readonly isOperational: boolean = true
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

// Specific error types
export class ValidationError extends AppError {
  constructor(
    message: string,
    public readonly fields: Array<{ field: string; message: string }>
  ) {
    super(message, 'VALIDATION_ERROR', 400);
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} with id '${id}' not found`, 'NOT_FOUND', 404);
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Authentication required') {
    super(message, 'UNAUTHORIZED', 401);
  }
}

export class ForbiddenError extends AppError {
  constructor(message = 'Access denied') {
    super(message, 'FORBIDDEN', 403);
  }
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super(message, 'CONFLICT', 409);
  }
}

export class RateLimitError extends AppError {
  constructor(public readonly retryAfter: number) {
    super('Rate limit exceeded', 'RATE_LIMIT', 429);
  }
}
```

### Error Code Catalog

```typescript
// Centralized error codes
export const ErrorCodes = {
  // Validation
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INVALID_INPUT: 'INVALID_INPUT',
  MISSING_FIELD: 'MISSING_FIELD',

  // Authentication
  UNAUTHORIZED: 'UNAUTHORIZED',
  INVALID_TOKEN: 'INVALID_TOKEN',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',

  // Authorization
  FORBIDDEN: 'FORBIDDEN',
  INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',

  // Resources
  NOT_FOUND: 'NOT_FOUND',
  CONFLICT: 'CONFLICT',
  ALREADY_EXISTS: 'ALREADY_EXISTS',

  // External
  EXTERNAL_SERVICE_ERROR: 'EXTERNAL_SERVICE_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT',

  // Internal
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  DATABASE_ERROR: 'DATABASE_ERROR',
} as const;
```

## Try-Catch Patterns

### Basic Pattern

```typescript
// Always type error as unknown
try {
  await riskyOperation();
} catch (error: unknown) {
  if (error instanceof AppError) {
    // Known application error - handle specifically
    logger.warn('Operation failed', { code: error.code, message: error.message });
    throw error;
  }

  if (error instanceof Error) {
    // Unknown error - wrap it
    logger.error('Unexpected error', { error: error.message, stack: error.stack });
    throw new AppError('An unexpected error occurred', 'INTERNAL_ERROR', 500, false);
  }

  // Non-Error thrown (rare)
  logger.error('Unknown error type', { error });
  throw new AppError('An unexpected error occurred', 'INTERNAL_ERROR', 500, false);
}
```

### Never Swallow Errors

```typescript
// Bad - error is silently swallowed
try {
  await saveData();
} catch (error) {
  // Nothing happens - bug goes unnoticed
}

// Bad - generic catch with no logging
try {
  await saveData();
} catch {
  return null;
}

// Good - always log or rethrow
try {
  await saveData();
} catch (error) {
  logger.error('Failed to save data', { error });
  throw error;
}

// Good - handle with fallback AND log
try {
  return await fetchFromCache();
} catch (error) {
  logger.warn('Cache miss, fetching from source', { error });
  return await fetchFromSource();
}
```

### Async Error Handling

```typescript
// Promise chains
fetchData()
  .then(processData)
  .then(saveData)
  .catch(error => {
    logger.error('Pipeline failed', { error });
    throw error;
  });

// Async/await (preferred)
async function pipeline() {
  try {
    const data = await fetchData();
    const processed = await processData(data);
    return await saveData(processed);
  } catch (error) {
    logger.error('Pipeline failed', { error });
    throw error;
  }
}

// Promise.all - one failure fails all
try {
  const [users, orders] = await Promise.all([
    fetchUsers(),
    fetchOrders(),
  ]);
} catch (error) {
  // Any failure ends up here
}

// Promise.allSettled - handle partial success
const results = await Promise.allSettled([
  fetchUsers(),
  fetchOrders(),
]);

results.forEach((result, index) => {
  if (result.status === 'rejected') {
    logger.error(`Operation ${index} failed`, { error: result.reason });
  }
});
```

## Known Gotchas

### Error Type in Catch

```typescript
// TypeScript catch clause variable is `unknown`
try {
  await operation();
} catch (error) {
  // error is unknown - must narrow
  if (error instanceof Error) {
    console.log(error.message);
  }
}
```

### Async Errors in Callbacks

```typescript
// Bad - unhandled promise rejection
array.forEach(async item => {
  await processItem(item); // Error won't be caught
});

// Good - use Promise.all or for...of
await Promise.all(array.map(async item => {
  await processItem(item);
}));

// Or sequential with for...of
for (const item of array) {
  await processItem(item);
}
```

### Error Stack Traces

```typescript
// Preserve stack trace when wrapping errors
try {
  await operation();
} catch (error) {
  const wrappedError = new AppError('Wrapped error', 'WRAPPED');
  if (error instanceof Error) {
    wrappedError.cause = error; // ES2022+
  }
  throw wrappedError;
}
```

### Unhandled Promise Rejections

```typescript
// Global handler for unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled promise rejection', { reason });
  // In production, you might want to exit gracefully
});

// Browser
window.addEventListener('unhandledrejection', event => {
  logger.error('Unhandled promise rejection', { reason: event.reason });
});
```

## Additional References

- [Error Boundaries (React & Vue)](references/error-boundaries.md)
- [API Error Handling & User-Facing Messages](references/api-error-handling.md)
- [Recovery Patterns (Retry & Circuit Breaker)](references/recovery-patterns.md)
