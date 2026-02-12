---
name: implement
description: Full feature implementation workflow with explore, plan, code, test, validate, and commit phases. Use for new features, enhancements, or significant code changes.
---

# Implement

> **Purpose:** Full feature implementation workflow
> **Phases:** Explore → Plan → Code → Cover → Validate → Document → Sync → Commit
> **Usage:** `/implement [scope flags] <task description>`

## Gate Enforcement

**CRITICAL:** This workflow has mandatory approval gates. Do NOT proceed past a gate without explicit approval.

**Valid approval:** `yes`, `y`, `approved`, `proceed`, `lgtm`, `looks good`, `go ahead`
**Invalid (NOT approval):** Silence, questions, "I see", "okay", "hmm"

**When in doubt:** Ask explicitly: "I need your approval to continue. Please respond with 'yes' to proceed."

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Specific files/directories to work on |
| `--uncommitted` | Build on current uncommitted changes |
| `--branch=<name>` | Branch context (default: current) |
| `--project=<path>` | Project root for monorepos |

**Examples:**
```bash
/implement --files=src/auth/ add password validation
/implement --uncommitted finish the login feature
/implement --project=packages/api add rate limiting
```

---

## Related Skills

This skill orchestrates an end-to-end workflow that incorporates patterns from several standalone skills:
- `/explore` — Phase 1 uses read-only exploration patterns
- `/plan` — Phase 2 uses planning patterns
- `/cover` — Phase 4 uses test coverage patterns
- `/validate` — Phase 5 uses validation patterns
- `/docs` — Phase 6 uses documentation patterns
- `/sync` — Phase 7 uses sync patterns
- `/commit` — Phase 8 uses commit patterns
- For changes affecting 6+ files, consider `/refactor` instead

---

## Phase 1: Explore

**Mode:** Read-only — understand the codebase before planning.

### Step 1.0: Parse Scope

```bash
git branch --show-current
git status --porcelain
```

Display scope context:
```markdown
## Scope Context

| Scope | Value |
|-------|-------|
| Files | [from --files or inferred] |
| Branch | [current branch name] |

**Task:** [from user input]
```

If scope is ambiguous, ask for clarification. **Wait if needed.**

### Step 1.1: Understand Request

Before exploring code:
1. What's the goal?
2. Who is affected?
3. Constraints?
4. Success criteria?

**Wait for user response.**

### Step 1.2: Explore Code

Read relevant files, trace imports and dependencies, note patterns and conventions.

```markdown
## Codebase Analysis

**Relevant Files:**
- `path/to/file.ts` - [purpose]

**Current Behavior:** [how it works now]
**Patterns Found:** [conventions to follow]
```

### Step 1.3: Verify Understanding

Restate the task, list assumptions, flag unclear areas. **Wait for confirmation.**

### Step 1.4: Surface Edge Cases

Present edge cases and ask which matter and how to handle them. **Wait for guidance.**

---

## Phase 2: Plan

**Mode:** Read-only — design the approach.

### Step 2.1: Create Plan

```markdown
## Implementation Plan

### Summary
[1-2 sentences]

### Files to Modify
- `path/to/file.ts` - [change]

### Steps
1. [Specific action]
2. [Specific action]

### Edge Cases
- [Case] - [handling]

### Checklist

**Code Phase:**
- [ ] Implement [component/feature]

**Cover Phase:**
- [ ] Write unit tests
- [ ] Write component tests

**Validate Phase:**
- [ ] Type check passes
- [ ] Lint passes
- [ ] Build succeeds

---
**Approve this plan?** (yes / no / modify)
```

**STOP HERE. Do NOT proceed to Code Phase until user responds with explicit approval.**

---

## Phase 3: Code

**Mode:** Full access — implement the approved plan.

**Constraints:**
- Stay within approved scope (1-5 files direct, 6+ files → suggest `/refactor`)
- No documentation files without approval
- No destructive operations without confirmation

### Step 3.1: Implement

For each file in plan:
1. Edit the file
2. Run type check after changes
3. Report progress

### Step 3.2: Handle Surprises

If unexpected issues arise, present options and **wait for decision**.

### Step 3.3: Validate Code (Pre-Tests)

```bash
npm run typecheck
npm run lint
```

---

## Phase 4: Cover

**Mode:** Testing — ensure new code has appropriate test coverage.

### Step 4.1: Analyze Coverage Needs

Categorize changed files by verification type:
- Utility → Unit tests (`.spec.ts`)
- Component → Component tests + Storybook story
- Service → Unit tests with mocks
- Types → No tests needed

### Step 4.2: Write Tests

Write appropriate tests for each file requiring coverage. Include test plans in Gherkin format as comments.

### Step 4.3: Run All Tests in Scope

```bash
npm run test -- [changed-files-pattern]
```

### Step 4.4: Verification Report

```markdown
## Test Coverage Report

**Tests Written:**
| File | Tests | Status |
|------|-------|--------|
| `helper.spec.ts` | 5 tests | ✓ All passing |

**All tests must pass before proceeding.**
```

**GATE: All tests must pass.**

---

## Phase 5: Validate

Run full validation to ensure production readiness.

```bash
npm run typecheck
npm run lint
grep -rn -E "(api[_-]?key|secret|password|token|credential)\s*[:=]" src/  # secrets scan
npm run build
```

**GATE: All validations must pass.**

---

## Phase 6: Document (Optional)

Prompt whether documentation is needed for complex implementations:
- `code` — JSDoc/inline comments
- `user` — User documentation
- `readme` — README updates
- `skip` — No documentation needed

**Wait for user response.**

---

## Phase 7: Sync (Optional)

Prompt whether AI documentation needs syncing:
- `memory` — Update project memory
- `context` — Update quick reference
- `skip` — No sync needed

**Wait for user response.**

---

## Phase 8: Commit

**Mode:** Git operations with user confirmation required.

**Constraints:**
- Never commit without explicit user approval
- Never force push
- Never commit secrets
- Always show changes before committing

### Step 8.1: Review Changes

```markdown
## Changes Summary

**Files changed:** N

| File | Change |
|------|--------|
| `file1.ts` | Added feature |
| `file1.spec.ts` | Added tests |
```

### Step 8.2: Confirm Commit

```markdown
**Message:**
\`\`\`
feat: add user authentication

Implements login/logout with session management.
\`\`\`

**Commit?** (yes / no / edit)
```

**STOP HERE. Do NOT run `git commit` until user responds with explicit approval.**

---

## Quick Reference

| Phase | Mode | Gate |
|-------|------|------|
| 1. Explore | Read-only | User confirms understanding |
| 2. Plan | Read-only | **User approves plan** |
| 3. Code | Full access | User confirms implementation |
| 4. Cover | Testing | **All tests pass** |
| 5. Validate | Validation | **All checks pass** |
| 6. Document | Optional | User chooses |
| 7. Sync | Optional | User chooses |
| 8. Commit | Git only | **User confirms** |
