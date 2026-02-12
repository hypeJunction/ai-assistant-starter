# Performance Logging

## Timing Operations

```typescript
async function timedOperation<T>(
  name: string,
  fn: () => Promise<T>
): Promise<T> {
  const start = Date.now();
  try {
    const result = await fn();
    const duration = Date.now() - start;

    if (duration > 1000) {
      logger.warn('Slow operation', { operation: name, duration: `${duration}ms` });
    } else {
      logger.debug('Operation completed', { operation: name, duration: `${duration}ms` });
    }

    return result;
  } catch (error) {
    const duration = Date.now() - start;
    logger.error('Operation failed', { operation: name, duration: `${duration}ms`, error });
    throw error;
  }
}

// Usage
const users = await timedOperation('fetchUsers', () => db.users.findMany());
```

## Metrics Logging

```typescript
// Log metrics for monitoring
logger.info('metrics', {
  type: 'gauge',
  metric: 'active_connections',
  value: connectionPool.activeCount,
});

logger.info('metrics', {
  type: 'histogram',
  metric: 'request_duration',
  value: duration,
  labels: { endpoint: '/api/users', method: 'GET' },
});
```
