---
chatmode: [developer, tester]
priority: high
---

# Validate

> **Chatmode:** Use developer or tester mode before running this workflow

Run validation checks to ensure code quality and correctness. Choose the appropriate scope based on your needs.

## Validation Scopes

### Quick Validation (Current Work)

Use during development to validate only what you've changed. Fast feedback loop.

```bash
/validate
```

### Full Validation (CI Pipeline)

Use before pushing to verify all CI checks will pass. Runs complete test suite.

```bash
/validate --full
```

---

## Quick Validation

Run validation checks on current work only, stopping if any level fails.

### Level 1: Syntax & Style

Type checking and linting - catches syntax errors and style violations.

```bash
# Type checking (adapt to your project)
npm run typecheck

# Linting
npm run lint
```

**Expected result:** No type errors, no lint errors.

### Level 2: Scoped Tests

Run tests for changed components/libraries only (never full test suite).

```bash
# For a specific component
npm run test -- ComponentName

# For a specific test file
npm run test -- file.spec

# For a directory
npm run test -- "src/components/"
```

**Expected result:** All tests pass, no failures.

### Level 3: Integration (Optional)

Manual verification of complete user flows when applicable.

```bash
# Start dev server
npm run dev

# Then manually test the feature in the browser
```

**Expected result:** Feature works as expected in actual UI.

### Smart Scoping

Determine what to validate based on the work done:

- **Component changes:** Type check + tests for that component
- **Utility changes:** Type check + unit tests for that utility
- **Multiple components in same directory:** Type check + directory tests
- **Configuration changes:** Full type check + subset of tests

---

## Full Validation (CI Pipeline)

Run the complete CI verification pipeline locally before pushing.

### Step 1: Type Checking

```bash
npm run typecheck
```

### Step 2: Linting

```bash
npm run lint
```

### Step 3: Unit Tests

```bash
npm run test
```

### Step 4: Build

```bash
npm run build
```

**Note:** Full validation runs the complete test suite - expect it to take several minutes.

---

## Common Issues

### Type Errors

- Check imports - are paths correct?
- Check prop types - do they match component definition?
- Check return types - does function return what it claims?

### Lint Errors

- Most can be auto-fixed: `npm run lint -- --fix`
- Unused imports/variables should be removed
- Follow eslint rule guidance

### Test Failures

- Read error message carefully
- Check if test data is set up correctly
- Verify mocks are configured properly
- Check for timing issues with async tests

### Build Errors

- Usually caused by unresolved type errors
- Check for circular dependencies
- Verify all imports resolve

---

## Output Format

Report validation results clearly:

```markdown
## Validation Results (Quick)

Level 1: Syntax & Style - PASSED
  - Type checking: No errors
  - Linting: No errors

Level 2: Scoped Tests - PASSED
  - ComponentName: 3 tests, all passed
```

For full validation:

```markdown
## CI Verification Results

Step 1: Type Checking - PASSED
Step 2: Linting - PASSED
Step 3: Unit Tests - PASSED (X tests)
Step 4: Build - PASSED

---
**All CI checks passed** - Ready to push
```

If validation fails:

```markdown
Level 2: Scoped Tests - FAILED
  - ComponentName: 2/3 tests passed
  - Failed: "validates user input"
  - Error: Expected validation error, got none
  - Cause: Missing validation logic
  - Fix: Added required field validation
```

## Notes

- **Quick validation:** Use during development for fast feedback
- **Full validation:** Use before pushing to ensure CI will pass
- **Run incrementally:** Fix level 1 before running level 2
- **Report clearly:** User needs to know what passed and what failed
- **Suggest fixes:** Don't just report errors, explain how to fix them
