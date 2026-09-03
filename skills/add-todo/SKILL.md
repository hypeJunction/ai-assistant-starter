---
name: add-todo
description: Document deferred work, shortcuts, and technical debt for future resolution. Use when taking a shortcut, finding tech debt, or deferring out-of-scope work.
category: meta
model: haiku
effort: low
triggers:
  - defer this
  - tech debt
  - add todo
  - note for later
  - shortcut taken
---

# Add Todo

> **Purpose:** Document deferred work, shortcuts, and technical debt for future resolution
> **Usage:** `/add-todo <description>`

## Iron Laws

1. **FULL CONTEXT ALWAYS** -- Future readers must understand the todo without extra research. If you can't explain it standalone, you haven't captured enough.
2. **ONE TEMPLATE** -- Use the canonical template defined in this file's workflow section. No freeform notes. No alternate formats.
3. **REALISTIC PRIORITIES** -- Not everything is high priority. Default to `P2-medium` unless there's a clear reason otherwise.
4. **CONFIRM BEFORE WRITING** -- Always show the complete todo content to the user and get approval before writing the file.

## Prerequisites

Requires `.ai-project/todos/` directory (created by `/init`). If it does not exist, create it or suggest running `/init`.

## When to Create a Todo

Create a todo entry when:

- Taking a shortcut that should be addressed later
- Identifying technical debt during development
- Discovering issues that are out of scope for current work
- Noting improvements that would require significant effort
- Deferring non-critical work to maintain focus

## When NOT to Create

- **P0-critical issues in current scope** — Fix it now with `/debug` or `/implement` instead of deferring. If the user describes something critical that belongs in the current work, say: *"This sounds like a P0-critical issue in scope — consider using `/debug` or `/implement` to address it now rather than deferring."*
- Active bugs that should be fixed now -> `/debug`
- Work that's part of the current task scope — just do it
- Vague ideas without concrete action ("maybe someday...") — not actionable
- Issues already tracked in an external system (Jira, GitHub Issues) — avoid duplication
- Architecture decisions that need recording -> `/adr`

## Todo Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `tech-debt` | Code that works but needs improvement | Hardcoded values, missing abstractions |
| `refactor` | Code structure improvements | Pattern migrations, file reorganization |
| `feature` | Missing functionality | Incomplete implementations, TODO comments |
| `bug` | Known issues not yet fixed | Edge cases, race conditions |
| `performance` | Performance improvements | Optimization opportunities |
| `docs` | Documentation needs | Missing API docs, outdated guides |
| `test` | Testing improvements | Missing tests, flaky tests |

## Priority Levels

| Priority | Description | Action Timeline |
|----------|-------------|-----------------|
| `P0` | Critical — blocking or causes data loss | Fix now (consider `/debug` or `/implement` instead) |
| `P1` | High — significant impact, needs attention soon | Address in next session |
| `P2` | Medium — should be addressed | Next opportunity |
| `P3` | Low — nice to have | When time permits |

## Workflow

### Step 1: Gather Information

Parse the user's description and identify what is provided vs. missing.

**Required metadata — ask if not provided:**

- **Priority:** If the user hasn't specified, ask: *"What priority? (P0-critical, P1-high, P2-medium, P3-low)"*
- **Estimated effort:** If the user hasn't specified, ask: *"Estimated effort? (nano/small/medium/large)"*

**Determine from context (do not ask):**

- **Affected files** — infer from the description or current working context
- **Context** — what triggered this (e.g., "found during /implement session")
- **Category** — match to the todo categories table

**If the description is vague**, ask for specifics before proceeding: *"Can you clarify what exactly the issue is and what the expected behavior should be?"*

**If the issue sounds P0-critical and in scope**, suggest fixing it now: *"This sounds like a critical issue in the current scope — would you prefer to use `/debug` or `/implement` to address it now?"*

### Step 2: Determine File Name

Create a new file in `.ai-project/todos/`:

```bash
.ai-project/todos/NNN-{descriptive-name}.md
```

