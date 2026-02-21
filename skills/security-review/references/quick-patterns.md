# Quick Patterns Reference

Tiered pattern classification for rapid triage. Use during Phase 3 (Security Scan) to quickly identify what needs deeper analysis vs. what's immediately reportable.

## Always Flag — Critical

These are dangerous in virtually all contexts. Report as HIGH confidence unless you find explicit, intentional usage with documented justification.

| Pattern | Language | Why Critical |
|---------|----------|-------------|
| `eval(userInput)` | JS/TS | Arbitrary code execution |
| `new Function(userInput)` | JS/TS | Arbitrary code execution |
| `child_process.exec(userInput)` | Node.js | OS command injection |
| `exec(user_input)` | Python | Arbitrary code execution |
| `pickle.loads(untrusted)` | Python | Arbitrary code execution via deserialization |
| `yaml.load(untrusted)` | Python | Code execution (use `yaml.safe_load`) |
| `unserialize($untrusted)` | PHP | Object injection / code execution |
| `Runtime.exec(userInput)` | Java | OS command injection |
| `ObjectInputStream.readObject()` | Java | Deserialization attack |
| `Marshal.load(untrusted)` | Ruby | Arbitrary code execution |

## Always Flag — High

These are dangerous when user-controlled data reaches them. Verify the data source before reporting.

| Pattern | Language | Risk |
|---------|----------|------|
| `element.innerHTML = userInput` | JS/TS | Stored/reflected XSS |
| `dangerouslySetInnerHTML={{__html: userInput}}` | React | Bypasses React escaping |
| `v-html="userInput"` | Vue | Bypasses Vue escaping |
| `` `SELECT * FROM x WHERE id = '${userId}'` `` | SQL | SQL injection |
| `prisma.$queryRaw(`...${userInput}...`)` | Prisma | SQL injection via raw query |
| `document.location = userInput` | JS | Open redirect |
| `res.redirect(req.query.url)` | Express | Open redirect |
| `fs.readFile(userInput)` | Node.js | Path traversal |
| `fs.writeFile(userInput, data)` | Node.js | Arbitrary file write |
| `crypto.createHash('md5')` | Node.js | Weak hash for security use |
| `Math.random()` for tokens/secrets | JS | Not cryptographically secure |

## Always Flag — Secrets

Hardcoded credentials in source code. Check that the value is a real secret (not a placeholder, env var reference, or test fixture).

| Pattern | Example |
|---------|---------|
| API keys | `const apiKey = 'sk_live_...'` |
| Private keys | `-----BEGIN RSA PRIVATE KEY-----` |
| Database URLs with credentials | `postgresql://user:password@host/db` |
| AWS credentials | `AKIA...` (20-char uppercase starting with AKIA) |
| JWT secrets | `const JWT_SECRET = 'my-secret-key'` |
| Password strings | `password = "admin123"` (outside test files) |

**Not secrets (don't flag):**
- `process.env.API_KEY` — environment variable reference
- `const API_KEY = ''` or `'placeholder'` — empty/placeholder
- Test files with `password: 'test123'` — test fixtures
- Constants named `PASSWORD_MIN_LENGTH` — config, not a secret

## Check Context First

These patterns may or may not be vulnerable depending on context. Investigate the data source and existing mitigations before flagging.

### SSRF — Server-Side Request Forgery

```typescript
// VULNERABLE: User controls the URL
const response = await fetch(req.body.url);

// SAFE: URL from server config
const response = await fetch(`${config.API_BASE_URL}/endpoint`);

// SAFE: URL constructed from allowlist
const ALLOWED_HOSTS = ['api.example.com', 'cdn.example.com'];
const url = new URL(req.body.url);
if (!ALLOWED_HOSTS.includes(url.hostname)) throw new Error('Blocked');
```

**Check for:** URL allowlists, hostname validation, private IP blocking, DNS rebinding protection.

### Path Traversal

```typescript
// VULNERABLE: User controls the file path
const file = fs.readFileSync(`./uploads/${req.params.filename}`);

// SAFE: Resolved path is validated
const resolved = path.resolve('./uploads', req.params.filename);
if (!resolved.startsWith(path.resolve('./uploads'))) throw new Error('Blocked');

// SAFE: Using a mapping/lookup instead of direct path
const files = { 'avatar': './uploads/avatar.png' };
const file = fs.readFileSync(files[req.params.key]);
```

**Check for:** `path.resolve` + prefix validation, allowlist/mapping approaches, `path.normalize` usage.

### Open Redirect

```typescript
// VULNERABLE: Unvalidated redirect
res.redirect(req.query.returnUrl);

// SAFE: Relative path only
const url = req.query.returnUrl;
if (url.startsWith('/') && !url.startsWith('//')) res.redirect(url);

// SAFE: Allowlisted domains
const allowed = ['example.com', 'app.example.com'];
const url = new URL(req.query.returnUrl);
if (allowed.includes(url.hostname)) res.redirect(url.href);
```

**Check for:** URL validation, relative-path enforcement, domain allowlists, protocol checking.

### Mass Assignment

```typescript
// VULNERABLE: Spreading user input directly
const user = await prisma.user.update({
  where: { id },
  data: req.body,  // User could set { role: 'admin' }
});

// SAFE: Explicit field selection
const { name, email } = req.body;
const user = await prisma.user.update({
  where: { id },
  data: { name, email },
});
```

**Check for:** Explicit field picking, DTO validation with Zod/class-validator, ORM-level field protection.

### Weak Cryptography

```typescript
// CONTEXT-DEPENDENT: MD5/SHA1
crypto.createHash('md5').update(data);  // Bad for passwords, OK for checksums
crypto.createHash('sha1').update(data); // Bad for security, OK for cache keys

// SAFE alternatives for security use
crypto.createHash('sha256').update(data);  // Hashing
await bcrypt.hash(password, 12);            // Passwords
crypto.randomBytes(32);                     // Token generation
```

**Check for:** What the hash is used for (security vs. non-security), whether bcrypt/argon2 is used for passwords.

### Race Conditions

```typescript
// VULNERABLE: Check-then-act without atomicity
const balance = await getBalance(userId);
if (balance >= amount) {
  await deductBalance(userId, amount);  // Another request could deduct between check and act
}

// SAFE: Atomic operation
await prisma.$transaction(async (tx) => {
  const account = await tx.account.findUnique({ where: { userId } });
  if (account.balance < amount) throw new Error('Insufficient funds');
  await tx.account.update({ where: { userId }, data: { balance: { decrement: amount } } });
});
```

**Check for:** Database transactions, optimistic locking, unique constraints, atomic operations.
