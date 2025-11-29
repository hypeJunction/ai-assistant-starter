# AI Assistant Instructions

**Start here: [`.ai-assistant/.instructions.md`](.ai-assistant/.instructions.md)**

## Quick Commands

```bash
# Testing (customize for your project)
npm run test -- ComponentName    # Single component
npm run test:unit -- pattern     # Pattern match

# Validation
npm run typecheck                # Type check
npm run lint                     # Lint (read-only)

# Development
npm run dev                      # Dev server
npm run storybook                # Storybook (if applicable)
```

## Critical Rules

1. **Scoped tests only** - Never run full test suite unless explicitly requested
2. **Edit over create** - Always prefer editing existing files
3. **Follow existing patterns** - Match the style and structure of surrounding code
4. **Use project logger** - Never `console.log` in production code

## Common Gotchas

| Error | Cause | Fix |
|-------|-------|-----|
| Tests fail on CI but pass locally | Environment differences | Check test isolation |
| Type errors after refactoring | Stale types | Run type check incrementally |
| Linter errors | Style violations | Run `npm run lint:fix` |

## Navigation

**Context:** [INDEX.md](.ai-assistant/INDEX.md) | [.memory.md](.ai-assistant/.memory.md) | [.context.md](.ai-assistant/.context.md)

**Domains:** [TypeScript](.ai-assistant/domains/typescript.instructions.md) | [Testing](.ai-assistant/domains/testing.instructions.md)

**Workflows:** [Validate](.ai-assistant/workflows/validate.prompt.md) | [Refactor](.ai-assistant/workflows/refactor.prompt.md)
