---
name: validate
description: Run validation checks to ensure code quality, security, and correctness. Supports quick (scoped), full (CI pipeline), fix (auto-correct), and CI mirror modes.
---

# Validate

> **Purpose:** Run validation checks for code quality, security, and correctness
> **Modes:** Quick (default) | Full (--full) | Fix (--fix) | CI Mirror (--ci)
> **Usage:** `/validate [scope flags]`

## Iron Laws

1. **NEVER SKIP TYPE CHECK** — Type check is the first gate. If it fails, nothing else matters. Fix types before running lint or tests.
2. **REPORT WHAT THE OUTPUT SAYS** — Never summarize or interpret validation output. Show the actual errors with file paths and line numbers.
3. **FAILURES ARE NOT SUGGESTIONS** — A failing validation means the code is not ready. Do not proceed past a failing check.

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

## Constraints

- Type check must pass before running tests
- Report all failures clearly with file, line, and suggested fix
- Stop at first failing level (don't waste time on later checks)
- Never skip type check
- Never commit with lint errors
- Run scoped tests by default (not full suite unless `--full`)

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

---

## Common Issues & Solutions

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
