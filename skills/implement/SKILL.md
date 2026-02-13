---
name: implement
description: Full feature implementation workflow with explore, plan, code, test, validate, and commit phases. Use for new features, enhancements, or significant code changes.
---

# Implement

> **Purpose:** Full feature implementation workflow
> **Phases:** Explore → Plan → Code → Self-Review → Test → Validate → Commit
> **Usage:** `/implement [scope flags] <task description>`

## Iron Laws

1. **NO CODE WITHOUT APPROVED PLAN** — Never write implementation code until the user has explicitly approved the plan. Wasted code is worse than no code.
2. **VERIFY AFTER EVERY FILE** — Run typecheck after each file change. Don't batch edits across files without verification. Evidence before assertions.
3. **STAY IN SCOPE** — Never fix, improve, or refactor code outside the approved plan. Create a todo for out-of-scope issues.

## When to Use

- New feature implementation
- Enhancements to existing features
- Significant code changes (3-5 files)

## When NOT to Use

- Bug fixes → `/debug`
- 16+ file changes → `/refactor` (6-15 files: confirm with user, consider `/refactor` if structural)
- Design/planning only → `/plan`
- Quick single-file edit → edit directly
- Emergency fix → `/hotfix`
- Strict test-first approach → `/tdd` (note: `/implement` supports TDD-lite in Phase 5)

## Gate Enforcement

See `ai-assistant-protocol` for valid approval terms and invalid responses.

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Specific files/directories to work on |
| `--uncommitted` | Build on current uncommitted changes |
| `--branch=<name>` | Branch context (default: current) |
| `--project=<path>` | Project root for monorepos |

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

---

## Phase 1: Explore

**Mode:** Read-only — understand the codebase before planning.

### Step 1.1: Parse Scope

```bash
git branch --show-current
git status --porcelain
```

If scope is ambiguous, ask for clarification. Use subagents for large explorations (6+ files) to preserve context.

### Step 1.2: Understand Request

1. What's the goal? (success criteria, not task description)
2. Who is affected?
3. Constraints?

**Wait for user response if requirements are unclear.**

### Step 1.3: Explore Code

Read relevant files, trace imports and dependencies, note patterns and conventions.

### Step 1.4: Verify Understanding

Restate the task, list assumptions, flag edge cases. **Wait for confirmation.**

---

## Phase 2: Plan

**Mode:** Read-only — design the approach.

### Step 2.1: Create Plan

Every step must include exact file paths, specific changes, and code snippets showing the shape of the change. See `/plan` skill for the full plan quality checklist.

```markdown
## Implementation Plan

### Summary
[1-2 sentences]

### Files to Modify
| File | Change | Lines |
|------|--------|-------|
| `path/to/file.ts` | [specific change] | ~N |

### Steps
1. **[Action] [target]** — File: `path`, Change: [specific], Deliverable: [what's true after]

### Edge Cases
- [Case] → [handling]

### Checklist
- [ ] Implement [component/feature]
- [ ] Write tests
- [ ] Type check + lint passes

---
**Approve this plan?** (yes / no / modify)
```

**GATE: Do NOT proceed to Code Phase until user responds with explicit approval.**

---

## Phase 3: Code

**Mode:** Full access — implement the approved plan.

### Step 3.1: Create Git Savepoint

For complex implementations, create a savepoint before starting:

```bash
git stash push -m "savepoint: before [feature]" --include-untracked
git stash pop
```

Or commit any existing work so you can revert cleanly if needed.

### Step 3.2: Implement (Verify Per File)

For each file in plan:
1. Edit the file
2. **Run typecheck immediately** — don't batch multiple file edits
3. Report progress

If typecheck fails after a change, fix it before moving to the next file.

### Step 3.3: Handle Surprises

| Surprise Type | Response |
|---------------|----------|
| **Scope expansion** | Stop. Present additional scope and ask for approval. |
| **Missing dependency** | Note it, ask if it should be added. |
| **Design conflict** | Present options. Don't force the original plan. |
| **Existing bug found** | Create a todo. Do NOT fix — out of scope. |

### Step 3.4: Validate Code

```bash
npm run typecheck
npm run lint
```

---

## Phase 4: Self-Review

**Mode:** Read-only — review your own work before testing.

Compare implementation against the approved plan:

```markdown
## Spec Compliance
| Plan Item | Status | Notes |
|-----------|--------|-------|
| [Step 1] | ✓ / ✗ | [deviations] |
```

Check for: `any` types, missing error handling, hardcoded values, inconsistent patterns, unused imports.

**Security checklist (mandatory for code that handles user input, auth, or external data):**

- [ ] No `eval()`, `new Function()`, or dynamic code execution with external input
- [ ] No `innerHTML`, `dangerouslySetInnerHTML`, or `v-html` with unsanitized data
- [ ] No raw SQL with string interpolation — use parameterized queries or ORM
- [ ] No hardcoded secrets, API keys, or credentials — use environment variables
- [ ] No `child_process.exec()` with user-controlled input — use `execFile()` with explicit args
- [ ] No disabled security controls (`rejectUnauthorized: false`, `--no-verify`)
- [ ] Input validation present at system boundaries (API routes, form handlers)
- [ ] Auth/authz checks present on protected routes and operations

Fix issues before proceeding.

---

## Phase 5: Test

**Mode:** Testing — ensure new code has appropriate test coverage.

**Test ordering:**
- **New functions/modules** — prefer writing the test first (TDD-style: write failing test, then implement, then verify). This produces tighter, more targeted code.
- **Enhancements to existing code** — write tests after implementation, verifying both new and existing behavior.
- **For strict TDD workflows**, use `/tdd` instead of `/implement`.

**Steps:**
1. Categorize changed files by verification type (utility → unit tests, component → component tests, types → skip)
2. Write tests with Gherkin test plans as comments
3. Run tests: `npm run test -- [changed-files-pattern]`

**GATE: All tests must pass.**

---

## Phase 6: Validate

Run full validation:

```bash
npm run typecheck
npm run lint
npm run build
```

**GATE: All validations must pass. If any fail, fix before proceeding.**

---

## Phase 7: Commit

**Mode:** Git operations with user confirmation required.

### Step 7.1: Completion Evidence

```markdown
## Completion Evidence
| Verification | Result |
|--------------|--------|
| Type check | ✓ Pass |
| Lint | ✓ Pass |
| Tests | ✓ Pass (N tests) |
| Build | ✓ Pass |
| Spec compliance | ✓ All plan items |
```

### Step 7.2: Confirm Commit

```markdown
**Message:**
```
feat: add user authentication
```

**Commit?** (yes / no / edit)
```

**GATE: Do NOT run `git commit` until user responds with explicit approval.**

---

## Quick Reference

| Phase | Mode | Gate |
|-------|------|------|
| 1. Explore | Read-only | User confirms understanding |
| 2. Plan | Read-only | **User approves plan** |
| 3. Code | Full access | Typecheck passes per file |
| 4. Self-Review | Read-only | Spec compliance verified |
| 5. Test | Testing | **All tests pass** |
| 6. Validate | Validation | **All checks pass** |
| 7. Commit | Git only | **User confirms** |
