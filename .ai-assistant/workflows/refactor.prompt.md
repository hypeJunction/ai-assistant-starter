---
chatmode: [developer, architect]
priority: high
---

# Workflow: Refactor Codebase

> **Purpose:** Systematic refactoring with proper planning, pattern detection, scope analysis, and parallel execution
> **Chatmode:** Use developer or architect mode before running this workflow
> **Prerequisites:** Clear understanding of what needs to be refactored
> **Related:** [create-file-list.prompt.md](./create-file-list.prompt.md) | [create-todo.prompt.md](./create-todo.prompt.md)

## Overview

This workflow guides systematic refactoring through:
1. Information gathering and clarification
2. Pattern analysis and edge case identification
3. Plan creation with full scope documentation
4. Parallel execution with progress tracking

---

## Phase 1: Information Gathering

### 1.1 Understand the Refactor Request

Ask clarifying questions to understand:

| Question | Purpose |
|----------|---------|
| **What pattern/code needs to change?** | Identify the target |
| **What is the new pattern/approach?** | Define the goal |
| **Why is this refactor needed?** | Understand motivation |
| **Are there any files/areas to exclude?** | Define boundaries |
| **Are there related refactors to coordinate?** | Avoid conflicts |

### 1.2 Categorize the Refactor

Determine the refactor type:

| Type | Description | Example |
|------|-------------|---------|
| `rename` | Renaming symbols (variables, functions, types, files) | `getData` -> `fetchUserData` |
| `restructure` | Moving code between files/directories | Move utilities to shared lib |
| `pattern-change` | Changing code patterns or conventions | Class -> functional components |
| `api-migration` | Updating to new API/library versions | v1 -> v2 API |
| `cleanup` | Removing dead code, unused imports, etc. | Remove deprecated functions |
| `type-improvement` | Improving TypeScript types | `any` -> proper types |

### 1.3 Assess Scope and Risk

| Scope | File Count | Risk Level | Approach |
|-------|------------|------------|----------|
| `small` | 1-5 files | Low | Direct changes |
| `medium` | 6-20 files | Medium | Batched changes with testing |
| `large` | 21-50 files | High | Phased approach with checkpoints |
| `massive` | 50+ files | Critical | Multiple phases, extensive testing |

---

## Phase 2: Pattern Analysis

### 2.1 Find All Occurrences

Search for all instances of the pattern to be refactored:

```bash
# Search for pattern occurrences
grep -r "pattern" src/

# Count occurrences
grep -r "pattern" src/ | wc -l
```

### 2.2 Analyze Pattern Variations

Identify different usages of the pattern:

| Variation | Count | Example | Special Handling |
|-----------|-------|---------|------------------|
| Standard usage | 15 | `pattern()` | Normal refactor |
| With options | 5 | `pattern({ opt: true })` | Update options |
| Edge case | 2 | `pattern?.()` | Handle optional chaining |

### 2.3 Identify Edge Cases

Look for situations that need special handling:

- **Conditional usage:** Pattern used inside conditionals
- **Dynamic usage:** Pattern constructed dynamically
- **External references:** Pattern exported/imported across packages
- **Test dependencies:** Pattern mocked in tests
- **Configuration:** Pattern referenced in config files

### 2.4 Ask Clarification Questions

If variations or edge cases are unclear, ask before proceeding:

```markdown
I found variations in how this pattern is used:

1. **Standard usage (15 files):** `oldFunction()`
2. **With callback (5 files):** `oldFunction(() => {})`
3. **Edge case (2 files):** `const fn = oldFunction; fn()`

> **ACTION REQUIRED:**
> Please clarify how to handle these variations.
```

---

## Phase 3: Plan Creation

### 3.1 Create Refactor Plan in /tmp

Create a detailed plan document:

```bash
/tmp/refactor-plan-{descriptive-name}.md
```

### 3.2 Plan Document Structure

```markdown
# Refactor Plan: {Title}

**Created:** {date}
**Type:** {rename|restructure|pattern-change|api-migration|cleanup|type-improvement}
**Scope:** {small|medium|large|massive} ({N} files)
**Risk Level:** {low|medium|high|critical}

## Summary

One-paragraph description of what this refactor accomplishes.

## Before/After Examples

### Before
\`\`\`typescript
// Current pattern
\`\`\`

### After
\`\`\`typescript
// New pattern
\`\`\`

## Pattern Rules

| Rule | Description |
|------|-------------|
| Rule 1 | How to transform pattern A |
| Rule 2 | How to handle edge case B |

## Scope Analysis

### Files to Modify

| # | File | Changes | Complexity |
|---|------|---------|------------|
| 1 | `path/to/file.ts` | Description | simple |
| 2 | `path/to/other.ts` | Description | complex |

### Files to Exclude

| File | Reason |
|------|--------|
| `path/to/excluded.ts` | Reason for exclusion |

## Edge Cases

| Case | Files Affected | Handling |
|------|----------------|----------|
| Case 1 | `file.ts` | How to handle |

## Validation Plan

1. Type check after each batch
2. Run affected tests after changes
3. Manual verification of complex cases
```

