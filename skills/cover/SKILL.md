---
name: cover
description: Analyze branch changes and ensure adequate test coverage. Creates missing tests with test plans, runs them, and reports results. Use after implementing changes to add tests.
---

# Cover

> **Purpose:** Ensure test coverage for changed code
> **Usage:** `/cover`

## Constraints

- Create test files (`.spec.ts`, `.test.ts`) freely
- Do not modify non-test source files without approval
- Do not run full test suites unless necessary — scope tests to changes
- Do not test type definitions or config files
- Every test file MUST include a test plan as a comment

## Workflow

### Step 1: Analyze Current Changes

```bash
MAIN_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')

git status --short
git log --oneline $MAIN_BRANCH..HEAD
git diff --name-only $MAIN_BRANCH..HEAD
```

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

### Step 4: Write Missing Tests

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

### Step 5: Run and Verify Tests

```bash
npm run test -- path/to/file.spec.ts     # Single file
npm run test -- "src/utils/"              # Directory
```

### Step 6: Fix Failures and Re-run

Common issues:
- Missing mocks for dependencies
- Incorrect assertions
- Missing `await` for async operations
- Test isolation issues (shared state)

### Step 7: Report Results

```markdown
## Test Coverage Report

### Changed Files Analyzed
- X TypeScript utilities
- Y existing test files
- Z files not requiring tests

### Tests Created
- ✅ utility.spec.ts - 8 tests, all passing
- ✅ service.spec.ts - 5 tests, all passing

### Tests Verified
- ✅ existingUtil.spec.ts - passing

### Skipped (No Tests Needed)
- types.ts - type definitions only
- config.ts - configuration file

### Issues Found
- ⚠️ [any issues discovered during testing]
```

## Test File Locations

| Source File | Test File |
|-------------|-----------|
| `src/utils/foo.ts` | `src/utils/foo.spec.ts` |
| `src/services/bar.ts` | `src/services/bar.spec.ts` |
| `libs/core/src/baz.ts` | `libs/core/src/baz.spec.ts` |
