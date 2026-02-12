# Logging Gotchas

## Circular References

```typescript
// Bad - causes JSON.stringify to fail
const obj = { a: 1 };
obj.self = obj;
logger.info('Data', obj);  // Error!

// Good - use safe serialization
import { serialize } from 'safe-stable-stringify';

function safeLog(data: unknown) {
  try {
    return JSON.parse(serialize(data));
  } catch {
    return '[Unserializable]';
  }
}
```

## Large Objects

```typescript
// Bad - logs entire large object
logger.debug('Response', { data: hugeArray });

// Good - log summary
logger.debug('Response', {
  dataCount: hugeArray.length,
  sampleIds: hugeArray.slice(0, 5).map(d => d.id),
});
```

## Async Context Loss

```typescript
// Bad - loses request context
setTimeout(() => {
  logger.info('Delayed operation');  // No requestId
}, 1000);

// Good - preserve context
const requestId = getCurrentRequestId();
setTimeout(() => {
  logger.info('Delayed operation', { requestId });
}, 1000);
```

## Log Level in Production

```typescript
// Don't log debug in production by default
const logger = pino({
  level: process.env.LOG_LEVEL ||
    (process.env.NODE_ENV === 'production' ? 'info' : 'debug'),
});
```
