---
name: logging-guidelines
description: Logging guidelines for TypeScript including structured logging, log levels, request logging, correlation IDs, and performance logging. Auto-loaded when working with logging code.
user-invocable: false
---

# Logging Guidelines

## Core Principles

1. **Structured logging** - Use JSON format for machine parseability
2. **Appropriate levels** - Use correct severity for each message
3. **Contextual information** - Include relevant data for debugging
4. **No sensitive data** - Never log passwords, tokens, or PII
5. **Consistent format** - Same structure across the application

## Log Level Hierarchy

| Level | When to Use |
|-------|-------------|
| `error` | Application errors requiring immediate attention |
| `warn` | Unexpected but handled situations |
| `info` | Significant business events |
| `debug` | Detailed debugging information |
| `trace` | Very detailed tracing (rarely used) |

### Level Selection Guide

```typescript
// ERROR - Something is broken, needs investigation
logger.error('Database connection failed', { error, retries: 3 });
logger.error('Payment processing failed', { orderId, error });

// WARN - Something unexpected but handled
logger.warn('Cache miss, fetching from database', { key });
logger.warn('Rate limit approaching', { current: 95, limit: 100 });
logger.warn('Deprecated API endpoint accessed', { endpoint, client });

// INFO - Business-significant events
logger.info('User registered', { userId, email });
logger.info('Order completed', { orderId, total, items: items.length });
logger.info('Application started', { port, environment });

// DEBUG - Development/troubleshooting details
logger.debug('Request received', { method, path, query });
logger.debug('Cache hit', { key, ttl });
logger.debug('Query executed', { sql, duration: '45ms' });

// TRACE - Extremely verbose (usually disabled)
logger.trace('Entering function', { fn: 'processItem', args });
```

## What to Log

### Do Log

```typescript
// Application lifecycle
logger.info('Application starting', { version, nodeVersion: process.version });
logger.info('Application ready', { port, healthCheck: '/health' });
logger.info('Application shutting down', { reason: 'SIGTERM' });

// Business events
logger.info('User action', { action: 'login', userId, method: 'oauth' });
logger.info('Transaction completed', { transactionId, amount, currency });
logger.info('Resource created', { resourceType: 'order', resourceId });

// Errors and failures
logger.error('Operation failed', { operation: 'payment', error: error.message, orderId });
logger.warn('External service degraded', { service: 'stripe', latency: '5000ms' });

// Performance metrics
logger.info('Request completed', { path, method, statusCode, duration: '150ms' });
logger.warn('Slow query detected', { query: 'findUsers', duration: '2500ms' });
```

### Don't Log

```typescript
// NEVER log these:
logger.info('User login', { password });           // Passwords
logger.debug('API call', { apiKey });              // API keys/tokens
logger.info('Payment', { creditCard });            // Financial data
logger.debug('Request', { authorization: token }); // Auth tokens
logger.info('User', { ssn, dateOfBirth });         // PII

// Mask sensitive data if needed for debugging
function maskEmail(email: string): string {
  const [local, domain] = email.split('@');
  return `${local[0]}***@${domain}`;
}

function maskCard(card: string): string {
  return `****${card.slice(-4)}`;
}

logger.info('User registered', { email: maskEmail(email) });
```

## console.log Prohibition

```typescript
// Bad - loses structure, hard to filter
console.log('User logged in:', userId);
console.error('Error:', error);

// Good - structured, filterable
logger.info('User logged in', { userId });
logger.error('Operation failed', { error: error.message });
```

### ESLint Rule

```json
{
  "rules": {
    "no-console": "error"
  }
}
```

## Structured Logging Example

```typescript
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
    bindings: () => ({}),
  },
  timestamp: () => `,"timestamp":"${new Date().toISOString()}"`,
  base: {
    service: process.env.SERVICE_NAME || 'app',
    environment: process.env.NODE_ENV || 'development',
  },
});

export function createLogger(context: string) {
  return logger.child({ context });
}
```

## References

- `references/logger-setup.md` - Full logger configuration, child loggers, error logging, error aggregation
- `references/request-logging.md` - HTTP request middleware, correlation IDs with AsyncLocalStorage
- `references/performance-logging.md` - Timing utilities, metrics logging patterns
- `references/log-infrastructure.md` - Log rotation, dev/prod transports, sampling strategies
- `references/logging-gotchas.md` - Circular references, large objects, async context loss, production levels
