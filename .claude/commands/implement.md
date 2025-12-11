---
description: Full implementation workflow - explore, plan, code, commit
---

# Implement

Follow **[implement.prompt.md](../../.ai-assistant/workflows/implement.prompt.md)** for: $ARGUMENTS

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Focus on specific files/directories |
| `--uncommitted` | Build on current uncommitted changes |
| `--branch=<name>` | Branch context |
| `--project=<path>` | Project root (monorepos) |

**Examples:**
```
/implement --files=src/auth/ add password validation
/implement --uncommitted finish login feature
```

## Phases

1. **Explore** - Parse scope, read and understand relevant code
2. **Plan** - Create detailed plan → **wait for your approval**
3. **Code** - Implement the approved plan (within scope)
4. **Cover** - Write tests for changed code
5. **Validate** - Run typecheck, lint, security scan, build
6. **Document** - *(optional)* Add docs for complex implementations
7. **Sync** - *(optional)* Update AI documentation (.memory.md, .context.md)
8. **Commit** - Show changes → **wait for your confirmation**

I will pause at each gate for your input. Scope carries through all phases.
