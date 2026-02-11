Memory management and profiling techniques for preventing leaks, handling large data, and measuring performance.

## Memory Management

### Avoid Memory Leaks

```typescript
// React: Clean up subscriptions
useEffect(() => {
  const subscription = eventEmitter.subscribe(handleEvent);

  return () => {
    subscription.unsubscribe();
  };
}, []);

// Clear intervals/timeouts
useEffect(() => {
  const interval = setInterval(poll, 1000);
  return () => clearInterval(interval);
}, []);

// Remove event listeners
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```

### Stream Large Data

```typescript
// Don't load entire file into memory
// Bad
const content = fs.readFileSync('large-file.json', 'utf-8');
const data = JSON.parse(content);

// Good - stream processing
import { createReadStream } from 'fs';
import { pipeline } from 'stream/promises';
import JSONStream from 'jsonstream';

await pipeline(
  createReadStream('large-file.json'),
  JSONStream.parse('items.*'),
  async function* (source) {
    for await (const item of source) {
      yield processItem(item);
    }
  }
);
```

## Profiling

### Frontend Profiling

```typescript
// Performance marks
performance.mark('operation-start');
await heavyOperation();
performance.mark('operation-end');

performance.measure('heavy-operation', 'operation-start', 'operation-end');

const measures = performance.getEntriesByName('heavy-operation');
console.log(`Operation took ${measures[0].duration}ms`);

// Web Vitals
import { getCLS, getFID, getLCP } from 'web-vitals';

getCLS(console.log);  // Cumulative Layout Shift
getFID(console.log);  // First Input Delay
getLCP(console.log);  // Largest Contentful Paint
```

### Backend Profiling

```typescript
// Simple timing
const start = performance.now();
await operation();
const duration = performance.now() - start;
logger.info('Operation completed', { duration: `${duration.toFixed(2)}ms` });

// Wrap functions for timing
function timed<T>(name: string, fn: () => Promise<T>): Promise<T> {
  const start = performance.now();
  return fn().finally(() => {
    const duration = performance.now() - start;
    if (duration > 100) {
      logger.warn('Slow operation', { name, duration: `${duration.toFixed(2)}ms` });
    }
  });
}

// Database query logging
prisma.$use(async (params, next) => {
  const start = performance.now();
  const result = await next(params);
  const duration = performance.now() - start;

  if (duration > 50) {
    logger.warn('Slow query', {
      model: params.model,
      action: params.action,
      duration: `${duration.toFixed(2)}ms`,
    });
  }

  return result;
});
```
