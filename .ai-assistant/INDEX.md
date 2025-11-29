# Documentation Index

> Quick lookup for patterns, errors, and topics across all AI instruction files.

---

## By Topic

### Project Structure
- **Monorepo structure** -> [.memory.md](./.memory.md#project-structure)
- **File locations** -> [.context.md](./.context.md#file-locations)
- **Architecture decisions** -> [decisions/](./decisions/)

### TypeScript
- **Avoid `any` type** -> [typescript.instructions.md](./domains/typescript.instructions.md#avoid-any-type)
- **`satisfies` vs `as`** -> [typescript.instructions.md](./domains/typescript.instructions.md#use-satisfies-instead-of-as)
- **Named exports only** -> [typescript.instructions.md](./domains/typescript.instructions.md#named-exports-only)
- **Type guards** -> [typescript.instructions.md](./domains/typescript.instructions.md#type-guards)
- **Utility types** -> [typescript.instructions.md](./domains/typescript.instructions.md#utility-types)

### Testing
- **Test plan format (Gherkin)** -> [testing.instructions.md](./domains/testing.instructions.md#test-plan-format)
- **Testing Library queries** -> [testing.instructions.md](./domains/testing.instructions.md#testing-library-queries)
- **Mocking patterns** -> [testing.instructions.md](./domains/testing.instructions.md#mocking)
- **Test execution commands** -> [.context.md](./.context.md#test-execution)

### Git & Workflow
- **Branch naming** -> [.memory.md](./.memory.md#branch-naming)
- **Commit message format** -> [.memory.md](./.memory.md#commit-message-format)

---

## By Common Error

### Type Errors
**Cause:** TypeScript type mismatch
**Solution:** Check types, use proper assertions
**Reference:** [typescript.instructions.md](./domains/typescript.instructions.md)

### Test Failures
**Cause:** Missing setup, environment differences
**Solution:** Check test isolation, mock dependencies
**Reference:** [testing.instructions.md](./domains/testing.instructions.md)

---

## By Pattern

### Data Patterns
- **Type guards** -> `function isType(value: unknown): value is Type`
- **Discriminated unions** -> `type Result = { success: true; data: T } | { success: false; error: string }`

### Testing Patterns
- **Test plan** -> Gherkin format at top of test file
- **Scoped tests** -> `npm run test -- ComponentName`

---

## Quick Command Reference

### Test Commands
```bash
npm run test -- ComponentName     # Component tests
npm run test:unit -- pattern      # Unit tests
npm run typecheck                 # Type check
```

### Development Commands
```bash
npm run dev       # Dev server
npm run lint      # Lint all
npm run format    # Format code
```

---

## Navigation

**Entry Point:** [.instructions.md](./.instructions.md)

**Core Documentation:**
- [.memory.md](./.memory.md) - Architecture & patterns
- [.context.md](./.context.md) - Quick reference

**Domain Guidelines:**
- [typescript.instructions.md](./domains/typescript.instructions.md)
- [testing.instructions.md](./domains/testing.instructions.md)

**Workflows:**
- [validate.prompt.md](./workflows/validate.prompt.md)
- [refactor.prompt.md](./workflows/refactor.prompt.md)
- [create-todo.prompt.md](./workflows/create-todo.prompt.md)
- [create-file-list.prompt.md](./workflows/create-file-list.prompt.md)

**Decisions:**
- [decisions/](./decisions/) - Architecture Decision Records

---

**Tip:** Use Ctrl+F to search this index for keywords.
