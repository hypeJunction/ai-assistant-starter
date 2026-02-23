---
name: security-review
description: Systematic security audit with confidence-based reporting. Analyzes attack surfaces, checks against OWASP categories, and reports only confirmed or likely vulnerabilities. Use for pre-merge security review or periodic audits.
category: process
triggers:
  - security audit
  - check vulnerabilities
  - security review
  - OWASP check
  - supply chain security
  - threat modeling
  - API security check
---

# Security Review

> **Purpose:** Systematic security audit of code with confidence-based findings
> **Mode:** Read-only — do NOT modify files
> **Usage:** `/security-review [scope flags]`

## Iron Laws

1. **NO FINDING WITHOUT AN ATTACK VECTOR** — Every reported vulnerability must include how an attacker exploits it. "This could be insecure" is not a finding. "An attacker can inject SQL via the `name` parameter because it's concatenated into the query at line 42" is.
2. **CHECK FOR MITIGATIONS BEFORE REPORTING** — Search the entire codebase for existing protections (middleware, validators, sanitizers) before flagging a vulnerability. False positives erode trust.
3. **CONFIDENCE DETERMINES ACTION** — HIGH confidence: report as finding. MEDIUM: flag for manual verification. LOW: do not report. Never inflate confidence to make a report seem more important.

## When to Use

- Pre-merge security audit
- Periodic security review of critical modules
- After adding authentication, authorization, or payment code
- When handling user input, file uploads, or external data

## When NOT to Use

- General code quality review → `/review`
- Running validation commands → `/validate`
- Fixing a known vulnerability → `/debug` or `/hotfix`
- Performance review → `/validate --full`

## Constraints

- **Read-only** — Report findings only, do not fix
- **Confidence-based reporting** — HIGH: report, MEDIUM: flag as needs verification, LOW: do not report
- **Don't invent issues** — If nothing found, say "clean review" (this is a valid outcome)
- **Research the entire codebase** before reporting — check for mitigations elsewhere
- **No framework FUD** — Don't flag things the framework already handles (see checklists reference)
- **Evidence required** — Every finding must include the vulnerable code AND explain how an attacker exploits it

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Review specific files or directories |
| `--diff` | Review only changed files (current branch vs base) |
| `--module=<name>` | Review a specific module or feature area |
| (none) | Review entire project (will ask to confirm scope) |

## Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **HIGH** | Confirmed vulnerability + attacker-controlled input reaches it + no mitigation found in codebase | Report as finding |
| **MEDIUM** | Possible vulnerability but mitigation may exist elsewhere, or input source unclear | Report as "needs verification" |
| **LOW** | Theoretical risk, framework-mitigated, or requires unlikely preconditions | Do not report |

## Do Not Flag

Skip these — they produce noise, not signal:

- Test files and test fixtures
- Dead code (unreachable, commented out)
- Documentation and comments
- Constants and static configuration
- Code behind authentication that only admins reach (unless reviewing auth itself)
- Framework-mitigated patterns (see checklists reference for details)

## Workflow

### Phase 1: Determine Scope

```bash
# Get project structure
find . -type f -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" | head -100

# If --diff flag
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff $MAIN...HEAD --name-only
```

Categorize files by risk tier:

| Tier | File Types | Priority |
|------|-----------|----------|
| **High risk** | Auth, payments, API routes, middleware, DB queries, file uploads | Review first |
| **Medium risk** | Business logic, data processing, external API calls | Review second |
| **Low risk** | UI components, utilities, config, types | Review if time permits |

If scope is large (>50 files), present tiers and ask user which to focus on.

### Context-Aware Reference Loading

Based on the code in scope, load the relevant reference files for deep analysis:

| Detected Code | Load References |
|---------------|-----------------|
| API routes, middleware, auth | `references/security-checklists.md`, `references/quick-patterns.md` |
| Frontend, templates, JSX | `references/quick-patterns.md`, `references/modern-threats.md` (DOM clobbering, XSS) |
| WebSocket, LLM/AI integration | `references/modern-threats.md` |
| `package.json`, lock files, CI configs | `references/supply-chain.md` |
| Dockerfiles, K8s manifests, Terraform, IAM | `references/infrastructure-security.md` |
| Crypto, secrets, tokens | `references/security-checklists.md` |
| External HTTP calls, webhooks | `references/quick-patterns.md` (SSRF), `references/modern-threats.md` |

Load only what's relevant — don't review all references for every audit.

### Phase 2: Attack Surface Mapping

For each file in scope, identify:

