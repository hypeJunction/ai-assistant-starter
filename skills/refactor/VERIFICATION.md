# Refactor Skill Verification

## Scenario: Cross-Codebase Class Rename

**Trigger:** `/refactor rename UserService to AccountService`

**Setup:** A developer needs to rename the `UserService` class to `AccountService` across the codebase. The class is used in 12 files across `src/services/`, `src/api/`, and `src/tests/`. Some files import it as a type, others instantiate it. There is also a `userService` variable name used in 8 files. The source file is named `user.service.ts`.

**Expected Outcome:** All 12 files updated with class rename, all 8 files updated with variable rename, imports updated, file `user.service.ts` renamed to `account.service.ts`, tests pass, no broken references remain.

---

## Key Checkpoints

### 1. Scope Detection

Agent detects that the rename affects 12+ files and routes to `/refactor` (not `/implement`, which handles fewer than 6 files).

**Pass:** Agent identifies this as a medium-scope refactor (6-20 files) and proceeds with batched execution.
**Fail:** Agent treats this as a small change and applies all edits at once without batching.

### 2. Complete Reference Discovery

Agent discovers ALL references to the old names:
- `UserService` class name (12 files)
- `userService` variable name (8 files)
- `user.service.ts` file name
- Import paths referencing `user.service`
- Type references (`type X = UserService`, `implements UserService`, `: UserService`)

**Pass:** Agent presents a pattern analysis showing all categories of references with accurate counts.
**Fail:** Agent misses variable name references, file rename, or type-only imports.

### 3. Tracking Manifest

Agent creates a tracking manifest listing every affected file, grouped by reference type.

**Pass:** Manifest includes file paths, reference types (class, variable, import, type), and occurrence counts.
**Fail:** Agent starts editing without a complete inventory of affected files.

### 4. Logical Batch Grouping

Agent groups changes into dependency-ordered batches:
1. Type definitions and interfaces first (catches downstream breakage early)
2. Implementation files second (service files, API handlers)
3. Test files last (tests verify the refactoring works)

**Pass:** Agent presents batches ordered by dependency layer and explains the ordering rationale.
**Fail:** Agent groups files randomly, or applies changes to tests before implementations.

### 5. Plan Approval Gate

Agent presents the full refactoring plan with batch grouping, before/after examples, and edge cases. Waits for explicit user approval.

**Pass:** Agent shows the plan summary per `references/refactor-templates.md` and does not proceed until approved.
**Fail:** Agent begins modifying files before the user approves the plan.

### 6. Batched Execution with Intermediate Typechecks

Agent applies changes batch by batch (max 5 files per batch). Runs typecheck after each batch. Reports progress between batches.

**Pass:** Each batch is followed by a typecheck. Agent reports which files were changed and whether the typecheck passed.
**Fail:** Agent applies all changes in one pass, or skips typechecks between batches.

### 7. File Rename Handling

Agent renames `user.service.ts` to `account.service.ts` and updates all import paths that reference the old file name.

**Pass:** File is renamed, all imports pointing to `user.service` are updated to `account.service`, typecheck passes.
**Fail:** Agent renames the class inside the file but does not rename the file itself, or renames the file but misses import path updates.

### 8. Remaining Reference Check

After all batches complete, agent greps for the old names (`UserService`, `userService`, `user.service`) to verify no references remain.

**Pass:** Agent runs a search and reports zero remaining references (or explains any intentional exceptions like comments or documentation).
**Fail:** Agent skips the remaining-reference check and proceeds directly to validation.

### 9. Full Validation

Agent runs the complete validation suite: typecheck, lint, and tests.

**Pass:** All three checks pass. Agent presents the verification report per `references/refactor-templates.md`.
**Fail:** Agent skips lint or runs only a subset of tests.

### 10. Completion Report

Agent presents a completion report listing all changed files, the file rename, and validation results.

**Pass:** Report includes file count, list of modified files, batch summary, and test results.
**Fail:** Agent commits without presenting a summary of what changed.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Rename in random order (not batched by dependency layer) | Type errors compound — changing tests before types means intermediate typechecks are meaningless |
| Skip the file rename (`user.service.ts` stays as-is) | File name contradicts the class name, confusing future developers |
| Miss variable name references (`userService` unchanged) | Inconsistent naming — class is `AccountService` but instances are still `userService` |
| Apply all changes without intermediate typechecks | A single mistake in an early file cascades into dozens of errors, making it hard to isolate the problem |
| Proceed without checking for remaining old references | Stale references in string literals, comments, or dynamic imports cause runtime failures |
| Mix refactor with behavior changes in the same commit | Violates Iron Law 1 — refactoring changes structure, not behavior |

---

## Known Gaps

These gaps in the current skill are addressed by improvements to `SKILL.md`:

1. **No phased refactor guidance** — The skill did not specify the order in which to apply changes across dependency layers (types first, then implementations, then tests). Now addressed in Phase 4 of SKILL.md.
2. **No batch grouping strategy** — The skill required batches of max 5 files but did not guide how to group them logically. Now addressed in Phase 4 of SKILL.md.
3. **No "Introduce Abstraction Layer" pattern** — For cases where a direct rename is unsafe (public API surface, published packages, high coupling), the skill lacked guidance on introducing an adapter or re-export layer to make the migration incremental. Now addressed in Phase 3 of SKILL.md.
