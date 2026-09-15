---
name: validate
description: Run validation checks to ensure code quality, security, and correctness. Supports quick (scoped), full (CI pipeline), fix (auto-correct), and CI mirror modes.
category: process
model: sonnet
effort: medium
triggers:
  - run checks
  - verify quality
  - typecheck
  - lint
  - does it pass
---

# Validate

> **Purpose:** Run validation checks for code quality, security, and correctness
> **Modes:** Quick (default) | Full (--full) | Fix (--fix) | CI Mirror (--ci)
> **Usage:** `/validate [scope flags]`

## Iron Laws

1. **NEVER SKIP TYPE CHECK** — Type check is the first gate. If it fails, nothing else matters. Fix types before running lint or tests.
2. **REPORT WHAT THE OUTPUT SAYS** — Never summarize or interpret validation output. Show the actual errors with file paths and line numbers.
3. **FAILURES ARE NOT SUGGESTIONS** — A failing validation means the code is not ready. Do not proceed past a failing check.
4. **NO CLAIMS WITHOUT FRESH EVIDENCE** — Never report a check as passing without showing the actual command output from this session. Words like "should pass," "probably works," or "looks correct" are not verification. Run the command, read the output, then state the result.
5. **NEVER RUN CHECKS IN THE MAIN AGENT** — Every command in this skill (format, typecheck, lint, tests, build, coverage, audit) is dispatched to an independent subagent via the `Agent` tool. The main agent reads the subagent's raw output; it does not execute the command itself.

## When to Use

- After making code changes to check nothing is broken
- Before committing to ensure quality
- As part of `/implement` or `/finish` workflows
- To check if CI will pass locally

## When NOT to Use

- Writing or running specific tests → `/test-coverage` or `/tdd`
- Reviewing code quality and patterns → `/review`
- Fixing bugs → `/debug`
- Security-specific audit → `/security-review`

## Early Exit

If `git status` shows no changes and no specific mode is requested, report "No changes to validate" and offer to run full validation anyway.

## Constraints

