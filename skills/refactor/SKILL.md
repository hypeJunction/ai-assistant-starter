---
name: refactor
description: Systematic multi-file refactoring with pattern analysis, scope detection, batched execution, and progress tracking. Use for renames, pattern changes, API migrations, or any change affecting 6+ files.
---

# Refactor

> **Purpose:** Systematic refactoring with planning, pattern detection, and batched execution
> **Phases:** Gather Context → Pattern Analysis → Plan → Execute → Validate → Docs → Commit
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
- Stop and ask when encountering unexpected patterns — don't force the change
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

```markdown
## Understanding the Refactor

1. **What pattern/code needs to change?**
2. **What's the target state?**
3. **Why is this refactor needed?**
4. **Any areas to exclude?**
```

**Wait for user response before exploring code.**

### Step 1.2: Explore and Categorize

```markdown
## Initial Analysis

**Refactor Type:** {rename|restructure|pattern-change|api-migration|cleanup|type-improvement}

**Scope Assessment:**
- Files affected: {N}
- Risk level: {low|medium|high|critical}
- Approach: {direct|batched|phased}
```

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

### Step 2.1: Find All Occurrences

Search for all instances of the pattern to be refactored.

### Step 2.2: Present Findings

```markdown
## Pattern Analysis

**Total Occurrences:** {N} across {M} files

**Pattern Variations:**
| Variation | Count | Example | Notes |
|-----------|-------|---------|-------|
| Standard usage | 15 | `pattern()` | Normal refactor |
| With options | 5 | `pattern({ opt: true })` | Special handling |
| Edge case | 2 | `pattern?.()` | Optional chaining |
```

### Step 2.3: Surface Edge Cases

```markdown
## Edge Cases to Discuss

| Case | Files Affected | Question |
|------|----------------|----------|
| Conditional usage | `file1.ts` | Transform too? |
| Dynamic reference | `utils.ts` | Handle dynamic lookup? |
| Exported API | `index.ts` | Breaking change? |
| Test mocks | `*.spec.ts` | Update mocks? |
```

**Wait for user guidance on edge cases.**

---

## Phase 3: Plan Creation

**Goal:** Get user approval before making any changes.

### Step 3.1: Create Plan

```markdown
## Refactor Plan Summary

**What:** {brief description}
**Scope:** {N} files across {directories}
**Risk:** {level}

**Key Changes:**
1. Change A
2. Change B

**Before/After:**
\`\`\`typescript
// Before
oldPattern()

// After
newPattern()
\`\`\`

**Edge Cases:** {N} handled per discussion

---
**Proceed with this refactor?** (yes / modify / cancel)
```

**STOP HERE. Do NOT begin modifying files until user responds with explicit approval.**

---

## Phase 4: Execution

**Goal:** Implement with progress tracking and regular updates.

### Step 4.1: Track Progress

For medium+ refactors, maintain a progress tracker.

### Step 4.2: Execute in Batches

```markdown
## Progress Update

**Batch 1 of {N}:** Files 1-5
- ✓ `file1.ts` - transformed
- ✓ `file2.ts` - transformed

**Validation:** Type check passed

**Next:** Batch 2 (files 6-10)

Any concerns before I continue?
```

### Step 4.3: Handle Discrepancies

If a file doesn't match expected patterns:

```markdown
## Found Something Unexpected

**File:** `src/components/Special.ts`
**Expected:** `oldPattern()`
**Found:** `oldPattern.withConfig()`

**Options:**
1. **Skip** - Leave unchanged
2. **Transform** - Apply similar transformation
3. **Manual** - Flag for manual review

Which approach?
```

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
- Renamed public API → Update tests referencing old names
- Changed signatures → Update calls and mocks
- Moved code → Update import paths
- Internal restructure → Existing tests should suffice

### Verification Report

```markdown
## Refactor Complete

**Files Modified:** {N}
**Files Skipped:** {N} (with reasons)

| Check | Status |
|-------|--------|
| Type check | ✓ Pass |
| Lint | ✓ Pass |
| Tests | ✓ Pass ({N} tests) |

**Can you verify the refactor works as expected?**
```

**GATE: All tests must pass before proceeding.**

---

## Phase 6: Docs (Optional)

Prompt for documentation updates:
- `ai` — Update AI assistant context (recommended for pattern changes)
- `user` — User documentation
- `skip` — No documentation

**Wait for response.**

---

## Phase 7: Commit

```markdown
## Ready to Commit

**Message:**
\`\`\`
refactor: {title}

{Brief description}
\`\`\`

**Commit?** (yes / edit / cancel)
```

**STOP HERE. Wait for explicit confirmation.**

---

## Principles

1. **Ask, don't assume** — Clarify requirements and edge cases
2. **Get approval before executing** — Never refactor without explicit approval
3. **Preserve behavior** — Refactors should not change functionality
4. **Surface issues early** — Report discrepancies, don't silently skip
5. **All tests must pass** — Update tests for renamed/moved code
6. **Confirm before committing** — User verification required

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
