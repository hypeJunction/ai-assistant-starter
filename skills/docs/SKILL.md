---
name: docs
description: Add or improve documentation for code. Use when code needs JSDoc comments, inline explanations, README files, or documentation updates.
category: meta
model: sonnet
effort: medium
triggers:
  - add documentation
  - needs docs
  - document this
  - JSDoc
  - README
---

# Docs

> **Purpose:** Add or improve documentation for code
> **Usage:** `/docs [scope flags] <description>`

## Iron Laws

1. **DOCUMENTATION ONLY** -- Do not change code behavior. If you spot a bug while documenting, note it — don't fix it.
2. **EXPLAIN THE WHY** -- Self-evident code needs no comment. When you do comment, explain the reasoning, not the mechanics.
3. **DO NOT GUESS INTENT** -- If you're unsure why code exists or what it does, ask. Wrong documentation is worse than no documentation.

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## When to Use

- Exported functions or classes lack JSDoc
- Complex algorithms or business logic need explanation
- A package or module has no README
- Public APIs need usage examples
- After implementing a feature that changes the API surface

## When NOT to Use

- Adding test coverage for code -> `/test-coverage`
- Exploring code to understand it -> `/explore`
- Recording an architecture decision -> `/adr`
- Documenting deferred work or tech debt -> `/add-todo`
- Writing a full project README from scratch -> `/init`

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Document only specified files/directories |

**Examples:**
```bash
/docs --files=src/utils/       # Document all utils
/docs --files=src/api/client.ts  # Document specific file
/docs add JSDoc to exported functions
```

## Workflow

### Step 1: Identify Documentation Scope

Determine what needs documentation:

```bash
# Find files without JSDoc comments
# Look for exported functions/classes

# Check for missing README files
find . -type d -name "src" -exec test ! -f {}/README.md \; -print
```

**Target areas:**
- Exported functions and classes
- Complex algorithms or business logic
- Public APIs and interfaces
- Package/module entry points

**If all exported functions, classes, and interfaces already have complete, accurate JSDoc:** Report "Documentation is complete — no changes needed" and exit.

### Step 2: Analyze Code Purpose

Before documenting, understand:
- What does this code do?
- Why does it exist?
- How is it used?
- What are the edge cases?

Read the implementation and any existing tests to understand behavior.

**Finding test files:** Look for tests in common locations:
- `__tests__/` directory adjacent to the source file
- `.spec.ts` or `.test.ts` suffix next to the source file
- `tests/` directory at the project root

### Step 3: Add Documentation

**For Functions (JSDoc):**
```typescript
/**
 * Brief description of what the function does.
 *
 * @param paramName - Description of the parameter
 * @returns Description of the return value
 * @throws {ErrorType} Description of when this error is thrown
 *
 * @example
 * ```typescript
 * const result = functionName(input);
 * ```
 */
export function functionName(paramName: Type): ReturnType {
  // ...
}
```

**For Classes:**
```typescript
/**
 * Brief description of the class purpose.
 *
 * @example
 * ```typescript
 * const instance = new ClassName(config);
 * instance.method();
 * ```
 */
export class ClassName {
  // ...
}
```

**For Interfaces and Type Aliases:**
```typescript
/**
 * Brief description of the interface purpose.
 * Explain when this type is used and any important constraints.
 *
 * @example
 * ```typescript
 * const config: InterfaceName = { key: 'value' };
 * ```
 */
export interface InterfaceName {
  /** Description of this property */
  propertyName: Type;
}
```

**For Complex Logic (Inline Comments):**
```typescript
// Explain WHY, not WHAT
// Good: "Skip validation for internal calls to avoid circular dependency"
// Bad: "Check if internal is true"
if (isInternal) {
  return data;
}
```

**For Modules/Packages (README.md):**
```markdown
# Module Name

Brief description of module purpose.

## Usage

\`\`\`typescript
import { something } from './module';
\`\`\`

## API

### `functionName(param)`

Description of the function.
```

### Step 4: Documentation Standards

**Do:**
- Explain the "why" behind decisions
- Include usage examples
- Document edge cases and gotchas
- Keep descriptions concise but complete
- Use consistent terminology

