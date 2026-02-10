---
name: validate
description: Run validation checks to ensure code quality, security, and correctness. Supports quick (scoped), full (CI pipeline), fix (auto-correct), and CI mirror modes.
---

# Validate

> **Purpose:** Run validation checks for code quality, security, and correctness
> **Modes:** Quick (default) | Full (--full) | Fix (--fix) | CI Mirror (--ci)
> **Usage:** `/validate [scope flags]`

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

**Secrets Scan (always runs):**
```bash
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" [changed-files]
```

Report:
```markdown
### Level 1: Syntax & Style

| Check | Status | Details |
|-------|--------|---------|
| Format | ✓ Pass / ✗ Fail | [N files need formatting] |
| Types | ✓ Pass / ✗ Fail | [N errors] |
| Lint | ✓ Pass / ✗ Fail | [N errors, M warnings] |
| Secrets | ✓ Pass / ⚠️ Review | [N potential secrets found] |
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
| 4 | Security | `npm audit --audit-level=high` |
| 5 | Accessibility | `npm run a11y 2>/dev/null \|\| true` |
| 6 | Performance | `npm run perf 2>/dev/null \|\| true` |
| 7 | Tests | `npm run test` |
| 8 | Coverage | `npm run test -- --coverage` (if --coverage) |
| 9 | Build | `npm run build` |
| 10 | Bundle Size | `npm run size 2>/dev/null \|\| true` |

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
