---
name: cover
description: Analyze branch changes and ensure adequate test coverage. Creates missing tests with test plans, runs them, and reports results. Use after implementing changes to add tests.
---

# Cover

> **Purpose:** Ensure test coverage for changed code
> **Phases:** Analyze → Design → Write → Run → Report
> **Usage:** `/cover [scope flags]`

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

- Writing tests for code you haven't read yet -> `/explore` first
- Debugging a test failure -> `/debug`
- Full CI validation -> `/validate`
- Writing integration/E2E tests for API routes -> `/api-test`

## Constraints

- Create test files (`.spec.ts`, `.test.ts`) freely
- Do not modify non-test source files without approval
- Do not run full test suites unless necessary -- scope tests to changes
- Do not test type definitions or config files
- Every test file MUST include a test plan as a comment

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Specific files/directories to cover |
| `--branch=<name>` | Compare against specific branch (default: main) |
| `--uncommitted` | Cover only uncommitted changes |

**Examples:**
```bash
/cover                              # Cover all changes on current branch
/cover --files=src/utils/parser.ts  # Cover specific file
/cover --files=src/auth/            # Cover specific directory
/cover --branch=develop             # Compare against develop branch
```

---

## Test Quality Criteria

Every test written by this skill must meet ALL of the following:

| Criterion | Rule | Smell if Violated |
|-----------|------|-------------------|
| **Independent** | No shared mutable state between tests | Tests pass alone but fail together (or vice versa) |
| **Fast** | Mock external dependencies (DB, API, filesystem) | Test suite takes minutes instead of seconds |
| **Readable** | Clear Given/When/Then structure | Can't understand the test without reading the source |
| **Focused** | One behavior per test | Test name contains "and" |
| **Deterministic** | Same input always produces same output | Flaky tests that pass sometimes |

## Coverage Targets by File Type

| File Type | Target | Focus |
|-----------|--------|-------|
| Business logic / services | 80%+ | Edge cases, error paths |
| Utilities / helpers | 90%+ | All code paths |
| API routes / handlers | 70%+ | Happy path + error codes |
| UI components | 60%+ | User interactions, states |

## Don't Test

- **Types / interfaces** -- no runtime behavior to verify
- **Trivial getters/setters** -- one-line property access with no logic
- **Framework internals** -- React rendering, Express routing itself
- **Constants / enums** -- static values that never change
- **Generated code** -- Prisma client, GraphQL codegen, etc.

## Test Smell Detection

Before finalizing tests, check for these anti-patterns:

| Smell | Example | Fix |
|-------|---------|-----|
| **Testing implementation details** | Spying on internal private methods | Test the public API output instead |
| **Multi-concern tests** | Test name has "and" (e.g., "validates and saves") | Split into two focused tests |
| **Mirror tests** | Test structure mirrors implementation line-by-line | Test inputs/outputs, not internal steps |
| **No meaningful assertions** | Test only checks that no error was thrown | Assert on return values or side effects |
| **Testing the mock** | Assertions only verify mock was called correctly | Assert on the behavior the mock enables |

---

## Workflow

### Step 1: Analyze Current Changes

```bash
MAIN_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')

git status --short
git log --oneline $MAIN_BRANCH..HEAD
git diff --name-only $MAIN_BRANCH..HEAD
```

If `--files` flag was provided, scope analysis to those paths only.

### Step 2: Categorize Changed Files

| File Type | Test Type Needed | Priority |
|-----------|------------------|----------|
| `*.ts` utilities/services | Unit tests (`.spec.ts`) | High |
| `*.tsx` components | Component tests | High |
| `*.ts` types/interfaces | No tests needed | Skip |
| Config/build files | No tests needed | Skip |

### Step 3: Identify Missing Coverage

```bash
# For each .ts file (excluding tests), check for .spec.ts
for file in $(git diff --name-only $MAIN_BRANCH..HEAD | grep '\.ts$' | grep -v '\.spec\.' | grep -v '\.test\.'); do
  spec="${file%.ts}.spec.ts"
  if [ ! -f "$spec" ]; then
    echo "Missing spec: $file"
  fi
done
```

### Step 4: Design Test Plans

For each file needing tests, design a plan BEFORE writing code:

```markdown
## Test Plan: [ModuleName]

**Functions to test:**
| Function | Behaviors | Edge Cases |
|----------|-----------|------------|
| `functionA` | happy path, error path | null input, empty array |
| `functionB` | transform, validate | boundary values |

**Estimated tests:** N
```

### Step 5: Write Missing Tests

For each file needing tests, create a `.spec.ts` file with:

**Required test plan format (Gherkin):**
```typescript
/**
 * Test Plan: ModuleName
 *
 * Scenario: Brief description
 *   Given [initial state]
 *   When [action]
 *   Then [expected outcome]
 */
```

**Test structure:**
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

**Coverage priorities:**
- Happy path behavior
- Edge cases (null, empty, boundary values)
- Error conditions
- Async operations

### Step 6: Run and Verify Tests

```bash
npm run test -- path/to/file.spec.ts     # Single file
npm run test -- "src/utils/"              # Directory
```

### Step 7: Fix Failures and Re-run

Common issues:
- Missing mocks for dependencies
- Incorrect assertions
- Missing `await` for async operations
- Test isolation issues (shared state)

### Step 8: Report Results

```markdown
## Test Coverage Report

### Changed Files Analyzed
- X TypeScript utilities
- Y existing test files
- Z files not requiring tests

### Tests Created
- utility.spec.ts - 8 tests, all passing
- service.spec.ts - 5 tests, all passing

### Tests Verified
- existingUtil.spec.ts - passing

### Skipped (No Tests Needed)
- types.ts - type definitions only
- config.ts - configuration file

### Test Quality Check
| Criterion | Status |
|-----------|--------|
| Independent | All tests pass in isolation |
| Fast | Suite completes in < Ns |
| Readable | Given/When/Then structure used |
| Focused | No multi-concern test names |
| Deterministic | No flaky tests detected |

### Issues Found
- [any issues discovered during testing]
```

## Test File Locations

| Source File | Test File |
|-------------|-----------|
| `src/utils/foo.ts` | `src/utils/foo.spec.ts` |
| `src/services/bar.ts` | `src/services/bar.spec.ts` |
| `libs/core/src/baz.ts` | `libs/core/src/baz.spec.ts` |

## Quick Reference

| Phase | Action | Gate |
|-------|--------|------|
| 1. Analyze | Diff branch, list changed files | -- |
| 2. Categorize | Determine test types needed | -- |
| 3. Identify | Find missing test files | -- |
| 4. Design | Plan tests per file | -- |
| 5. Write | Create test files | -- |
| 6. Run | Execute tests | **All tests pass** |
| 7. Fix | Resolve failures | **All tests pass** |
| 8. Report | Summary with quality check | -- |