### 3.3 User Approval

Present the plan summary and ask for approval:

```markdown
## Refactor Plan Summary

**What:** {brief description}
**Scope:** {N} files across {directories}
**Risk:** {level}

**Key Changes:**
1. Change A
2. Change B
3. Change C

**Edge Cases Identified:** {N} (see plan for details)

> **ACTION REQUIRED:**
> Review the plan above and choose:
> - **Approve** - Proceed with refactoring
> - **Modify** - Request changes to the plan
> - **Cancel** - Abort the refactor
```

---

## Phase 4: Execution

### 4.1 Create File List for Tracking

Create `.ai-assistant/file-lists/refactor-{name}.md`:

```markdown
# Refactor: {Title}

**Plan:** `/tmp/refactor-plan-{name}.md`
**Created:** {date}
**Status:** In Progress

## Progress

- Total files: {N}
- Completed: 0
- Remaining: {N}

## Files

### Pending

- [ ] `path/to/file1.ts` - {brief note}
- [ ] `path/to/file2.ts` - {brief note}

### Completed

[Empty initially]

### Skipped

[Files that couldn't be refactored with reason]
```

### 4.2 Execute in Batches

For medium to large refactors, work in batches:

**Batch 1:** Files 1-5
- Apply pattern transformation
- Verify no type errors
- Run tests

**Batch 2:** Files 6-10
- Apply pattern transformation
- Verify no type errors
- Run tests

### 4.3 Handle Discrepancies

If a file doesn't match expected patterns:

1. **Stop and document** - Don't force the change
2. **Ask for clarification** - Present the discrepancy
3. **Update the plan** - Add new rule if needed
4. **Continue** - Apply updated approach

```markdown
> **WARNING:**
> Discrepancy found - file doesn't match expected pattern.

**File:** `src/components/Special.ts`
**Expected:** `oldPattern()`
**Found:** `oldPattern.withConfig()`

> **ACTION REQUIRED:**
> Choose how to proceed:
> 1. **Skip** - Leave this file unchanged
> 2. **Transform** - Apply similar transformation
> 3. **Manual** - Flag for manual review later
```

---

## Phase 5: Validation

### 5.1 Run Type Checking

```bash
npm run typecheck
```

### 5.2 Run Linting

```bash
npm run lint
```

### 5.3 Run Affected Tests

```bash
npm run test -- {affected-pattern}
```

### 5.4 Completion Report

```markdown
## Refactor Complete: {Title}

**Files Modified:** {N}
**Files Skipped:** {N} (with reasons)
**Issues Found:** {N}

### Validation Results

Type checking: Passed
Linting: Passed
Tests: Passed ({N} tests)

### Manual Review Needed

- [ ] `file.ts` - Complex edge case, verify behavior

### File List

Updated: `.ai-assistant/file-lists/refactor-{name}.md`
```

---

## Rules

### Prohibited

- **Do not change behavior** - Refactors should preserve functionality
- **Do not skip validation** - Always run type checking and tests
- **Do not ignore edge cases** - Document and handle all variations
- **Do not force changes** - Ask about discrepancies

### Required

- **Create a plan first** - No refactoring without documented plan
- **Get user approval** - For scope > 5 files or risk > low
- **Track progress** - Use file list for all multi-file refactors
- **Validate after changes** - Type check and test affected code
- **Report discrepancies** - Don't silently skip or modify differently

---

## Quick Checklist Template

Copy this checklist when starting a refactor:

```markdown
## Refactor: {Title}

### Pre-Refactor
- [ ] Understand requirements
- [ ] Search for all occurrences
- [ ] Document pattern variations
- [ ] Create plan in `/tmp/refactor-plan-{name}.md`
- [ ] Get user approval

### Execution
- [ ] Create file list in `.ai-assistant/file-lists/`
- [ ] Batch 1: {files} -> Verify: type check
- [ ] Batch 2: {files} -> Verify: type check
- [ ] ...

### Validation
- [ ] Type check
- [ ] Lint
- [ ] Tests

### Post-Refactor
- [ ] Update file list (mark complete)
- [ ] Report results
```

---

## References

- [Create File List](./create-file-list.prompt.md)
- [Create Todo](./create-todo.prompt.md)
- [TypeScript Guidelines](../domains/typescript.instructions.md)