**Naming conventions:**
- Prefix with a 3-digit sequence number for queue ordering: `001-`, `002-`, etc.
- Use kebab-case for the description
- Be descriptive but concise
- Examples: `001-refactor-api-client.md`, `002-optimize-search-full-table-scan.md`

To determine the next sequence number, check existing files:
```bash
ls .ai-project/todos/[0-9]*.md 2>/dev/null | tail -1
```

### Step 3: Fill In the Canonical Template

This is the **single authoritative template** for all todo files. Do not use any other format.

```markdown
---
title: Brief Descriptive Title
priority: P2
estimated_effort: medium
created: YYYY-MM-DD
context: What triggered this — e.g., "found during /implement session"
---

## Description

Clear description of what needs to be done and why. Future readers must
understand the issue without extra research.

## Affected Files

- `path/to/file.ts` — what needs to change and why

## Suggested Approach

1. Step-by-step outline of how to fix this
2. Include enough detail to act on without re-investigation

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

**Effort levels:**

| Effort | Description |
|--------|-------------|
| `nano` | < 15 minutes, trivial change |
| `small` | 15-60 minutes, straightforward |
| `medium` | 1-4 hours, moderate complexity |
| `large` | 4+ hours, significant work |

### Step 4: Show and Confirm

**REQUIRED — do not skip.** Show the complete todo content (frontmatter + body) to the user and ask for approval before writing:

> *"Here's the todo I'll create at `.ai-project/todos/NNN-name.md`. Does this look good?"*

Wait for the user to confirm. If they request changes, adjust and re-show.

### Step 5: Write and Confirm

After approval:

1. Write the file to `.ai-project/todos/NNN-{descriptive-name}.md`
2. Confirm creation: *"Created `.ai-project/todos/NNN-name.md`."*

### Optional: Link Related Resources

If there are related todos or issues, add a Related section at the end:

```markdown
## Related

- **Todos:** [related-todo-id](./related-todo-id.md)
- **Issues:** [#123](https://github.com/org/repo/issues/123)
```

## Todo Lifecycle

1. **Created** — Todo documented with full context
2. **In Progress** — Actively being worked on
3. **Done** — Work finished → ADR created → todo deleted
4. **Cancelled** — No longer relevant → todo deleted with brief note in commit message

**Completed todos are not kept.** ADRs capture the decision record. Git history preserves the todo's existence.

## Completing a Todo

When a todo is done:

1. **Verify all acceptance criteria are met**
2. **Create an ADR** — Invoke `/adr --from-todo <todo-file>` to capture the decision context, what was implemented, alternatives considered, and consequences
3. **Delete the todo file** — The ADR now holds the permanent record; git history preserves the todo
4. **Commit both changes** — The ADR creation and todo deletion should be in the same commit

### Why Delete?

- ADRs reflect the **current state** of architectural thinking
- Todos reflect **pending work** — once done, they are noise
- Git history provides the **step-by-step evolution** if needed
- Stale completed todos create confusion about what's actually pending

## Cancelling a Todo

When a todo is no longer relevant:

1. **Delete the todo file**
2. **Note the reason in the commit message** (e.g., "remove todo: superseded by X" or "remove todo: no longer applicable after Y")
3. No ADR needed for cancellations unless a significant decision was involved

## Maintaining Todos

### Regular Review

- Review open todos periodically
- Update priorities based on current needs
- Cancel obsolete todos (delete with reason in commit)

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| TODO-T1 | Positive | "Note this shortcut for later" | Skill triggers |
| TODO-T2 | Positive | "Add a todo for this tech debt" | Skill triggers |
| TODO-T3 | Positive | "Defer this, it's out of scope" | Skill triggers |
| TODO-T4 | Negative | "Fix this bug" | Does NOT trigger (-> /debug) |
| TODO-T5 | Negative | "Record the architecture decision" | Does NOT trigger (-> /adr) |
| TODO-T6 | Negative | "Add documentation to this function" | Does NOT trigger (-> /docs) |
| TODO-T7 | Boundary | "We should improve this eventually" | Context-dependent — if it's concrete deferred work, create a todo; if vague, ask for specifics before creating |

## References

- [Example Todo](references/example-todo.md) — Worked example of a fully filled-in todo entry
