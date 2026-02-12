# Request Logging & Correlation IDs

## HTTP Request Logger Middleware

```typescript
import { v4 as uuidv4 } from 'uuid';

function requestLogger(req: Request, res: Response, next: NextFunction) {
  const requestId = req.headers['x-request-id'] as string || uuidv4();
  const startTime = Date.now();

  // Add request ID to response headers
  res.setHeader('x-request-id', requestId);

  // Log request start
  logger.info('Request started', {
    requestId,
    method: req.method,
    path: req.path,
    query: req.query,
    userAgent: req.headers['user-agent'],
    ip: req.ip,
  });

  // Log response
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const logFn = res.statusCode >= 400 ? logger.warn : logger.info;

    logFn.call(logger, 'Request completed', {
      requestId,
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      contentLength: res.getHeader('content-length'),
    });
  });

  next();
}
```

## Correlation IDs with AsyncLocalStorage

```typescript
import { AsyncLocalStorage } from 'async_hooks';

const asyncLocalStorage = new AsyncLocalStorage<{ requestId: string }>();

// Middleware to set context
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] as string || uuidv4();
  asyncLocalStorage.run({ requestId }, () => next());
});

// Logger that automatically includes correlation ID
function getLogger() {
  const store = asyncLocalStorage.getStore();
  return logger.child({ requestId: store?.requestId });
}

// Usage anywhere in the call stack
async function processOrder(orderId: string) {
  const log = getLogger();
  log.info('Processing order', { orderId });
  // requestId automatically included
}
```
