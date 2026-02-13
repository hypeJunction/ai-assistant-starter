---
name: plan
description: Create a detailed implementation plan without writing code. Read-only analysis and planning with user approval gate. Use before implementing features or making significant changes.
triggers:
  - plan approach
  - design before coding
  - think through
  - what's the best way
  - plan implementation
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
- You could describe the diff in one sentence → edit directly
- Bug investigation → `/debug`
- Refactoring with known pattern → `/refactor`

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Focus planning on specific files/directories |
| `--uncommitted` | Plan based on current uncommitted changes |
| `--project=<path>` | Project root for monorepos |

## Workflow

### Step 1: Parse Scope

```bash
git branch --show-current
git status --porcelain
```

### Step 2: Interview (for complex or ambiguous tasks)

Before exploring code, interview the user to clarify requirements:

1. What's the desired end state? (success criteria, not task description)
2. What constraints exist? (performance, compatibility, dependencies)
3. Any approaches you've considered or want to avoid?
4. Edge cases that matter to you?

**Skip this step** if the user provided a detailed spec or the task is straightforward.

### Step 3: Explore Relevant Code

Use subagents for large explorations (6+ files) to preserve context.

1. Search for related files
2. Read key components
3. Understand existing patterns
4. Identify dependencies

### Step 4: Assess Complexity

| Complexity | Characteristics | Plan Depth |
|------------|-----------------|------------|
| **Trivial** | 1-2 files, known pattern | Bullet list of changes |
| **Standard** | 3-5 files, clear approach | Detailed steps with code snippets |
| **Complex** | 6+ files, architectural impact | Full plan with alternatives analysis |
| **Risky** | Breaking changes, migrations, data loss potential | Plan + rollback plan + test strategy |

For Complex and Risky, present 2-3 alternative approaches with trade-offs before recommending one.

### Step 5: Create Plan

**Every step must include:** exact file path, what specifically changes, representative code snippet showing the change shape, clear deliverable, and estimated scope.

```markdown
## Implementation Plan

### Summary
[1-2 sentences]

### Files to Modify
| File | Change | Lines |
|------|--------|-------|
| `src/auth/login.ts` | Add input validation to handleSubmit | ~15 |

### Steps

**Step 1: [Action verb] [specific target]** (~2-5 min)
- File: `src/auth/login.ts`
- Change: [specific description]
- Code shape:
  ```typescript
  // Before → After showing the change
  ```
- Deliverable: [what's true after this step]

### Edge Cases
| Case | Handling |
|------|----------|
| [Edge case] | [How to handle] |

### Test Strategy
- [Specific test scenario with expected assertion]

### Security Considerations
- [ ] Handles user input? → Validation required at entry point
- [ ] Touches auth/authz? → Verify access controls preserved
- [ ] Stores/transmits sensitive data? → Encryption and secrets management
- [ ] Calls external services? → Input sanitization and response validation
- [ ] N/A — no security-sensitive changes

### Risks
| Risk | Mitigation |
|------|------------|
| [What could go wrong] | [How to prevent or recover] |

---
**Approve this plan?** (yes / no / modify)
```

For Complex/Risky plans, optionally include a Mermaid diagram showing component relationships or data flow.

### Step 6: Wait for Approval

**GATE: Do NOT proceed to implementation without explicit approval.**

See `ai-assistant-protocol` for valid approval terms and invalid responses.

### Step 7: Persist Plan as Todos

After approval, invoke `/add-todo` for each plan step to create trackable, persistent work items.

For each step in the approved plan, create a todo with:
- **Title:** The step's action (e.g., "Add input validation to handleSubmit")
- **Category:** `feature` (or `refactor`, `test`, etc. as appropriate)
- **Description:** The step's specific changes, file paths, and deliverable from the plan
- **Affected Files:** Exact files from the plan step
- **Acceptance Criteria:** The step's deliverable restated as checkable criteria

```markdown
## Todos Created

| Todo | File | Priority |
|------|------|----------|
| `add-input-validation.md` | `.ai-project/todos/` | medium |
| `update-api-handler.md` | `.ai-project/todos/` | medium |
| `add-validation-tests.md` | `.ai-project/todos/` | medium |

Each step is now a trackable todo. When completed, `/add-todo` will prompt
for an ADR capturing the decision, then remove the todo.
```

**Skip this step** for Trivial plans (1-2 files, single bullet list).

### Step 8: Execution Handoff

```markdown
## Next Steps

Choose execution mode:
- **`/implement`** — Execute the plan step by step (default)
- **`/tdd`** — Test-driven execution (write tests first, then implement)
- **Parallel dispatch** — Break independent tasks into subagent work (for Complex plans)
- **Manual** — You execute, I advise

Which approach?
```

## Plan Quality Checklist

Before presenting the plan, verify:
- [ ] Every step has an exact file path
- [ ] Every step has a clear deliverable
- [ ] Code snippets show the shape of changes
- [ ] Edge cases have explicit handling
- [ ] Test strategy names specific scenarios
- [ ] Risks have mitigation strategies
- [ ] Steps are ordered by dependency
- [ ] No step takes longer than 5 minutes of focused work
