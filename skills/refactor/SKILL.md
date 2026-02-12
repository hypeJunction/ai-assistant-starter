---
name: refactor
description: Systematic multi-file refactoring with pattern analysis, scope detection, batched execution, and progress tracking. Use for renames, pattern changes, API migrations, or any change affecting 6+ files.
---

# Refactor

> **Purpose:** Systematic refactoring with planning, pattern detection, and batched execution
> **Phases:** Gather Context -> Pattern Analysis -> Plan -> Execute -> Validate -> Docs -> Commit
> **Usage:** `/refactor [scope flags] <refactor description>`

## Gate Enforcement

**CRITICAL:** Refactoring affects multiple files. Mandatory approval gates at every phase.

**Valid approval:** `yes`, `y`, `approved`, `proceed`, `lgtm`, `go ahead`
**Invalid (NOT approval):** Silence, questions, "I see", "okay", "hmm"

**When in doubt:** Ask explicitly: "I need your approval to continue. Please respond with 'yes' to proceed."

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Limit refactor to specific files/directories |
| `--project=<path>` | Project root for monorepos |

**Examples:**
```bash
/refactor --files=src/components/ rename getUserData to fetchUser
/refactor --files=src/api/ migrate from axios to fetch
/refactor --project=packages/web update all imports to use new paths
```

## Constraints

- Full access to read, write, edit, and execute commands
- Get approval before starting any refactor
- Confirm approach for edge cases
- Stop and ask when encountering unexpected patterns -- don't force the change
- Track progress with file lists for changes affecting 5+ files

---

## Phase 1: Gather Context

**Goal:** Understand the refactor through conversation.

### Step 1.0: Parse Scope

```bash
git branch --show-current
git status --porcelain
```

### Step 1.1: Clarify Requirements

Ask: (1) What pattern/code needs to change? (2) Target state? (3) Why? (4) Areas to exclude?

**Wait for user response before exploring code.**

### Step 1.2: Explore and Categorize

Determine refactor type (`rename|restructure|pattern-change|api-migration|cleanup|type-improvement`), file count, risk level, and approach:

| Scope | File Count | Risk | Approach |
|-------|------------|------|----------|
| Small | 1-5 | Low | Direct changes |
| Medium | 6-20 | Medium | Batched with testing |
| Large | 21-50 | High | Phased with checkpoints |
| Massive | 50+ | Critical | Multiple phases |

**Wait for confirmation.**

---

## Phase 2: Pattern Analysis

**Goal:** Analyze patterns thoroughly and surface variations.

All output templates for this phase are in `references/refactor-templates.md`.

### Step 2.1: Find All Occurrences

Search for all instances of the pattern to be refactored.

### Step 2.2: Present Findings

Present pattern analysis findings (see `references/refactor-templates.md` -- Pattern Analysis: Findings).

### Step 2.3: Surface Edge Cases

Present edge cases for discussion (see `references/refactor-templates.md` -- Pattern Analysis: Edge Cases).

**Wait for user guidance on edge cases.**

---

## Phase 3: Plan Creation

**Goal:** Get user approval before making any changes.

### Step 3.1: Create Plan

Present the refactor plan summary (see `references/refactor-templates.md` -- Plan Summary).

**STOP HERE. Do NOT begin modifying files until user responds with explicit approval.**

---

## Phase 4: Execution

**Goal:** Implement with progress tracking and regular updates.

### Step 4.1: Track Progress

For medium+ refactors, maintain a progress tracker.

### Step 4.2: Execute in Batches

Report batch progress (see `references/refactor-templates.md` -- Batch Progress).

### Step 4.3: Handle Discrepancies

If a file doesn't match expected patterns, present discrepancy report (see `references/refactor-templates.md` -- Discrepancy Report).

**Wait for user decision.**

---

## Phase 5: Validation

**Goal:** Verify changes preserve behavior.

```bash
npm run typecheck
npm run lint
npm run test -- {affected-pattern}
npm run test  # Full suite for large refactors
```

### Test Coverage Check

Evaluate if refactor requires test updates:
- Renamed public API -> Update tests referencing old names
- Changed signatures -> Update calls and mocks
- Moved code -> Update import paths
- Internal restructure -> Existing tests should suffice

### Verification Report

Present verification report (see `references/refactor-templates.md` -- Verification Report).

**GATE: All tests must pass before proceeding.**

---

## Phase 6: Docs (Optional)

Prompt for documentation updates:
- `ai` -- Update AI assistant context (recommended for pattern changes)
- `user` -- User documentation
- `skip` -- No documentation

**Wait for response.**

---

## Phase 7: Commit

Present commit message (see `references/refactor-templates.md` -- Commit Message).

**STOP HERE. Wait for explicit confirmation.**

---

## Principles

1. **Ask, don't assume** -- Clarify requirements and edge cases
2. **Get approval before executing** -- Never refactor without explicit approval
3. **Preserve behavior** -- Refactors should not change functionality
4. **Surface issues early** -- Report discrepancies, don't silently skip
5. **All tests must pass** -- Update tests for renamed/moved code
6. **Confirm before committing** -- User verification required

## Quick Reference

| Phase | Key Action | Gate |
|-------|------------|------|
| 1. Gather Context | Ask questions, explore code | User confirms |
| 2. Pattern Analysis | Find variations, surface edge cases | User guides handling |
| 3. Plan | Design solution | **User approves** |
| 4. Execute | Batched changes with progress | User resolves issues |
| 5. Validate | Run all tests | **All tests pass** |
| 6. Docs | Update documentation | Optional |
| 7. Commit | Commit all changes | **User confirms** |

## References

- [Refactor Templates](references/refactor-templates.md) — Display templates for plan summaries, batch progress, discrepancy reports, verification reports, and commit messages
