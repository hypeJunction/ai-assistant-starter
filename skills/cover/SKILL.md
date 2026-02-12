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

- Writing tests before code → `/tdd`
- Debugging a test failure → `/debug`
- Full CI validation → `/validate`

## Constraints

- Create test files (`.spec.ts`, `.test.ts`) freely
- Do not modify non-test source files without approval
- Scope tests to changes — don't run full suites unless necessary
- Every test file MUST include a test plan as a comment

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Specific files/directories to cover |
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
MAIN_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git diff --name-only $MAIN_BRANCH..HEAD
```

### Step 2: Categorize and Identify Missing Coverage

| File Type | Test Type | Priority |
|-----------|-----------|----------|
| `*.ts` utilities/services | Unit tests (`.spec.ts`) | High |
| `*.tsx` components | Component tests | High |
| `*.ts` types/interfaces | Skip | — |
| Config/build files | Skip | — |

### Step 3: Design Test Plans

For each file needing tests:

```markdown
## Test Plan: [ModuleName]

| Function | Behaviors | Edge Cases |
|----------|-----------|------------|
| `functionA` | happy path, error path | null input, empty array |
```

### Step 4: Write Tests

**Required test plan (Gherkin) as comment:**
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

**Coverage priorities:** Happy path → Edge cases (null, empty, boundary) → Error conditions → Async operations

**For utilities with well-defined contracts**, consider property-based testing (e.g., with fast-check) to catch edge cases that example-based tests miss.

### Step 5: Run and Fix

```bash
npm run test -- path/to/file.spec.ts
```

If failures: fix mocks, assertions, missing `await`, or isolation issues. Re-run until green.

### Step 6: Report

```markdown
## Test Coverage Report

### Tests Created
- utility.spec.ts — 8 tests, all passing
- service.spec.ts — 5 tests, all passing

### Skipped (No Tests Needed)
- types.ts — type definitions only

### Test Quality Check
| Criterion | Status |
|-----------|--------|
| Independent | ✓ |
| Fast | ✓ |
| Focused | ✓ |
| Deterministic | ✓ |
```

## Quick Reference

| Phase | Gate |
|-------|------|
| 1. Analyze | — |
| 2. Categorize | — |
| 3. Design | — |
| 4. Write | — |
| 5. Run | **All tests pass** |
| 6. Report | — |
