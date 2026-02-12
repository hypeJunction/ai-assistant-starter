# Log Infrastructure

## Log Rotation

```typescript
import pino from 'pino';
import { createWriteStream } from 'pino-pretty';

// Development: pretty print
const devStream = createWriteStream({
  colorize: true,
  translateTime: 'HH:MM:ss',
  ignore: 'pid,hostname',
});

// Production: JSON to file with rotation
// Use external tools like logrotate or log shipping
const prodTransport = pino.transport({
  target: 'pino/file',
  options: { destination: '/var/log/app/app.log' },
});

export const logger = pino(
  { level: process.env.LOG_LEVEL || 'info' },
  process.env.NODE_ENV === 'production' ? prodTransport : devStream
);
```

## Log Sampling

```typescript
// For high-volume logs, use sampling
function shouldSample(rate: number): boolean {
  return Math.random() < rate;
}

// Log 10% of debug messages in production
if (shouldSample(0.1)) {
  logger.debug('Detailed operation info', { data });
}

// Always log errors, sample info
if (level === 'error' || shouldSample(0.5)) {
  logger.log(level, message, data);
}
```
