# Logger Setup & Configuration

## Logger Setup (Pino)

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

// Create child logger with context
export function createLogger(context: string) {
  return logger.child({ context });
}
```

## Log Structure

Every log entry should include:

```typescript
{
  "level": "info",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "service": "api-gateway",
  "environment": "production",
  "context": "user-service",
  "message": "User registered",
  "userId": "user-123",
  "email": "j***@example.com",  // Masked
  "requestId": "req-456"
}
```

## Child Loggers

```typescript
// Create contextual logger for a module
const userLogger = createLogger('user-service');

// Add request context
function requestLogger(req: Request) {
  return logger.child({
    requestId: req.headers['x-request-id'],
    userId: req.user?.id,
    path: req.path,
  });
}

// Usage in request handler
app.get('/users/:id', (req, res) => {
  const log = requestLogger(req);
  log.info('Fetching user');
  // All logs from this request have the same requestId
});
```

## Error Logging

### Logging Errors with Full Context

```typescript
try {
  await riskyOperation();
} catch (error) {
  logger.error('Operation failed', {
    operation: 'riskyOperation',
    error: error instanceof Error ? {
      message: error.message,
      name: error.name,
      stack: error.stack,
    } : error,
    input: { /* relevant input data, sanitized */ },
  });
  throw error;
}

// For known errors, include error code
if (error instanceof AppError) {
  logger.error('Application error', {
    code: error.code,
    message: error.message,
    statusCode: error.statusCode,
    isOperational: error.isOperational,
  });
}
```

### Error Aggregation

```typescript
// Include fields that help aggregate similar errors
logger.error('Database query failed', {
  errorCode: 'DB_CONNECTION_ERROR',
  errorType: error.constructor.name,
  database: 'users',
  operation: 'find',
  // These fields help group similar errors
});
```