- Type check must pass before running tests
- Report all failures clearly with file, line, and suggested fix
- Stop at first failing level (don't waste time on later checks)
- Never skip type check
- Never commit with lint errors
- Run scoped tests by default (not full suite unless `--full`)

> **Note:** Detect package manager from lockfile (`package-lock.json` = npm, `pnpm-lock.yaml` = pnpm, `yarn.lock` = yarn, `bun.lockb` = bun). Use detected manager for all commands. Command examples below use `npm` as placeholder — substitute the detected manager.

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Validate specific files/directories |
| `--uncommitted` | Validate uncommitted changes (default) |
| `--staged` | Validate staged changes only |
| `--full` | Run complete CI pipeline |
| `--ci` | Mirror exact CI configuration |
| `--fix` | Auto-fix correctable issues |
| `--security` | Include security checks |
| `--coverage` | Include test coverage report |

**Examples:**
```bash
/validate                           # Quick validation of uncommitted changes
/validate --files=src/components/   # Specific directory
/validate --full                    # Complete CI pipeline
/validate --fix                     # Auto-fix lint/format issues
/validate --ci                      # Mirror exact CI checks
/validate --full --coverage         # Full validation with coverage
```

---

## Quick Validation (Default)

Fast feedback during development — validate only what changed.

### Step 0: Determine Scope

```bash
git diff --name-only HEAD
git diff --name-only --staged  # if --staged flag
```

### Level 1: Syntax & Style

> **Execution order within this level:** Run checks in dependency order: (a) Typecheck first (catches type errors that cause other failures), (b) Lint second (may depend on types), (c) Tests third (need types and imports correct), (d) Build last (depends on all above). This prevents cascading failures from obscuring root causes.

**Format Check:**
```bash
npm run format:check 2>/dev/null || npx prettier --check [changed-files]
```

**Type Check:**
```bash
npm run typecheck
```

**Lint:**
```bash
npm run lint -- [changed-files]
```

**Security Scan (always runs):**

> See `references/security-scan-patterns.md` for concrete grep patterns for secrets, dangerous functions, and security anti-patterns. Run these scans as part of full validation.

```bash
# Secrets detection
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" [changed-files]

# Insecure pattern detection
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|document\.write\()" [changed-files]

# Raw SQL interpolation (injection risk)
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(\\\$queryRaw\`|\\\$executeRaw\`|\.query\(.*\\\$\{|SELECT.*\\\$\{|INSERT.*\\\$\{|UPDATE.*\\\$\{|DELETE.*\\\$\{)" [changed-files]

# Command injection patterns
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(child_process|exec\(|execSync\(|spawn\(|execFile\()" [changed-files]

# Disabled security controls
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(rejectUnauthorized:\s*false|NODE_TLS_REJECT_UNAUTHORIZED|--no-verify)" [changed-files]
```

**Interpreting results:**
- Secrets: Any match in non-test, non-example files is a **blocker** — do not proceed
- `eval`/`innerHTML`/`dangerouslySetInnerHTML`: Requires justification — flag for review
- Raw SQL with interpolation: **Blocker** unless using tagged template literals (`Prisma.sql\`...\``)
- `child_process`/`exec`: Flag for review — verify no user input reaches the command
- Disabled TLS/verification: **Blocker** unless in test configuration only

Report:
```markdown
### Level 1: Syntax & Style

| Check | Status | Details |
|-------|--------|---------|
| Format | ✓ Pass / ✗ Fail | [N files need formatting] |
| Types | ✓ Pass / ✗ Fail | [N errors] |
| Lint | ✓ Pass / ✗ Fail | [N errors, M warnings] |
| Secrets | ✓ Pass / ⚠️ Review | [N potential secrets found] |
| Security patterns | ✓ Pass / ⚠️ Review | [N insecure patterns found] |
```

**If failures, stop and report before Level 2.**

### Level 2: Scoped Tests

Run tests only for changed components/files:

```bash
npm run test -- ComponentName
npm run test -- "src/components/"
```

### Level 3: Integration (Optional)

For UI changes, suggest manual verification:
```bash
npm run dev
```

---

## Full Validation (--full)

Complete CI pipeline verification before push/merge.

| Step | Check | Command |
|------|-------|---------|
| 1 | Format | `npm run format:check` |
| 2 | Types | `npm run typecheck` |
| 3 | Lint | `npm run lint` |
| 4 | Security scan | Secrets + insecure pattern detection (see Quick Validation) |
| 5 | Dependency audit | `npm audit --audit-level=high` |
| 6 | Accessibility | `npm run a11y 2>/dev/null \|\| true` |
| 7 | Performance | `npm run perf 2>/dev/null \|\| true` |
| 8 | Tests | `npm run test` |
| 9 | Coverage | `npm run test -- --coverage` (if --coverage) |
| 10 | Build | `npm run build` |
| 11 | Bundle Size | `npm run size 2>/dev/null \|\| true` |

Report:
```markdown
## Full Validation Results

| Step | Check | Status | Time |
|------|-------|--------|------|
| 1 | Format | ✓ Pass | 2s |
| 2 | Types | ✓ Pass | 8s |
| ... | ... | ... | ... |

✅ **All CI checks passed** — Ready to push
```

---

## Fix Mode (--fix)

Auto-correct formatting and lint issues.

1. **Auto-fix format:** `npm run format 2>/dev/null || npx prettier --write [changed-files]`
2. **Auto-fix lint:** `npm run lint -- --fix [changed-files]`
3. **Verify fixes:** Re-run typecheck and lint
4. **Run scoped tests:** `npm run test -- [affected-tests]`

Report:
```markdown
## Fix Mode Results

### Auto-fixed
| Type | Files Fixed | Issues Resolved |
|------|-------------|-----------------|
| Format | 5 | 23 |
| Lint | 3 | 8 |

### Remaining Issues (manual fix required)
| File | Line | Issue |
|------|------|-------|
| `src/utils.ts` | 45 | Type error: cannot assign... |
```

---

## CI Mirror Mode (--ci)

Run exact same checks as CI pipeline.

1. **Detect CI config:** Look for `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`
2. **Extract CI steps:** Parse config and run equivalent local commands
3. **Report:** Show CI job → local command → status mapping

In CI mode (`--mode=ci`):
- Run the same checks as full mode
- Use non-interactive output (no fix offers)
- Exit with non-zero code on any failure
- Output results in a format parseable by CI systems (structured JSON or standard exit codes)

---

## Verification Patterns

### Regression Test Verification

When validating a bug fix with a regression test, verify the test actually catches the bug:

```
1. Write the regression test
2. Run it → MUST PASS (with the fix in place)
3. Revert the fix
4. Run it → MUST FAIL (proves the test catches the bug)
5. Restore the fix
6. Run it → MUST PASS (confirms fix works)
```

A regression test that passes both with and without the fix proves nothing. Skip the red-green cycle only for tests that verify new behavior (not bug fixes).

### Agent Delegation Verification

Every command in this skill (typecheck, lint, tests, build, coverage, security scan) runs in an independent subagent via the `Agent` tool — never directly in the main agent's shell (see `ai-assistant-protocol` § Validation Execution).

When a subagent reports task completion, verify independently:

1. Check the VCS diff — does it show the expected changes?
2. Dispatch a fresh subagent to (re-)run validation commands and return full raw output — don't trust a bare "all tests pass" claim from any agent, including the one that made the change
3. Read that raw output yourself and report the actual state based on it

---

## Common Issues & Solutions (see `references/validation-troubleshooting.md` for expanded patterns including build failures and CI discrepancies)

### Type Errors

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| `Cannot find module` | Missing import | Check path, add dependency |
| `Type X not assignable to Y` | Type mismatch | Fix types or add assertion |
| `Property does not exist` | Missing property | Add to interface |
| `Implicit any` | Missing annotation | Add explicit type |

### Test Failures

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Timeout | Async not awaited | Add `await` or increase timeout |
| Mock not called | Wrong mock setup | Check mock implementation |
| Snapshot mismatch | Intentional change | Update snapshot with `-u` |

---

## Validation Levels Reference

| Level | Checks | When to Use |
|-------|--------|-------------|
| **Quick** | Format, Types, Lint, Scoped Tests | During development |
| **Full** | All checks + Full test suite + Build | Before push/PR |
| **CI** | Mirror exact CI pipeline | Before important merges |
| **Fix** | Auto-correct + Verify | When you have many small issues |

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| VAL-T1 | Positive | "Run the checks" | Skill triggers |
| VAL-T2 | Positive | "Does it pass typecheck?" | Skill triggers |
| VAL-T3 | Positive | "Lint my code" | Skill triggers |
| VAL-T4 | Negative | "Write tests for this" | Does NOT trigger (→ /test-coverage) |
| VAL-T5 | Negative | "Review the code quality" | Does NOT trigger (→ /review) |
| VAL-T6 | Negative | "Fix the type error" | Does NOT trigger (→ /debug) |
| VAL-T7 | Boundary | "Check if CI will pass" | Triggers with --ci flag |
