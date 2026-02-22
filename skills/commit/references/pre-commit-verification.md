# Pre-Commit Verification

Verification requirements that must be satisfied before claiming changes are ready to commit. The core principle: **evidence must be fresh, not remembered.**

## Verification by Change Tier

| Tier | Scope | Required Verification |
|------|-------|----------------------|
| **nano** | 1-2 files, <20 lines | Security scan |
| **small** | 2-4 files, <100 lines | Security scan + typecheck |
| **medium** | 5-10 files, 100-500 lines | Security scan + typecheck + lint + affected tests |
| **large** | 10+ files, 500+ lines | Security scan + typecheck + lint + full test suite + build |

### What Each Check Validates

| Check | What It Catches | Not Caught By |
|-------|----------------|---------------|
| **Security scan** | Hardcoded secrets, `eval()`, `innerHTML` with user data | Everything else |
| **Typecheck** | Type errors, missing imports, wrong argument types | Runtime logic errors |
| **Lint** | Style violations, unused variables, common mistakes | Type errors, logic errors |
| **Tests** | Behavioral regressions, logic errors | Missing test coverage |
| **Build** | Module resolution, bundling issues, env variable references | Tests, types (usually caught earlier) |

No single check is sufficient. Each catches a different class of problem.

## Evidence Requirements

### The Freshness Rule

Evidence is only valid if it was produced **after the last file modification** in the current interaction.

**Valid evidence:**
```
[edit file] → [run typecheck] → [show output] → [claim it passes]
✓ Fresh: command ran after the edit
```

**Invalid evidence:**
```
[run typecheck] → [edit file] → [claim it passes because it passed before]
✗ Stale: the edit may have introduced new errors
```

```
[typecheck passed in a previous message] → [claim it still passes]
✗ Stale: can't reference prior runs as current evidence
```

### Output Requirements

For each verification step, the actual command output must be present in the current message:

```markdown
## Verification Evidence

**Typecheck:** `npm run typecheck`
```
✓ No errors found
```

**Lint:** `npm run lint`
```
✓ No warnings or errors
```

**Tests:** `npm run test -- src/auth/`
```
✓ 12 tests passed (0 failed, 0 skipped)
```
```

Don't summarize — show the actual output. If the output is too long, show the summary line (e.g., "12 passed, 0 failed").

## Rationalization Prevention

Common excuses for skipping verification, and why they're wrong:

| Rationalization | Why It's Wrong | What to Do |
|----------------|----------------|-----------|
| "Tests passed earlier" | File edits may have introduced regressions | Run tests again. Show fresh output. |
| "It's just a config change" | Config changes can break builds, tests, and deployments | Run the full verification for the tier. Config is code. |
| "Linter is clean" | Linter catches style issues, not type errors or logic bugs | Linter ≠ typecheck ≠ tests. Run all required checks. |
| "I only changed one line" | Single-line changes cause some of the hardest bugs | Verify. The smaller the change, the easier it is to verify — so verify. |
| "It's the same pattern as before" | Copy-paste bugs are real. Context differs between instances. | Verify independently. |
| "The types guarantee it" | TypeScript types prevent type errors, not logic errors | Types are necessary but not sufficient. Run tests. |
| "Build succeeded" | Build verifies compilation, not correctness | Build ≠ tests. Run both. |
| "It compiles, ship it" | Compilation is the lowest bar. It means the syntax is valid. | Run the full verification stack for the tier. |

## Branch Safety

### When on Main/Master

If committing directly to a protected branch:

1. **Warn explicitly:** "You're on `main`. This will commit directly to the main branch."
2. **Suggest alternatives:**
   - Create a feature branch: `git checkout -b feat/description`
   - Stash and switch: `git stash && git checkout -b feat/description && git stash pop`
3. **Wait for explicit confirmation** before proceeding

### When to Suggest a Feature Branch

| Situation | Recommendation |
|-----------|---------------|
| nano change on main | OK to commit directly (with warning) |
| small change on main | Suggest branch, accept if user says "just commit" |
| medium/large change on main | Strongly recommend branch + PR |
| Any change with failing CI | Do NOT commit. Fix first. |
| Uncommitted work from another task | Stash first, then decide |

### When to Suggest Stash

```bash
# Current changes are unrelated to what you're about to commit
git stash push -m "WIP: [description of unrelated work]"
# ... make and commit the intended changes ...
git stash pop
```

Suggest stash when:
- `git status` shows changes in files unrelated to the commit scope
- The user asks to commit specific files but has other modifications
- Switching to a different task mid-stream
