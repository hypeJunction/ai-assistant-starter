# Security Scan Patterns

Grep-based security patterns used during validation. Each pattern includes what it detects, why it matters, severity, and false positive guidance.

## Pattern 1: Secrets Detection

**Severity:** BLOCKER (in non-test, non-example files)

```bash
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" [files]
```

**What it detects:**
- Hardcoded API keys, passwords, tokens, and credentials
- Assignment or declaration of secret-like variable names with literal values

**False positives:**
- Type definitions: `apiKey: string` (no literal value)
- Environment variable references: `apiKey: process.env.API_KEY`
- Test fixtures with dummy values: `password: 'test123'` in `.spec.ts` files
- Configuration keys: `secretKeyRef:` in Kubernetes YAML
- Documentation or comments mentioning secrets

**When to flag:**
- Any literal string value assigned to a secret-like variable in production code
- `.env` files committed to git (check `.gitignore`)
- JSON config files with actual credentials

**When to skip:**
- Test files (`.spec.ts`, `.test.ts`, `__tests__/`)
- Type declarations (`interface`, `type`)
- Environment variable lookups (`process.env.*`)

## Pattern 2: Insecure Code Execution

**Severity:** REVIEW REQUIRED

```bash
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|document\.write\()" [files]
```

**What it detects:**
| Pattern | Risk | OWASP Category |
|---------|------|----------------|
| `eval()` | Arbitrary code execution | A03: Injection |
| `new Function()` | Dynamic code execution | A03: Injection |
| `innerHTML =` | Cross-Site Scripting (XSS) | A07: XSS |
| `dangerouslySetInnerHTML` | XSS in React | A07: XSS |
| `document.write()` | DOM manipulation XSS | A07: XSS |

**False positives:**
- `dangerouslySetInnerHTML` with DOMPurify sanitization: **safe if sanitizer is verified**
- `innerHTML` in test setup code: **safe in test context**
- `eval` in build tools or bundler config: **safe in build-time context**
- Third-party library internals (node_modules): **not your code**

**When to flag:**
- Any `eval()` or `new Function()` with user-controlled input
- `innerHTML` with any dynamic content not sanitized
- `dangerouslySetInnerHTML` without DOMPurify or equivalent

**When to skip:**
- Build-time code (webpack config, bundler plugins)
- Server-side rendering with trusted content
- Test files setting up DOM fixtures

## Pattern 3: SQL Injection

**Severity:** BLOCKER

```bash
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(\\\$queryRaw\`|\\\$executeRaw\`|\.query\(.*\\\$\{|SELECT.*\\\$\{|INSERT.*\\\$\{|UPDATE.*\\\$\{|DELETE.*\\\$\{)" [files]
```

**What it detects:**
- Raw SQL queries with string interpolation (`${variable}` inside SQL)
- Prisma raw queries that may bypass parameterization

**False positives:**
- Prisma tagged template literals: `prisma.$queryRaw\`SELECT * FROM users WHERE id = ${id}\`` — These are **safe** because Prisma auto-parameterizes tagged templates
- Knex query builder: `knex('users').where('id', id)` — Safe (parameterized)
- Template literals used for table/column names (not values): generally safe but should still use allowlists

**When to flag:**
- `prisma.$queryRawUnsafe()` or `prisma.$executeRawUnsafe()` — always dangerous
- String concatenation in SQL: `"SELECT * FROM users WHERE id = " + userId`
- `db.query("SELECT * FROM users WHERE id = ${userId}")` — untagged template

**When to skip:**
- Prisma tagged template raw queries (auto-parameterized)
- ORM query builder methods (Knex, TypeORM QueryBuilder, Drizzle)
- Migration files with static SQL (no user input)

## Pattern 4: Command Injection

**Severity:** REVIEW REQUIRED

```bash
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(child_process|exec\(|execSync\(|spawn\(|execFile\()" [files]
```

**What it detects:**
- Shell command execution that could be exploited if user input reaches the command

**False positives:**
- Build scripts and tooling (postinstall, prebuild)
- `spawn()` with argument arrays (safe — no shell interpolation)
- `execFile()` with fixed command paths (safe — no shell)
- Test helpers that run CLI commands

**When to flag:**
- `exec()` or `execSync()` with any dynamic input: `exec(\`rm ${userInput}\`)`
- Shell commands constructed from request parameters
- `spawn()` with `{ shell: true }` option and dynamic arguments

**When to skip:**
- `spawn('git', ['status'])` — fixed command, array arguments, no shell
- `execFile('/usr/bin/node', ['script.js'])` — fixed path, no shell
- Build-time scripts that never see user input

## Pattern 5: Disabled Security Controls

**Severity:** BLOCKER (in production code)

```bash
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(rejectUnauthorized:\s*false|NODE_TLS_REJECT_UNAUTHORIZED|--no-verify)" [files]
```

**What it detects:**
- Disabled TLS certificate verification (man-in-the-middle vulnerability)
- Disabled git hooks (`--no-verify`)
- Disabled SSL/TLS protections

**False positives:**
- Test configuration: `rejectUnauthorized: false` in test setup for self-signed certs
- Local development configuration explicitly scoped to dev environment
- Comments or documentation mentioning these patterns

**When to flag:**
- Any production code with `rejectUnauthorized: false`
- Environment-agnostic code that disables TLS
- `NODE_TLS_REJECT_UNAUTHORIZED=0` in scripts that run in production

**When to skip:**
- Test configuration files
- Local development proxy setup (explicitly scoped)
- Documentation or comments

## Severity Summary

| Pattern | Default Severity | Escalate When |
|---------|-----------------|---------------|
| Secrets | BLOCKER | Always in production code |
| Code execution | REVIEW | User input reaches eval/innerHTML |
| SQL injection | BLOCKER | Unparameterized queries with dynamic input |
| Command injection | REVIEW | User input reaches exec/spawn |
| Disabled security | BLOCKER | In production code paths |

## Interpreting Results

- **BLOCKER** — Do not proceed. Fix before committing.
- **REVIEW** — Flag for discussion. May be acceptable with justification and mitigation.
- **No matches** — Pattern check passed. Continue validation.

When a pattern matches, always check:
1. Is this in production code or test/build code?
2. Does user/external input reach this code path?
3. Is there a sanitizer or validator between the input and the dangerous operation?
4. Is there an existing security review or ADR that documents this as an accepted risk?
