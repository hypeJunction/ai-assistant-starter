---
name: review
description: Comprehensive code review of the current branch against base. Read-only analysis with P0-P3 severity-rated findings and actionable feedback. Use before merging or to check code quality.
---

# Review

> **Purpose:** Code review of the current branch against the base branch
> **Mode:** Read-only — do NOT modify files, run tests, or make commits
> **Usage:** `/review [scope flags]`

## Iron Laws

1. **READ EVERYTHING BEFORE JUDGING** — Read all changed files before forming any opinion. Early conclusions from partial reading lead to wrong findings.
2. **EVIDENCE, NOT THEORY** — Every P0/P1 finding must include the specific code and a concrete explanation of why it's a real problem, not a hypothetical one.
3. **CLEAN REVIEWS ARE VALID** — If the code is good, say so. Not finding issues is a legitimate review outcome, not a failure to review thoroughly.

## When to Use

- Before merging a PR
- After completing implementation work
- Reviewing someone else's branch
- Quality check before release

## When NOT to Use

- Security-specific concerns → `/security-review`
- Running validation commands → `/validate`
- Making code changes → `/implement` or `/refactor`
- Investigating a bug → `/debug`

## Constraints

- **Read-only** — Suggestions only, no modifications
- **Acknowledge good patterns** — Not just problems
- **Fresh context recommended** — If you wrote the code, use a subagent or fresh session to avoid self-confirmation bias

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Review specific files instead of full branch diff |
| `--pr=<number>` | Review a specific PR by number |

## Severity + Confidence

| Level | Label | Confidence Required | When to Use |
|-------|-------|---------------------|-------------|
| P0 | Critical | HIGH — confirmed in code | Security vulnerability, data loss, correctness bug |
| P1 | High | HIGH — likely real | Logic error, race condition, performance regression |
| P2 | Medium | MEDIUM — possible | Code smell, maintainability concern |
| P3 | Low | Any | Style, naming, minor suggestion |

**Confidence determines whether to report:**
- **HIGH** — Confirmed by reading code + evidence of real impact → Report
- **MEDIUM** — Pattern is typically problematic but mitigation may exist → Report as "needs verification"
- **LOW** — Theoretical or framework-mitigated → Do not report

## Workflow

### Step 1: Gather Context

```bash
git branch --show-current
MAIN_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
gh pr view --json number,title,body,baseRefName,url 2>/dev/null
```

### Step 2: Get the Diff

```bash
git diff $MAIN_BRANCH...HEAD --stat
git diff $MAIN_BRANCH...HEAD
```

### Step 3: Validate Scope

- **Empty diff** → Report "No changes found" and exit
- **Large diff (>500 lines)** → Warn user, ask to review all or focus on specific areas
- **Mixed-concern changes** (feature + refactor + config) → Flag as candidate for splitting into separate PRs

### Step 4: Review Each File

For each changed file, read the full file for context. Check:

**Code Quality:** No `any` types, proper typing, correct imports, no lint warnings
**Testing:** Test coverage for new code, meaningful descriptions, proper async handling
**Security (structured check — do not skip):**
- No `eval()`, `new Function()`, or dynamic code execution with external input
- No `innerHTML`, `dangerouslySetInnerHTML`, or `v-html` with unsanitized data
- No raw SQL with string interpolation — parameterized queries or ORM required
- No hardcoded secrets, API keys, or credentials in source files
- No `child_process.exec()` with user-controlled input
- No disabled security controls (`rejectUnauthorized: false`)
- Input validation present at API boundaries (request params, body, headers)
- Auth/authz checks present on protected operations
- No open redirects (redirect URLs validated against allowlist)
- No sensitive data in logs or error messages exposed to users
**Performance:** No obvious bottlenecks, efficient data fetching
**General:** No `console.log` in prod, error handling present, no dead code

### Escalation Flags

Flag for explicit discussion even if no bug is found:
- Schema or migration changes
- API contract changes (request/response shape, status codes)
- New dependencies added
- Security-sensitive code (auth, crypto, input handling)
- Infrastructure or CI/CD config changes

### Step 5: Generate Report

```markdown
## Code Review: [Branch Name]

### Summary
[Brief overview of what the changes accomplish]

### P0 Critical
1. **[Issue]** — `file.ts:line` — Confidence: HIGH
   - **Evidence:** [Why real, not theoretical]
   - **Fix:** [Specific remediation]

_(None found — or list findings)_

### P1 High
1. **[Issue]** — `file.ts:line` — Confidence: HIGH/MEDIUM
   - **Evidence:** [Why it matters]
   - **Fix:** [Approach]

### P2 Medium
1. [Issue] — `file.ts:line` — [suggestion]

### P3 Low
1. [Suggestion] — `file.ts:line`

### Positive Notes
- [What was done well]

### Escalation Flags
- [Any flagged items, or "None"]

### Files Reviewed
| File | Status | Notes |
|------|--------|-------|
| path/to/file.ts | ✅/🟡/🔴 | Brief note |

### Areas Not Covered
[What couldn't be verified — runtime behavior, external API contracts, business logic]

### Residual Risks
[Risks remaining even after fixing all findings]

---
**Recommendation:** [Approve / Request Changes / Needs Discussion]
```

### Step 6: Action Menu

```markdown
**What would you like to do?**
1. **Fix all** — Apply fixes for all P0-P2 findings
2. **Fix P0-P1 only** — Critical and high issues only
3. **Fix specific items** — Choose which (e.g., "P0.1, P1.2")
4. **No changes** — Keep as read-only review
```

**STOP HERE. Wait for user selection.**

If user picks a fix option, apply fixes in priority order (P0 → P1 → P2), run typecheck and lint after, then offer to commit.
