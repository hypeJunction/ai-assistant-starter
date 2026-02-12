---
name: security-guidelines
description: Application security guidelines covering input validation, XSS prevention, SQL injection, authentication, and secrets management. Auto-loaded when implementing authentication, handling user input, or managing secrets.
user-invocable: false
---

# Security Guidelines

## Core Principles

1. **Defense in depth** — Multiple layers of security
2. **Least privilege** — Minimum permissions required
3. **Fail secure** — Default to denying access
4. **Never trust input** — Validate everything from external sources
5. **Keep secrets secret** — Never expose sensitive data

## Input Validation

Always validate external input (URL params, request body, query strings, headers, file uploads, WebSocket messages).

```typescript
import { z } from 'zod';

const UserInputSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100),
  age: z.number().int().min(0).max(150).optional(),
});

function validateUserInput(input: unknown) {
  return UserInputSchema.parse(input);
}

// Validate IDs (prevent injection)
function validateId(id: string): string {
  if (!/^[a-zA-Z0-9-_]+$/.test(id)) {
    throw new ValidationError('Invalid ID format');
  }
  return id;
}
```

## XSS Prevention

```typescript
// Bad
element.innerHTML = userInput;

// Good - use text content
element.textContent = userInput;

// Good - frameworks escape by default
<div>{userInput}</div>      // React
<div>{{ userInput }}</div>   // Vue

// When HTML is required, sanitize first
import DOMPurify from 'dompurify';
const sanitized = DOMPurify.sanitize(userHtml, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
  ALLOWED_ATTR: ['href', 'target'],
});
```

## SQL Injection Prevention

```typescript
// Bad
const query = `SELECT * FROM users WHERE id = '${userId}'`;

// Good - parameterized query
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);

// Good - ORM
const user = await prisma.user.findUnique({ where: { id: userId } });
```

## Authentication

- Hash passwords with bcrypt (12+ rounds)
- Use short-lived JWT access tokens (15min) + longer refresh tokens (7d)
- Set cookies: `httpOnly: true`, `secure: true`, `sameSite: 'lax'`
- Implement rate limiting on auth endpoints

## Secrets Management

```typescript
// Bad
const API_KEY = 'sk_live_abc123xyz';

// Good - fail if missing
const API_KEY = process.env.API_KEY;
if (!API_KEY) throw new Error('API_KEY required');
```

Never commit: `.env`, `*.key`, `*.pem`, `credentials.json`, `secrets/`

## Security Headers

Use `helmet` or set manually:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Common Gotchas

- **Open redirect**: Always validate redirect URLs against whitelist
- **Timing attacks**: Use `crypto.timingSafeEqual` for secret comparison
- **Prototype pollution**: Check for `__proto__`, `constructor`, `prototype` keys
- **Information disclosure**: Never expose stack traces in production errors
