---
name: test-coverage
description: Analyze branch changes and ensure adequate test coverage. Creates missing tests, runs them, and reports results. Use after implementing changes to add tests.
category: process
model: sonnet
effort: medium
triggers:
  - add tests
  - missing tests
  - test coverage
  - needs tests
  - untested code
---

# Test Coverage

> **Purpose:** Ensure test coverage for changed code
> **Phases:** Analyze → Discover → Baseline → Design → Write → Run → Measure → Report
> **Usage:** `/test-coverage [scope flags]`

## Iron Laws

1. **EVERY CHANGED FUNCTION NEEDS A TEST** — No exceptions for "simple" code. Simple code that breaks causes the worst outages because nobody thought to test it.
2. **TESTS MUST BE INDEPENDENT** — No shared mutable state, no test ordering dependencies. Every test must pass when run alone.
3. **TEST BEHAVIOR, NOT IMPLEMENTATION** — Test what the code does, not how it does it. Refactoring should not break tests.

## When to Use

- After implementing a feature (post `/implement`)
- When adding tests to existing uncovered code
- Before submitting a PR to ensure coverage
- When a bug fix needs regression tests

## When NOT to Use

- Writing tests before code → `/tdd`
- Debugging a test failure → `/debug`
- Full CI validation → `/validate`

## Constraints

- Create test files (`.spec.ts`, `.test.ts`) freely
- Do not modify non-test source files without approval
- Scope tests to changes — don't run full suites unless necessary

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Specific files/directories to check coverage for |
| `--branch=<name>` | Compare against specific branch (default: main) |
| `--uncommitted` | Cover only uncommitted changes |

## Test Quality Criteria

| Criterion | Rule | Smell if Violated |
|-----------|------|-------------------|
| **Independent** | No shared mutable state between tests | Tests pass alone but fail together |
| **Fast** | Mock external dependencies (DB, API, filesystem) | Suite takes minutes |
| **Readable** | Clear Arrange/Act/Assert structure | Can't understand without reading source |
| **Focused** | One behavior per test | Test name contains "and" |
| **Deterministic** | Same input → same output | Flaky tests |

## Don't Test

- **Types / interfaces** — no runtime behavior
- **Trivial getters/setters** — one-line property access with no logic
- **Framework internals** — React rendering, Express routing itself
- **Constants / enums** — static values
- **Generated code** — Prisma client, GraphQL codegen

## Test Smell Detection

| Smell | Fix |
|-------|-----|
| **Testing implementation details** (spying on private methods) | Test the public API output |
| **Multi-concern tests** (name has "and") | Split into focused tests |
| **Mirror tests** (structure mirrors implementation) | Test inputs/outputs |
| **No meaningful assertions** (only checks no error thrown) | Assert on return values or side effects |
| **Testing the mock** (assertions only on mock calls) | Assert on behavior the mock enables |
| **Coverage theater** (tests execute code without meaningful assertions) | Add real assertions or delete the test |

## Coverage Targets

| File Type | Target | Focus |
|-----------|--------|-------|
| Business logic / services | 80%+ | Edge cases, error paths |
| Utilities / helpers | 90%+ | All code paths |
| API routes / handlers | 70%+ | Happy path + error codes |
| UI components | 60%+ | User interactions, states |

---

## Workflow

### Step 1: Analyze Changes

```bash
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff --name-only $MAIN_BRANCH..HEAD
```

### Step 2: Categorize and Identify Missing Coverage

| File Type | Test Type | Priority |
|-----------|-----------|----------|
| `*.ts` utilities/services | Unit tests (`.spec.ts`) | High |
| `*.tsx` components | Component tests | High |
| `*.ts` types/interfaces | Skip | — |
| Config/build files | Skip | — |

**Early exit:** If all changed files are type-only (interfaces, type definitions, enums, constants), config-only, or already have adequate test coverage, report this and exit:

```markdown
## Nothing to Test

All changed files are either type-only definitions or already have adequate coverage:
- `types/user.ts` — type definitions only (skip)
- `services/auth.service.ts` — existing tests cover changes (skip)

No new tests needed.
```

### Step 3: Discover Test Patterns

Before writing any tests, discover where existing tests live and what patterns they use:

1. **File naming:** Search for `*.spec.ts`, `*.test.ts`, `*.spec.tsx`, `*.test.tsx` to determine the project convention
2. **Directory structure:** Check if tests are co-located with source files or in separate `__tests__/` directories
3. **Import patterns:** Note how modules under test are imported (relative paths, aliases, barrel imports)
4. **Mock patterns:** Identify how dependencies are mocked (manual mocks, `vi.mock()`, `jest.mock()`, dependency injection)

