---
name: plan
description: Create a detailed implementation plan without writing code. Read-only analysis and planning with user approval gate. Use before implementing features or making significant changes.
---

# Plan

> **Purpose:** Create detailed implementation plan without writing code
> **Mode:** Read-only — no code changes
> **Usage:** `/plan [scope flags] <task description>`

## Iron Laws

1. **NO CODE IN PLANNING** — This is a read-only skill. Do not write, edit, or modify any source files. Planning only.
2. **EVERY STEP MUST BE ACTIONABLE** — Vague steps like "update the auth module" are not plans. Specify the file path, what changes, and what the result looks like.
3. **NO PLAN WITHOUT APPROVAL** — Do not proceed to implementation without explicit user approval of the plan.

## When to Use

- Before implementing a new feature
- Before making significant changes to existing code
- When the approach is unclear and needs design
- When multiple files or components are affected

## When NOT to Use

- Simple single-file changes with clear approach → just `/implement`
- Bug investigation → `/debug`
- Post-implementation review → `/review`
- Refactoring with known pattern → `/refactor`

## Constraints

- **Read-only** — Do NOT write any code
- **Planning only** — Use read, glob, grep operations
- **Approval gate** — Do NOT proceed to implementation without explicit user approval

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Focus planning on specific files/directories |
| `--uncommitted` | Plan based on current uncommitted changes |
| `--project=<path>` | Project root for monorepos |

**Examples:**
```bash
/plan --files=src/auth/ add password validation
/plan --uncommitted what's the best way to finish this
/plan add caching to the API layer
```

## Workflow

### Step 1: Parse Scope

```bash
git branch --show-current
git status --porcelain
```

Display scope context:

```markdown
## Plan Scope

| Scope | Value |
|-------|-------|
| Files | [from --files or "to be determined"] |
| Branch | [current branch] |

**Task:** [from user input]
```

### Step 2: Explore Relevant Code

1. Search for related files
2. Read key components
3. Understand existing patterns
4. Identify dependencies

### Step 3: Assess Complexity

| Complexity | Characteristics | Plan Depth |
|------------|-----------------|------------|
| **Trivial** | 1-2 files, known pattern | Bullet list of changes |
| **Standard** | 3-5 files, clear approach | Detailed steps with code snippets |
| **Complex** | 6+ files, architectural impact | Full plan with alternatives analysis |
| **Risky** | Breaking changes, migrations, data loss potential | Plan + rollback plan + test strategy |

Flag the assessed complexity to the user. For Complex and Risky, consider whether `/refactor` is more appropriate.

### Step 4: Identify Approach

Consider:
- What changes are needed?
- Which files will be modified?
- What patterns should be followed?
- What edge cases exist?
- What could go wrong?

For Complex/Risky tasks, present 2-3 alternative approaches with trade-offs before recommending one.

### Step 5: Create Plan

**Every step must meet these requirements:**
- Exact file path (verified to exist or explicitly marked as new)
- What specifically changes (not "update the component" but "add validation to the onSubmit handler")
- Representative code snippet showing the change shape
- Clear deliverable (what's true after this step that wasn't before)
- Estimated scope (how many lines, how many functions)

```markdown
## Implementation Plan

### Scope
| Scope | Value |
|-------|-------|
| Complexity | [Trivial / Standard / Complex / Risky] |
| Files | [paths] |
| Branch | [branch name] |
| Task | [task description] |

### Summary
[1-2 sentence overview]

### Files to Modify
| File | Change | Lines |
|------|--------|-------|
| `src/auth/login.ts` | Add input validation to handleSubmit | ~15 |
| `src/auth/login.spec.ts` | Add validation test cases | ~30 |

### Implementation Steps

**Step 1: [Action verb] [specific target]** (~2-5 min)
- File: `src/auth/login.ts`
- Change: [specific description]
- Code shape:
  ```typescript
  // Before:
  function handleSubmit(data: FormData) { ... }

  // After:
  function handleSubmit(data: FormData) {
    const validated = validateInput(data);
    if (!validated.success) return validated.errors;
    ...
  }
  ```
- Deliverable: [what's true after this step]

**Step 2: [Action verb] [specific target]** (~2-5 min)
- File: `src/auth/login.spec.ts`
- ...

### Edge Cases
| Case | Handling |
|------|----------|
| [Edge case] | [How to handle] |

### Test Strategy
- [Specific tests to write, not just "write tests"]
- [What assertions, what scenarios]

### Potential Risks
| Risk | Mitigation |
|------|------------|
| [What could go wrong] | [How to prevent or recover] |

---
**Approve this plan?** (yes / no / modify)
```

### Step 6: Wait for Approval

**GATE: Do NOT proceed to implementation without explicit approval.**

Valid approval: "yes", "approved", "proceed", "lgtm", "go ahead"

### Step 7: Execution Handoff

After approval, suggest how to execute:

```markdown
## Next Steps

Choose execution mode:
- **`/implement`** — Execute the plan step by step (default)
- **Parallel dispatch** — Break independent tasks into subagent work (for Complex plans)
- **Manual** — You execute, I advise

Which approach?
```

## Plan Quality Checklist

Before presenting the plan, verify:
- [ ] Every step has an exact file path
- [ ] Every step has a clear deliverable
- [ ] Code snippets show the shape of changes (not just prose)
- [ ] Edge cases have explicit handling (not "handle edge cases")
- [ ] Test strategy names specific scenarios (not "write tests")
- [ ] Risks have mitigation strategies (not "be careful")
- [ ] Steps are ordered by dependency (what must come first)
- [ ] No step takes longer than 5 minutes of focused work

## Extended Thinking

For complex decisions, use extended thinking to consider:
- Multiple approaches and trade-offs
- Existing patterns in the codebase
- Performance implications
- Maintainability
