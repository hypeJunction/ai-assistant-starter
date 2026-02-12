---
name: naming-guidelines
description: Naming conventions for TypeScript including variables, functions, classes, files, and directories. Auto-loaded when writing or reviewing code.
user-invocable: false
---

# Naming Guidelines

## Core Principles

1. **Clarity over brevity** - Names should be self-explanatory
2. **Consistency** - Same concept, same name everywhere
3. **Searchability** - Names should be easy to find
4. **Context-aware** - Length proportional to scope
5. **No abbreviations** - Unless universally understood

## Case Conventions

### JavaScript/TypeScript

| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `userName`, `isActive` |
| Functions | camelCase | `getUserById`, `calculateTotal` |
| Classes | PascalCase | `UserService`, `HttpClient` |
| Interfaces | PascalCase | `UserProps`, `ApiResponse` |
| Types | PascalCase | `UserId`, `Status` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES`, `API_URL` |
| Enums | PascalCase | `UserRole`, `Status` |
| Enum values | PascalCase | `UserRole.Admin` |
| Files (components) | PascalCase | `UserProfile.tsx` |
| Files (utilities) | camelCase | `formatDate.ts` |
| Files (tests) | match source | `UserProfile.spec.ts` |

## Variables

Use descriptive names. Prefix booleans with `is`, `has`, `can`, `should`, `will`. Use plural names for collections. Include units for numbers (`timeoutMs`, `priceInCents`).

```typescript
// Good
const currentUser = getUser();
const isActive = true;
const hasPermission = user.role === 'admin';
const activeItems = items.filter(item => item.active);
const timeoutMs = 5000;

// Bad
const d = new Date();
const active = true;
const timeout = 5000; // Seconds? Milliseconds?
```

See `references/variable-naming.md` for full examples (booleans, collections, numbers, strings, abbreviations).

## Functions

Use verb + noun for actions, `get` + noun for getters, `is`/`has`/`can` for checkers, `handle`/`on` for events. Avoid generic names like `process`, `handle`, `getData`.

```typescript
// Good
function createUser(data: UserData): User { }
function getUserById(id: string): User | undefined { }
function isValidEmail(email: string): boolean { }
function handleSubmit(data: FormData): void { }

// Bad
function process(data: unknown) { }
function doStuff() { }
```

See `references/function-naming.md` for full patterns (transformers, event handlers, hooks).

## Classes & Types

Classes use PascalCase nouns. Interfaces describe what it is (no `I` prefix). Type aliases describe the concept.

```typescript
class UserService { }
interface UserProfileProps { }
type UserId = string;
type Status = 'pending' | 'active' | 'completed';
```

See `references/class-type-naming.md` for full examples (interfaces, type aliases, components).

## Files & Directories

Components use PascalCase, utilities use camelCase or kebab-case, tests match source file.

```typescript
UserProfile.tsx        // Component
formatDate.ts          // Utility
UserProfile.spec.tsx   // Test
```

See `references/file-directory-naming.md` for directory structure, CSS/BEM naming, environment variables.

## API Endpoint Naming

> **Note:** For comprehensive REST API naming conventions (plural nouns, kebab-case paths, query parameter styles), see the `rest-api-guidelines` skill.

## Gotchas

Avoid reserved words, variable shadowing, and inconsistent naming across the codebase. Pick one style and stick with it (`fetchUsers` vs `getUsers`, `onClick` vs `handleClick`).

See `references/naming-gotchas.md` for anti-patterns, reserved words, shadowing, and consistency rules.

## References

- `references/variable-naming.md` - Booleans, collections, numbers, strings, abbreviations, pronounceability
- `references/function-naming.md` - Action verbs, getters, checkers, transformers, event handlers, hooks
- `references/class-type-naming.md` - Classes, interfaces, type aliases, component naming
- `references/file-directory-naming.md` - File names, directory structure, CSS/BEM, environment variables
- `references/naming-gotchas.md` - Anti-patterns, reserved words, shadowing, consistency
