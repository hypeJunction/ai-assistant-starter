# Validation Troubleshooting

Common issues encountered during validation, organized by check type. Each issue includes the error pattern, likely cause, and fix.

## Type Errors

| Error Pattern | Likely Cause | Fix |
|---------------|--------------|-----|
| `Cannot find module 'X'` | Missing import or uninstalled dependency | Check import path; run `npm install` if dependency missing |
| `Type 'X' is not assignable to type 'Y'` | Type mismatch in assignment or function call | Fix the type (cast, widen, or correct the value) |
| `Property 'X' does not exist on type 'Y'` | Accessing undefined property | Add to interface, or check for typo |
| `Implicit 'any' type` | Missing type annotation with `strict: true` | Add explicit type annotation |
| `Object is possibly 'undefined'` | Nullable value used without check | Add null check or optional chaining (`?.`) |
| `Argument of type 'X' is not assignable to parameter of type 'Y'` | Wrong argument type in function call | Check function signature; transform the argument |
| `Cannot find name 'X'` | Variable not declared or imported | Add import or declaration |
| `No overload matches this call` | Wrong argument combination for overloaded function | Check available overloads in type definition |

### Type Error Resolution Strategy

1. **Start with the first error** — Later errors are often caused by earlier ones
2. **Check if it's an import issue** — Missing/wrong imports cause cascading errors
3. **Read the full error** — TypeScript errors include the expected and actual types
4. **Don't use `as any`** — Fix the root cause instead of casting

## Lint Errors

| Error Pattern | Likely Cause | Fix |
|---------------|--------------|-----|
| `'X' is defined but never used` | Unused import or variable | Remove it, or prefix with `_` if intentionally unused |
| `Unexpected any` | `any` type used (blocked by `@typescript-eslint/no-explicit-any`) | Use a specific type or `unknown` |
| `Missing return type on function` | Function lacks explicit return type | Add return type annotation |
| `Prefer const` | `let` used but never reassigned | Change `let` to `const` |
| `React Hook useEffect has missing dependencies` | Effect hook dependency array incomplete | Add missing deps, or restructure to avoid them |
| `'X' is already declared in the upper scope` | Variable shadows outer scope variable | Rename inner variable |
| `Unexpected console statement` | `console.log` in production code | Remove or use proper logging utility |
| `Import order violation` | Imports not sorted per convention | Run `--fix` or reorder manually |

### Auto-Fixable Lint Issues

These can be resolved with `npm run lint -- --fix`:
- Import ordering
- Trailing commas
- Semicolons
- Quotes (single vs double)
- Indentation
- Unused imports (with `eslint-plugin-unused-imports`)

These require manual fixes:
- `any` types
- Missing dependencies in hooks
- Unused variables (sometimes auto-fixable)
- Logic-related rules

## Test Failures

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Timeout | Async operation not awaited | Add `await`; increase timeout if legitimately slow |
| `Cannot find module` in test | Wrong import path or missing mock | Check paths; add `vi.mock()` if needed |
| Mock not called | Mock setup doesn't match actual call | Verify mock matches the actual import path |
| Snapshot mismatch | Intentional UI change | Update with `--update` flag after reviewing diff |
| `Expected X, received undefined` | Function returns nothing or wrong value | Check function implementation |
| `TypeError: X is not a function` | Wrong mock setup or missing export | Verify mock returns the right shape |
| Test passes alone, fails in suite | Shared state between tests | Add proper setup/teardown; check for global state |
| `ECONNREFUSED` | Test needs a running server | Use test server setup or mock HTTP calls |

### Test Failure Resolution Strategy

1. **Read the assertion error** — It tells you expected vs actual
2. **Run the single failing test** — Isolate from suite: `npm test -- -t "test name"`
3. **Check if it's a mock issue** — Most test failures are mock misconfigurations
4. **Check for async issues** — Missing `await` is the #1 cause of flaky tests

## Build Failures

| Error Pattern | Likely Cause | Fix |
|---------------|--------------|-----|
| `Module not found` | Missing dependency or wrong path in build config | Install dependency; check alias configuration |
| `SyntaxError: Unexpected token` | File not processed by correct loader/plugin | Check build config for file type handling |
| `Out of memory` | Build process exceeds Node.js memory limit | Increase with `NODE_OPTIONS=--max_old_space_size=4096` |
| `Circular dependency` | Module A imports B which imports A | Refactor to break the cycle; extract shared code |
| `Cannot resolve 'X'` | TypeScript path alias not configured in bundler | Add alias to build config (webpack, vite, etc.) |
| `Export 'X' was not found in 'Y'` | Named export missing or renamed | Check source module for the export |

## Format Errors

| Error Pattern | Likely Cause | Fix |
|---------------|--------------|-----|
| `File differs from Prettier formatting` | File not formatted | Run `npm run format` or `npx prettier --write [file]` |
| Trailing whitespace | Editor not configured | Enable "trim trailing whitespace" in editor |
| Mixed line endings (CRLF/LF) | Windows/Unix mismatch | Configure `.gitattributes` and editor settings |

## CI vs Local Discrepancies

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Passes locally, fails in CI | Different Node version | Match CI Node version locally (use `.nvmrc` or `volta`) |
| Tests timeout in CI only | CI is slower than local machine | Increase test timeouts; check for network-dependent tests |
| Lint passes locally, fails in CI | Different ESLint config or version | Check `package-lock.json` is committed and up-to-date |
| Build fails in CI only | Missing environment variable | Add to CI secrets/env configuration |
| Type check passes locally, fails in CI | Different TypeScript version or config | Ensure `tsconfig.json` is committed; lock TS version |
| Different test results | OS-specific behavior | Check for path separators (`/` vs `\`), case sensitivity |

### Resolving CI Discrepancies

1. **Check Node.js version** — `node --version` locally vs CI config
2. **Clean install** — Delete `node_modules` and `npm ci` (not `npm install`)
3. **Check environment** — Missing env vars, different OS, different architecture
4. **Check git state** — CI runs on the pushed commit, not your working tree
