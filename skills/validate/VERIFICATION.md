# Validate Skill Verification

## Scenario

A developer has just finished implementing a feature and wants to run full validation before committing. The project uses TypeScript, Vitest, ESLint, and has a build step. There is a type error in one file, 2 lint warnings (unused import, missing return type), and all tests pass. They invoke `/validate --mode=full`.

### Project Setup

| Tool | Version | Config |
|------|---------|--------|
| TypeScript | 5.x | `tsconfig.json` with `strict: true` |
| Vitest | 1.x | `vitest.config.ts` |
| ESLint | 8.x | `.eslintrc.cjs` with `@typescript-eslint` |
| Build | Vite | `vite build` via `npm run build` |

### package.json Scripts

```json
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "lint": "eslint src/",
    "test": "vitest run",
    "build": "vite build"
  }
}
```

### Issues Present

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `src/services/order.service.ts` | 23 | Type error: `Type 'string' is not assignable to type 'number'` | Error |
| `src/utils/format.ts` | 1 | Unused import: `'dayjs' is defined but never used` | Warning |
| `src/utils/format.ts` | 12 | Missing return type: `Missing return type on function 'formatCurrency'` | Warning |

All 14 tests pass. The build fails because the type error in `order.service.ts` prevents compilation.

## Expected Outcome

The agent runs all four checks in dependency order (typecheck, lint, tests, build). Typecheck catches the type error in `order.service.ts:23`. Lint catches the 2 warnings in `format.ts`. Tests all pass with 14/14 reported. Build fails due to the type error. The agent presents a structured report with all results -- it does not stop at the first failure. The agent offers to fix the issues. After fixing, the agent re-validates to confirm all checks pass cleanly.

## Key Checkpoints

### Checkpoint 1: Agent identifies validation mode (full -- all checks)

**Phase:** Mode Detection

The agent parses the `--mode=full` flag (or `--full`) and recognizes that full validation requires running all checks: typecheck, lint, tests, and build. The agent does not default to quick/scoped validation.

**Evidence expected:**
```
Running full validation (--full mode).
Checks: Format, Typecheck, Lint, Security Scan, Tests, Build
```

### Checkpoint 2: Agent determines correct commands from project config

**Phase:** Command Discovery

The agent reads `package.json` to discover available scripts. It detects the package manager from the lockfile (e.g., `package-lock.json` for npm, `pnpm-lock.yaml` for pnpm, `yarn.lock` for yarn). It maps each validation step to the correct project command rather than hardcoding `npm run`.

**Evidence expected:**

The agent reads `package.json` and identifies:
- `typecheck` -> `npm run typecheck` (or detected package manager equivalent)
- `lint` -> `npm run lint`
- `test` -> `npm run test`
- `build` -> `npm run build`

If the project used pnpm, the agent would use `pnpm run typecheck`, not `npm run typecheck`.

### Checkpoint 3: Agent runs typecheck -- catches type error, reports file:line

**Phase:** Level 1: Syntax & Style (typecheck runs first within level)

The agent runs `npm run typecheck` (or equivalent). TypeScript reports the type error. The agent captures the output and reports the exact file, line, and error message. The agent does NOT stop here -- it continues to the next check.

**Evidence expected:**
```
Typecheck: FAILED (1 error)

src/services/order.service.ts:23 - error TS2322: Type 'string' is not assignable to type 'number'.
  23 |   const total: number = calculateTotal(items)
```

### Checkpoint 4: Agent runs lint -- catches 2 warnings, reports file:line

**Phase:** Level 1: Syntax & Style (lint runs second within level)

The agent runs `npm run lint`. ESLint reports the 2 warnings. The agent captures the output and reports each warning with file, line, and rule name. The agent continues to the next check.

**Evidence expected:**
```
Lint: PASSED with warnings (0 errors, 2 warnings)

src/utils/format.ts:1 - warning @typescript-eslint/no-unused-vars: 'dayjs' is defined but never used
src/utils/format.ts:12 - warning @typescript-eslint/explicit-function-return-type: Missing return type on function 'formatCurrency'
```

### Checkpoint 5: Agent runs tests -- all pass, reports count

**Phase:** Level 1: Syntax & Style / Level 2: Tests

The agent runs `npm run test`. All 14 tests pass. The agent reports the count and confirms no failures.

**Evidence expected:**
```
Tests: PASSED (14/14)

Test Suites: 4 passed, 4 total
Tests:       14 passed, 14 total
```

### Checkpoint 6: Agent runs build -- fails due to type error

**Phase:** Full Validation: Build step

The agent runs `npm run build`. The build fails because the TypeScript type error in `order.service.ts` prevents successful compilation. The agent reports the build failure and links it back to the type error found in Checkpoint 3.

**Evidence expected:**
```
Build: FAILED

Build failed due to TypeScript compilation error:
src/services/order.service.ts:23 - Type 'string' is not assignable to type 'number'

Note: This is the same type error reported in the typecheck step.
Fixing the type error will resolve both the typecheck and build failures.
```

### Checkpoint 7: Agent presents structured report with all results

**Phase:** Report Generation

The agent compiles all results into a single structured report. The report covers every check that was run, with pass/fail status, issue counts, and timing. The report does not omit any check, even if an earlier check failed.

**Evidence expected:**
```markdown
## Full Validation Results

| Step | Check | Status | Details |
|------|-------|--------|---------|
| 1 | Typecheck | FAIL | 1 error (src/services/order.service.ts:23) |
| 2 | Lint | WARN | 0 errors, 2 warnings (src/utils/format.ts) |
| 3 | Tests | PASS | 14/14 passed |
| 4 | Build | FAIL | Compilation error (caused by type error above) |

Result: 2 checks failed, 1 check has warnings, 1 check passed.
```