1. **User inputs** — Request params, body, headers, query strings, file uploads, WebSocket messages
2. **Database queries** — Direct SQL, ORM calls, raw queries
3. **Authentication/authorization checks** — Who can reach this code?
4. **External service calls** — APIs, webhooks, third-party SDKs
5. **Cryptographic operations** — Hashing, encryption, token generation
6. **File system operations** — Reads, writes, path construction
7. **Deserialization** — `JSON.parse` with revivers, `yaml.load`, `pickle`, `unserialize`
8. **Supply chain surface** — Dependency manifests, lock files, install scripts, CI/CD configs
9. **Infrastructure configs** — Dockerfiles, K8s manifests, Terraform, cloud IAM policies

Classify each data flow as:
- **Attacker-controlled** — Data from unauthenticated users, URL params, form input
- **Server-controlled** — Environment variables, database lookups by server, config files
- **Gray area** — Database values from prior user input (stored XSS), third-party API responses

Focus analysis on attacker-controlled and gray-area flows.

### Cross-File Data Flow Tracing

For each user input entry point, trace the data flow across files:

1. **Where does input enter?** — Identify the route handler, controller, or resolver that first receives user data
2. **What transformations are applied?** — Follow the data through helper functions, service layers, and middleware. Note any validation, sanitization, encoding, or escaping applied along the way
3. **Where is it used?** — Identify the terminal sink where the data is consumed:
   - Database query (SQL, NoSQL, ORM raw query)
   - Shell command (`exec`, `spawn`, `execFile`)
   - HTML output (`innerHTML`, `dangerouslySetInnerHTML`, template rendering)
   - File system operation (`readFile`, `writeFile`, path construction)
   - HTTP request (SSRF via `fetch`, `axios`, `http.request`)
   - Deserialization (`JSON.parse` with reviver, `yaml.load`, `pickle.loads`)
4. **Flag any path where input reaches a sensitive sink without validation or sanitization** — If user input flows from entry point to a dangerous sink with no transformation, that is a HIGH confidence finding

Trace across file boundaries: follow imports, function calls, and callback chains. Do not stop at a function boundary — if `handleUser(req.body)` calls `createSystemUser(username)` which calls `exec()`, the full chain must be traced.

### Quick Triage

Before deep scanning, run through the quick patterns reference (`references/quick-patterns.md`):

- **Always Flag (Critical):** `eval()`, `exec()`, `pickle.loads()`, `unserialize()`, `new Function()` — dangerous in virtually all contexts
- **Always Flag (High):** `innerHTML`, `dangerouslySetInnerHTML`, SQL string interpolation, hardcoded secrets — dangerous when user-controlled data reaches them
- **Check Context First:** SSRF, path traversal, open redirects, weak crypto, mass assignment, race conditions — investigate data source and mitigations before flagging

### Phase 3: Security Scan

Check each attack surface against OWASP categories (see `references/security-checklists.md`):

1. **Injection** — SQL, NoSQL, command, LDAP, template
2. **XSS** — Reflected, stored, DOM-based
3. **Broken Authentication** — Weak passwords, missing rate limits, session issues
4. **Broken Access Control** — IDOR, missing authz, privilege escalation
5. **CSRF** — State-changing requests without tokens
6. **Race Conditions** — TOCTOU, double-submit, concurrent mutations
7. **Session Management** — Fixation, insecure cookies, missing expiry
8. **Cryptographic Failures** — Weak algorithms, hardcoded keys, missing encryption
9. **Information Disclosure** — Stack traces, verbose errors, exposed internals
10. **Denial of Service** — ReDoS, unbounded queries, resource exhaustion
11. **Business Logic** — Price manipulation, workflow bypass, negative quantities
12. **SSRF** — User-controlled URLs in server-side requests (see `references/modern-threats.md`)
13. **Deserialization** — Unsafe deserialization of untrusted data (see `references/modern-threats.md`)
14. **Supply Chain** — Dependency confusion, typosquatting, pipeline poisoning (see `references/supply-chain.md`)

When reviewing API endpoints, also check the OWASP API Security Top 10 (see `references/security-checklists.md`):
mass assignment, broken object-level authorization, unrestricted resource consumption, SSRF, security misconfiguration.

**Security Error Handling Check** — For each endpoint and error path in scope, check error handling for security implications:

1. **Error message exposure** — Do error responses expose internal file paths, stack traces, database schema details, or SQL error messages? Production error responses must return generic messages (e.g., "Internal server error") without internal details.
2. **Sensitive data in catch blocks** — Do catch blocks log the full request body, headers, or authentication tokens? Logs should redact sensitive fields (`password`, `token`, `authorization`, `cookie`).
3. **Authentication vs authorization error differentiation** — Are authentication failures (wrong password) distinguishable from authorization failures (insufficient permissions) in HTTP responses? Responses should not reveal whether a user account exists. Use timing-safe comparison (`crypto.timingSafeEqual`) for credential checks to prevent timing attacks.

