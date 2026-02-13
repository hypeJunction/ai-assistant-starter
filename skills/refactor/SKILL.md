---
name: refactor
description: Systematic multi-file refactoring with pattern analysis, scope detection, batched execution, and progress tracking. Use for renames, pattern changes, API migrations, or any change affecting 6+ files.
triggers:
  - rename
  - restructure
  - reorganize
  - pattern change
  - large-scale change
  - multi-file change
---

# Refactor

> **Purpose:** Systematic refactoring with planning, pattern detection, and batched execution
> **Phases:** Gather Context → Pattern Analysis → Plan → Execute → Validate → Commit
> **Usage:** `/refactor [scope flags] <refactor description>`

## Iron Laws

1. **NO BEHAVIOR CHANGE WITHOUT APPROVAL** — Refactoring changes structure, not behavior. If the refactor would change what the code does, stop and confirm.
2. **ALL EXISTING TESTS MUST PASS** — After every batch, run tests. If tests fail, the refactor introduced a bug.
3. **BATCH AND VERIFY** — Never change more than 5 files without verifying. Large refactors are done in small, verified increments.
4. **REVERT ON FAILURE** — If a batch breaks tests, revert the entire batch rather than debugging individual changes. Start fresh with a corrected approach.

## When to Use

- Renaming functions, variables, or types across the codebase
- Migrating from one API/pattern to another
- Restructuring directories or modules
- Any change affecting 6+ files

## When NOT to Use

- Changing behavior (adding features) → `/implement`
- Fixing a bug → `/debug`
- 1-5 file changes → `/implement`
- Emergency fix → `/hotfix`

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Gate Enforcement

See `ai-assistant-protocol` for valid approval terms and invalid responses.

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Limit refactor to specific files/directories |
| `--project=<path>` | Project root for monorepos |

---

## Phase 1: Gather Context

### Step 1.1: Clarify Requirements

Ask: (1) What pattern/code needs to change? (2) Target state? (3) Why? (4) Areas to exclude?

**Wait for user response before exploring code.**

### Step 1.2: Explore and Categorize

Determine refactor type, file count, risk level:

| Scope | Files | Risk | Approach |
|-------|-------|------|----------|
| Small | 1-5 | Low | Direct changes |
| Medium | 6-20 | Medium | Batched with testing |
| Large | 21-50 | High | Phased with checkpoints |
| Massive | 50+ | Critical | Multiple phases |

**Wait for confirmation.**

---

## Phase 2: Pattern Analysis

### Step 2.1: Find All Occurrences

Search for all instances of the pattern. Present findings (see `references/refactor-templates.md` — Pattern Analysis).

### Step 2.2: Surface Edge Cases

Present edge cases for discussion. **Wait for user guidance.**

---

## Phase 3: Plan

Present the refactor plan summary (see `references/refactor-templates.md` — Plan Summary).

**GATE: Do NOT begin modifying files until user approves.**

---

## Phase 4: Execute

### Step 4.1: Create Git Savepoint

Before starting any changes:

```bash
git stash push -m "savepoint: before refactor" --include-untracked 2>/dev/null; git stash pop 2>/dev/null
```

Or ensure all current work is committed so you can revert cleanly.

### Step 4.2: Execute in Batches (max 5 files per batch)

For each batch:
1. Apply changes
2. Run typecheck
3. Run affected tests
4. Report progress

**If tests fail after a batch:** Revert the batch (`git checkout -- [affected-files]`), reassess the approach, and try again with a corrected strategy. Do not debug individual file changes within a broken batch.

### Step 4.3: Handle Discrepancies

If a file doesn't match expected patterns, present discrepancy report. **Wait for user decision.** Don't force the change.

---

## Phase 5: Validate

```bash
npm run typecheck
npm run lint
npm run test -- {affected-pattern}
npm run test  # Full suite for large refactors
```

### Test Updates Required

- Renamed public API → Update test references
- Changed signatures → Update calls and mocks
- Moved code → Update import paths
- Internal restructure → Existing tests should suffice

Present verification report (see `references/refactor-templates.md` — Verification Report).

**GATE: All tests must pass before proceeding.**

---

## Phase 6: Commit

Present commit message. Refactoring commits should use `refactor:` type and clearly describe what changed structurally.

Keep refactoring commits separate from feature commits. Never mix refactoring and behavior changes in the same commit.

**GATE: Wait for explicit confirmation.**

---

## Principles

1. **Ask, don't assume** — Clarify requirements and edge cases
2. **Get approval before executing** — Never refactor without explicit approval
3. **Preserve behavior** — Refactors should not change functionality
4. **Surface issues early** — Report discrepancies, don't silently skip
5. **Revert freely** — Failed batches get reverted, not debugged
6. **Confirm before committing** — User verification required

## Quick Reference

| Phase | Gate |
|-------|------|
| 1. Gather Context | User confirms scope |
| 2. Pattern Analysis | User guides edge cases |
| 3. Plan | **User approves** |
| 4. Execute | Tests pass per batch |
| 5. Validate | **All tests pass** |
| 6. Commit | **User confirms** |

## References

- [Refactor Templates](references/refactor-templates.md) — Display templates for plan summaries, batch progress, discrepancy reports, verification reports, and commit messages
