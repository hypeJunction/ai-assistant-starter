---
name: security-review
description: Systematic security audit with confidence-based reporting. Analyzes attack surfaces, checks against OWASP categories, and reports only confirmed or likely vulnerabilities. Use for pre-merge security review or periodic audits.
---

# Security Review

> **Purpose:** Systematic security audit of code with confidence-based findings
> **Mode:** Read-only — do NOT modify files
> **Usage:** `/security-review [scope flags]`

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

### Phase 2: Attack Surface Mapping

For each file in scope, identify:

1. **User inputs** — Request params, body, headers, query strings, file uploads, WebSocket messages
2. **Database queries** — Direct SQL, ORM calls, raw queries
3. **Authentication/authorization checks** — Who can reach this code?
4. **External service calls** — APIs, webhooks, third-party SDKs
5. **Cryptographic operations** — Hashing, encryption, token generation
6. **File system operations** — Reads, writes, path construction

Classify each data flow as:
- **Attacker-controlled** — Data from unauthenticated users, URL params, form input
- **Server-controlled** — Environment variables, database lookups by server, config files

Focus analysis on attacker-controlled flows.

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

For each potential finding, record:
- The vulnerable code (file and line)
- The attack vector (how attacker reaches it)
- Initial confidence level

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
| OWASP categories checked | X / 11 |
| Mitigations searched | ✅ |
| Framework patterns verified | ✅ |

### Conclusion

[Overall security posture assessment]

---
**Recommendation:** [Approve / Needs fixes / Needs deeper review by security specialist]
```

**Clean review template** (when nothing found):

```markdown
## Security Review: [scope]

**Files reviewed:** [count]
**OWASP categories checked:** 11/11
**Findings:** None

No security vulnerabilities found at HIGH or MEDIUM confidence.
This does not guarantee absence of vulnerabilities — it means static analysis
did not identify exploitable issues in the reviewed scope.
```
