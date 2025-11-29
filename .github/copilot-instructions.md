# GitHub Copilot Instructions

This file provides instructions for GitHub Copilot when working in this repository.

## Project Context

- **Project:** {{PROJECT_NAME}}
- **Type:** {{PROJECT_TYPE}}
- **Language:** TypeScript
- **Framework:** {{FRAMEWORK}}

For detailed project context, see [.ai-assistant/.memory.md](../.ai-assistant/.memory.md).

## Code Style

### TypeScript

- Use TypeScript strict mode
- Avoid `any` type - use proper types or `unknown`
- Prefer `satisfies` over `as` for type assertions
- Use named exports only (no default exports)
- Let TypeScript infer types when possible
- Prefer `undefined` over `null`

### Functional Patterns

- Prefer array methods (`map`, `filter`, `reduce`) over loops
- Avoid mutation - create new objects/arrays
- Use `const` by default, `let` only when necessary

### Error Handling

- Errors in catch blocks are `unknown` - use type guards
- Use proper error logging, not `console.log`

## Testing

### Test Plans

All test files should include a test plan at the top:

```typescript
/**
 * Test Plan: ComponentName
 *
 * Scenario: User can submit form
 *   Given the form is displayed
 *   When user fills required fields
 *   And clicks submit
 *   Then data is sent to server
 */
```

### Test Structure

- Use AAA pattern: Arrange, Act, Assert
- Or Given-When-Then for BDD style
- Keep tests focused and independent

## Documentation

- Code should be self-documenting
- Write comments only for non-obvious behavior
- Use JSDoc for public APIs

## Imports

Organize imports in this order:
1. External dependencies
2. Internal absolute imports
3. Relative imports

## Security

When generating code, avoid:
- XSS vulnerabilities
- SQL injection
- Command injection
- Hardcoded secrets

## Detailed Instructions

For comprehensive guidance, see:
- [.ai-assistant/.instructions.md](../.ai-assistant/.instructions.md) - Global rules
- [.ai-assistant/domains/typescript.instructions.md](../.ai-assistant/domains/typescript.instructions.md) - TypeScript patterns
- [.ai-assistant/domains/testing.instructions.md](../.ai-assistant/domains/testing.instructions.md) - Testing practices