When reviewing infrastructure configs, check against `references/infrastructure-security.md`:
Docker (non-root, no secrets in layers), K8s (security contexts, RBAC), Terraform (no hardcoded secrets, least privilege IAM), CI/CD (pinned actions, minimal permissions).

For each potential finding, record:
- The vulnerable code (file and line)
- The attack vector (how attacker reaches it)
- Initial confidence level

**Attack Chain Analysis** — For P0/P1 findings, analyze attack chains after identifying individual vulnerabilities. How could an attacker combine this vulnerability with others? What is the maximum impact if exploited? For each critical finding, document:

- **Entry point** — How the attacker initiates the attack (e.g., unauthenticated API endpoint, authenticated user input)
- **Exploitation** — What the attacker does to trigger the vulnerability (e.g., inject shell metacharacters, store malicious HTML)
- **Impact** — The immediate consequence (e.g., remote code execution, session hijacking, data theft)
- **Data at risk** — What sensitive data becomes accessible (e.g., environment variables, database contents, user PII, API keys)

If multiple vulnerabilities exist, assess whether they can be chained: for example, command injection enabling RCE, followed by credential theft from environment variables, leading to database exfiltration. Include the chain analysis in the report alongside individual findings.

### Phase 4: Context Research

Before finalizing any finding, search the codebase for mitigations:

```bash
# Example: found raw SQL — check if there's a query builder or ORM layer
grep -r "parameterized\|prepared\|sanitize\|escape" src/

# Example: found user input in template — check if framework auto-escapes
grep -r "dangerouslySetInnerHTML\|v-html\|innerHTML" src/
```

For each potential finding:
- **Search for middleware** that might validate/sanitize input upstream
- **Check framework defaults** — does the framework handle this automatically?
- **Look for wrappers** — is there a security utility layer?

Adjust confidence:
- Found mitigation → downgrade to LOW (remove from report)
- Mitigation is partial or conditional → keep at MEDIUM
- No mitigation found → confirm as HIGH

### Phase 5: Generate Report

```markdown
## Security Review: [scope description]

### Scope
- **Files reviewed:** [count]
- **Risk tiers covered:** [high/medium/low]
- **Method:** [static analysis / diff review / module review]

### HIGH Confidence Findings

#### Finding 1: [Vulnerability Type]
- **Severity:** Critical / High
- **Location:** `file.ts:line`
- **Vulnerable code:**
  ```typescript
  [the actual code]
  ```
- **Attack vector:** [How an attacker exploits this]
- **Evidence:** [Why no mitigation exists — what was checked]
- **Recommended fix:** [Specific remediation]

_(Repeat for each HIGH finding, or "No HIGH confidence findings.")_

### MEDIUM Confidence — Needs Verification

These may be real issues but require manual verification:

1. **[Type]** — `file.ts:line` — [Why it's uncertain: "Input source unclear" / "Mitigation may exist in middleware"]

_(Or "None.")_

### Pre-Conclusion Audit

Before concluding, verify completeness:

| Item | Status |
|------|--------|
| Files in scope reviewed | X / Y |
| High-risk files covered | ✅ / ❌ |
| Attack surfaces mapped | X identified |
| OWASP categories checked | X / 14 |
| Mitigations searched | ✅ |
| Framework patterns verified | ✅ |

### Conclusion

[Overall security posture assessment]

---
**Recommendation:** [Approve / Needs fixes / Needs deeper review by security specialist]
```

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| SEC-T1 | Positive | "Security audit of the auth module" | Skill triggers |
| SEC-T2 | Positive | "Check for vulnerabilities in the API" | Skill triggers |
| SEC-T3 | Positive | "OWASP review before release" | Skill triggers |
| SEC-T4 | Negative | "Review code quality" | Does NOT trigger (-> /review) |
| SEC-T5 | Negative | "Fix the SQL injection bug" | Does NOT trigger (-> /debug or /hotfix) |
| SEC-T6 | Negative | "Run the tests" | Does NOT trigger (-> /validate) |
| SEC-T7 | Boundary | "Review this PR for security and code quality" | Triggers for security phase; code quality defers to /review |

**Clean review template** (when nothing found):

```markdown
## Security Review: [scope]

**Files reviewed:** [count]
**OWASP categories checked:** 14/14
**Findings:** None

No security vulnerabilities found at HIGH or MEDIUM confidence.
This does not guarantee absence of vulnerabilities — it means static analysis
did not identify exploitable issues in the reviewed scope.
```