Read 1-2 existing test files that are closest to the files being tested (same directory or same file type) and adopt their:
- `describe`/`it` nesting structure
- Setup/teardown patterns (`beforeEach`, `afterEach`, factories)
- Assertion style (`expect().toBe()`, `expect().toEqual()`, custom matchers)
- Mock approach (inline mocks, shared fixtures, mock factories)

If no existing test files are found, use the default structure in Step 6.

### Step 4: Measure Coverage Baseline

Check if the project has coverage tooling configured:

1. Look for coverage configuration in `vitest.config.*`, `jest.config.*`, `package.json` (jest/vitest sections), or `.nycrc`
2. Check `package.json` scripts for a coverage command (e.g., `test:coverage`, `coverage`)

If coverage tooling is available, run coverage on affected files to establish a baseline:

```bash
# Vitest example
npm run test -- --coverage --run <affected-pattern>

# Jest example
npm run test -- --coverage --collectCoverageFrom='<affected-pattern>' --forceExit
```

Record the baseline coverage percentages for affected files. If no coverage tooling exists, note this in the final report and proceed without numeric measurements.

### Step 5: Design Test Plans

For each file needing tests:

```markdown
## Test Plan: [ModuleName]

| Function | Behaviors | Edge Cases |
|----------|-----------|------------|
| `functionA` | happy path, error path | null input, empty array |
```

### Step 6: Write Tests

**Test structure (default — override with patterns discovered in Step 3):**
```typescript
describe('ModuleName', () => {
  describe('functionName', () => {
    it('should [expected behavior] when [condition]', () => {
      // Arrange
      // Act
      // Assert
    });
  });
});
```

**Coverage priorities:** Happy path → Edge cases (null, empty, boundary) → Error conditions → Async operations

**For utilities with well-defined contracts**, consider property-based testing (e.g., with fast-check) to catch edge cases that example-based tests miss.

### Step 7: Run and Fix

**Delegate each check to its own subagent** — run every distinct command via a separate `Agent` call, never directly in the main agent's shell and never bundled into one call. Send independent checks in a single message with multiple tool uses so they run concurrently. Give each subagent its exact command and require raw output sized to the outcome; read every subagent's output yourself before reporting results. See `ai-assistant-protocol` § Validation Execution.

```bash
npm run test -- path/to/file.spec.ts
```

If failures: fix mocks, assertions, missing `await`, or isolation issues. Re-run until green.

### Step 8: Measure Coverage After

If coverage tooling was available in Step 4, re-run coverage to show improvement:

```bash
npm run test -- --coverage --run <affected-pattern>
```

Compare before vs after for each affected file. Record the delta.

If coverage tooling is not available, skip this step — the report in Step 9 will note that numeric coverage was not measurable.

### Step 9: Report and Approve

Present the coverage report and wait for user approval before committing.

```markdown
## Test Coverage Report

### Coverage Summary (if measurable)
| File | Before | After | Delta |
|------|--------|-------|-------|
| `services/user.service.ts` | 12% | 85% | +73% |
| `utils/validator.ts` | 0% | 92% | +92% |

### Tests Created
- `user.service.spec.ts` — 8 tests, all passing
- `validator.spec.ts` — 5 tests, all passing

### Skipped (No Tests Needed)
- `types.ts` — type definitions only

### Remaining Gaps
- `user.service.ts` line 45-52: error recovery branch (edge case, low risk)

### Test Quality Check
| Criterion | Status |
|-----------|--------|
| Independent | Pass |
| Fast | Pass |
| Focused | Pass |
| Deterministic | Pass |
```

**GATE: Do NOT commit until user responds with explicit approval.** See `ai-assistant-protocol` for valid approval terms and invalid responses.

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| COV-T1 | Positive | "Add tests for this code" | Skill triggers |
| COV-T2 | Positive | "Ensure test coverage for my changes" | Skill triggers |
| COV-T3 | Positive | "These files need tests" | Skill triggers |
| COV-T4 | Negative | "Write the test first, then implement" | Does NOT trigger (-> /tdd) |
| COV-T5 | Negative | "Run the test suite" | Does NOT trigger (-> /validate) |
| COV-T6 | Negative | "Debug the failing test" | Does NOT trigger (-> /debug) |
| COV-T7 | Boundary | "This function needs a test" | Triggers (adding coverage to existing code) |
| COV-T8 | Early-exit | All changed files are type-only or already covered | Reports "No new tests needed" and exits |

## Quick Reference

| Phase | Gate |
|-------|------|
| 1. Analyze | — |
| 2. Categorize | **Early exit if nothing to test** |
| 3. Discover Patterns | — |
| 4. Baseline Coverage | — |
| 5. Design | — |
| 6. Write | — |
| 7. Run | **All tests pass** |
| 8. Measure Coverage | — |
| 9. Report & Approve | **User approves before commit** |
