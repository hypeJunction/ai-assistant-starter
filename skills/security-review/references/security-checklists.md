# Security Checklists

## OWASP Checklist

### 1. Injection
- [ ] SQL queries use parameterized statements or ORM
- [ ] NoSQL queries don't concatenate user input
- [ ] OS commands don't include user input (or use allowlists)
- [ ] Template engines escape by default
- [ ] LDAP queries use proper escaping

### 2. Cross-Site Scripting (XSS)
- [ ] User input is escaped before rendering in HTML
- [ ] No `dangerouslySetInnerHTML`, `v-html`, or `innerHTML` with user data
- [ ] CSP headers are set
- [ ] URL parameters aren't reflected into page without escaping

### 3. Broken Authentication
- [ ] Passwords hashed with bcrypt/scrypt/argon2 (not MD5/SHA)
- [ ] Rate limiting on login endpoints
- [ ] Account lockout after failed attempts
- [ ] Secure session configuration (httpOnly, secure, sameSite)
- [ ] Token expiry is enforced

### 4. Broken Access Control (IDOR)
- [ ] Object references validated against current user
- [ ] Direct database IDs not exposed in URLs without authorization checks
- [ ] Role checks present before data access
- [ ] API endpoints verify permissions, not just authentication

### 5. CSRF
- [ ] State-changing requests require CSRF tokens
- [ ] SameSite cookie attribute is set
- [ ] Custom headers required for API calls (e.g., X-Requested-With)

### 6. Race Conditions
- [ ] Financial operations use database locks or transactions
- [ ] Unique constraints at DB level for things that must be unique
- [ ] Check-then-act patterns use atomic operations
- [ ] File operations handle concurrent access

### 7. Session Management
- [ ] Session IDs regenerated after login
- [ ] Sessions expire after inactivity
- [ ] Logout invalidates server-side session
- [ ] Cookies marked httpOnly, secure, sameSite

### 8. Cryptographic Failures
- [ ] No hardcoded secrets or API keys
- [ ] Strong algorithms used (AES-256, RSA-2048+, SHA-256+)
- [ ] Random values use cryptographically secure generators
- [ ] Secrets compared with timing-safe equality

### 9. Information Disclosure
- [ ] Production errors don't expose stack traces
- [ ] API responses don't leak internal structure
- [ ] Debug endpoints disabled in production
- [ ] HTTP headers don't reveal server versions

### 10. Denial of Service
- [ ] No ReDoS-vulnerable regex patterns
- [ ] Database queries have limits/pagination
- [ ] File upload size limits enforced
- [ ] Request body size limits set
- [ ] No unbounded loops based on user input

### 11. Business Logic
- [ ] Price/quantity can't be set to negative values
- [ ] Workflow steps can't be skipped
- [ ] Rate limits on expensive operations
- [ ] Referral/discount codes validated server-side

## Framework-Mitigated Patterns

These are generally safe due to framework defaults. Don't flag unless the unsafe escape hatch is used.

### React / JSX
- **Safe:** `<div>{userInput}</div>` — React escapes by default
- **Unsafe:** `dangerouslySetInnerHTML={{__html: userInput}}` — bypasses escaping
- **Unsafe:** `href={userInput}` — can be `javascript:` URL

### Prisma / ORMs
- **Safe:** `prisma.user.findMany({ where: { id } })` — parameterized
- **Unsafe:** `prisma.$queryRaw(\`SELECT * FROM users WHERE id = '${id}'\`)` — raw SQL with interpolation
- **Safe:** `prisma.$queryRaw(Prisma.sql\`SELECT * FROM users WHERE id = ${id}\`)` — tagged template

### Next.js
- **Safe:** Server components render on server, no client XSS vector
- **Safe:** API routes with built-in CSRF protection (same-origin)
- **Unsafe:** `getServerSideProps` returning unsanitized user input in props
- **Unsafe:** Middleware that doesn't validate redirect URLs

### Express + Helmet
- **Safe:** `app.use(helmet())` sets security headers
- **Unsafe:** Overriding helmet defaults to disable protections
- **Unsafe:** Missing `express.json({ limit: '1mb' })` — no body size limit

## Server-Controlled vs Attacker-Controlled

Use this decision tree to classify data flows:

**Attacker-controlled (review carefully):**
- URL parameters and query strings
- Request body (forms, JSON)
- HTTP headers (except server-set ones)
- File uploads
- WebSocket messages from client
- Cookie values (user can modify)

**Server-controlled (lower risk):**
- Environment variables
- Database values from server-initiated queries
- Config files
- Server-generated session data
- Values from trusted internal services

**Gray area (verify):**
- Database values originally from user input (stored XSS vector)
- Third-party API responses (supply chain risk)
- Values from authenticated users (trust level depends on authorization)

## Common False Positives

Don't report these — they waste reviewer time:

1. **Test files using hardcoded credentials** — Test fixtures with `password: "test123"` are not secrets
2. **Environment variable references without values** — `process.env.API_KEY` is not a hardcoded secret
3. **ORM/framework queries** — Standard ORM usage is parameterized by default
4. **React JSX expressions** — `{variable}` is auto-escaped
5. **Internal-only admin endpoints** behind authentication — Lower risk tier, not zero risk
6. **Type-only imports** — TypeScript types don't execute
7. **Constants named SECRET/KEY/PASSWORD** — Check if they hold actual secrets or are config keys