**Don't:**
- State the obvious ("Increments counter by 1")
- Document implementation details that may change
- Add comments to self-explanatory code
- Use vague descriptions ("Handles stuff")

### Step 4.5: Confirm Documentation Changes

Present a summary of planned documentation changes before applying:

```markdown
## Planned Documentation Changes

| File | Change |
|------|--------|
| `src/services/payment.service.ts` | Add JSDoc to `processPayment()`, `getPaymentStatus()` |
| `src/services/payment.service.ts` | Update stale JSDoc on `refundPayment()` |
| `src/services/payment.service.ts` | Add interface docs for `PaymentConfig` |

**Apply these changes?** (yes / edit / cancel)
```

**GATE: User must approve documentation plan before changes are applied.**

### Step 5: Verify Documentation

After adding documentation:
- Ensure examples compile/work
- Check for spelling/grammar
- Verify accuracy against implementation
- Run type check to catch JSDoc type issues

```bash
npm run typecheck
```

### Step 6: Present Documentation Report

Present the documentation report using the Output Format defined below. Include what was added, updated, and skipped.

## Rules

### Prohibited

- **Do not add noise documentation** -- Comments that restate the obvious
- **Do not document every line** -- Only add value where needed
- **Do not guess at intent** -- Ask if unclear about purpose

### Required

- **JSDoc for exported functions** -- Public API must be documented
- **Examples for complex usage** -- Show how to use non-obvious APIs
- **README for packages** -- Each package/module should have one

### Recommended

- **Document edge cases** -- What happens with null, empty, etc.
- **Link related code** -- Reference related functions or modules
- **Update stale docs** -- Fix outdated documentation when found

## Output Format

Report what was documented:

```markdown
## Documentation Report

### Files Updated
- `src/utils/parser.ts` - Added JSDoc to 3 functions
- `src/services/api.ts` - Added module description
- `src/components/README.md` - Created package README

### Documentation Added
- `parseConfig()` - Function description, params, return, example
- `ApiService` - Class description, usage example
- `src/components/` - README with usage and API docs

### Notes
- `legacyHandler()` - Skipped, marked for deprecation
- Consider adding architecture docs for data flow
```

## Quick Reference

### JSDoc Tags

| Tag | Purpose | Example |
|-----|---------|---------|
| `@param` | Parameter description | `@param name - User's display name` |
| `@returns` | Return value | `@returns The parsed configuration` |
| `@throws` | Exceptions | `@throws {Error} If config is invalid` |
| `@example` | Usage example | See code block examples above |
| `@deprecated` | Mark as deprecated | `@deprecated Use newFunction instead` |
| `@see` | Reference related | `@see parseConfig` |

### Documentation Checklist

- [ ] Exported functions have JSDoc
- [ ] Complex logic has explanatory comments
- [ ] Public APIs have examples
- [ ] Packages have README files
- [ ] Edge cases are documented
- [ ] Examples are accurate and tested

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| DOC-T1 | Positive | "Add JSDoc to this file" | Skill triggers |
| DOC-T2 | Positive | "Document the public API" | Skill triggers |
| DOC-T3 | Positive | "This module needs a README" | Skill triggers |
| DOC-T4 | Negative | "Add tests for this code" | Does NOT trigger (-> /test-coverage) |
| DOC-T5 | Negative | "How does this work?" | Does NOT trigger (-> /explore) |
| DOC-T6 | Negative | "Record why we chose this approach" | Does NOT trigger (-> /adr) |
| DOC-T7 | Boundary | "Explain this function" | Context-dependent — if user wants docs added, trigger; if exploring to understand, route to /explore |
| DOC-T8 | Positive | `/docs --files=src/services/payment.service.ts` | Skill triggers, scopes to the specified file |
| DOC-T9 | Positive | "Update the stale JSDoc on this function" | Skill triggers — stale doc update is in scope |
| DOC-T10 | Positive | "Document this interface" | Skill triggers — interface documentation is in scope |
| DOC-T11 | Negative | "Document this private helper" | Does NOT document — private/non-exported helpers are out of scope |
| DOC-T12 | Boundary | "Add @throws tags to error-throwing functions" | Skill triggers — @throws documentation is in scope |
| DOC-T13 | Early-exit | All exports already have complete JSDoc | Reports "Documentation is complete — no changes needed" and exits |