### Checkpoint 8: Agent determines execution order within validation level

**Phase:** Planning / Execution

The agent runs checks in dependency order within each validation level: typecheck first (catches type errors that cause other failures), lint second (may depend on types), tests third (need types and imports correct), build last (depends on all above). This prevents cascading failures from obscuring root causes.

**Evidence expected:**

The agent runs typecheck before build. The build failure is correctly identified as a downstream consequence of the type error, not as a separate root cause. The agent does not waste time debugging the build failure independently.

### Checkpoint 9: Agent offers to fix issues

**Phase:** Remediation

After presenting the full report, the agent offers to fix the identified issues. The offer is specific about what can be fixed and what requires manual intervention.

**Evidence expected:**
```
3 issues found. I can fix all of them:

1. Type error in order.service.ts:23 — Fix the type mismatch
2. Unused import in format.ts:1 — Remove the 'dayjs' import
3. Missing return type in format.ts:12 — Add return type to 'formatCurrency'

Would you like me to fix these? (all / specific / none)
```

### Checkpoint 10: After fixing, agent re-validates to confirm all clean

**Phase:** Re-validation

After the user approves fixes and the agent applies them, the agent re-runs the full validation pipeline (typecheck, lint, tests, build). All checks pass. The agent reports a clean validation.

**Evidence expected:**
```
Re-running full validation after fixes...

| Step | Check | Status | Details |
|------|-------|--------|---------|
| 1 | Typecheck | PASS | 0 errors |
| 2 | Lint | PASS | 0 errors, 0 warnings |
| 3 | Tests | PASS | 14/14 passed |
| 4 | Build | PASS | Build succeeded |

All checks passed. Ready to commit.
```

### Checkpoint 11: If project has no build script, agent skips build (not fails)

**Phase:** Command Discovery / Execution

If a project's `package.json` does not contain a `build` script, the agent skips the build step gracefully rather than failing with "script not found." The report shows the build step as "Skipped (no build script)" rather than as a failure.

**Evidence expected:**
```
| Step | Check | Status | Details |
|------|-------|--------|---------|
| ... | ... | ... | ... |
| 4 | Build | SKIP | No build script found in package.json |
```

## Anti-Patterns

### 1. Agent stops at first failure (should run all checks and report all issues)

**Wrong:** Agent runs typecheck, sees the type error, and immediately stops. It never runs lint, tests, or build. The developer only learns about the type error and has to run `/validate` again after fixing it to discover the lint warnings.

Full validation must run all checks regardless of earlier failures. The whole point of `--full` mode is to get a comprehensive view of all issues at once, so the developer can fix everything in a single pass.

### 2. Agent runs build before typecheck (type errors cause build failures)

**Wrong:** Agent runs build first, sees the compilation failure, and reports a build error. Then it runs typecheck and finds the same type error. The developer now sees what appears to be two separate issues when it is really one root cause.

Checks must run in dependency order: typecheck before build. This ensures the root cause (type error) is identified first, and the build failure is correctly attributed to it rather than reported as an independent problem.

### 3. Agent fails if optional scripts do not exist

**Wrong:** The project does not have a `format:check` script. The agent runs `npm run format:check`, gets a "missing script" error, and reports a format check failure. The developer is confused because they never configured a formatter.

Optional checks (format, a11y, perf, size) should be skipped gracefully if the corresponding script does not exist. Use `npm run X 2>/dev/null || true` for optional steps, or check `package.json` scripts before running.

### 4. Agent hardcodes npm when project uses different package manager

**Wrong:** The project uses pnpm (has `pnpm-lock.yaml`), but the agent runs `npm run typecheck`. This may work in some cases but can cause subtle issues: different dependency resolution, missing packages, or wrong versions.

The agent must detect the package manager from the lockfile (`package-lock.json` = npm, `pnpm-lock.yaml` = pnpm, `yarn.lock` = yarn, `bun.lockb` = bun) and use the detected manager for all commands.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| Intra-Level 1 execution order unclear | The skill listed typecheck, lint, and format as Level 1 checks but did not specify which runs first within the level. An agent might run lint before typecheck, causing type-error-induced lint failures to obscure the root cause. | Added explicit intra-level ordering: typecheck first, lint second, tests third, build last. This dependency order prevents cascading failures from masking root causes. |
| security-scan-patterns.md not proactively linked | The security scan section referenced patterns inline but did not proactively direct the agent to `references/security-scan-patterns.md` for the full pattern catalog, false positive guidance, and severity classification. | Added explicit cross-reference: "See `references/security-scan-patterns.md` for concrete grep patterns for secrets, dangerous functions, and security anti-patterns. Run these scans as part of full validation." |
| CI mode not fully expanded | The `--ci` mode section described detecting and parsing CI config, but did not specify output format, exit code behavior, or non-interactive constraints. An agent in CI mode might still offer interactive fix prompts. | Added CI mode specification: non-interactive output (no fix offers), non-zero exit code on any failure, results in parseable format (structured JSON or standard exit codes). |
| Package manager hardcoded as npm | Command examples throughout the skill used `npm run` without detecting the project's actual package manager. Projects using pnpm, yarn, or bun would get incorrect commands. | Added package manager detection: detect from lockfile, use detected manager for all commands. The existing note about adapting to project's package manager was generic; now it is a concrete detection step. |
