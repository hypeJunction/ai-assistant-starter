---
name: add-todo
description: Document deferred work, shortcuts, and technical debt for future resolution. Use when taking a shortcut, finding tech debt, or deferring out-of-scope work.
category: meta
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
2. **USE THE TEMPLATE** -- Consistent structure aids discovery, tracking, and queue management. No freeform notes.
3. **REALISTIC PRIORITIES** -- Not everything is high priority. Default to `medium` unless there's a clear reason otherwise.

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
| `high` | Blocking or high-impact | Address soon |
| `medium` | Should be addressed | Next opportunity |
| `low` | Nice to have | When time permits |

## Workflow

### Step 1: Create the File

Create a new file in `.ai-project/todos/`:

```bash
.ai-project/todos/NNN-{descriptive-name}.md
```

**Naming conventions:**
- Prefix with a 3-digit sequence number for queue ordering: `001-`, `002-`, etc.
- Use kebab-case for the description
- Be descriptive but concise
- Examples: `001-refactor-api-client.md`, `002-tech-debt-config-loading.md`

To determine the next sequence number, check existing files:
```bash
ls .ai-project/todos/[0-9]*.md 2>/dev/null | tail -1
```

### Step 2: Use the Template

Fill in the template (see `_template.md` in todos directory):

```markdown
---
id: {unique-id}
title: Brief Descriptive Title
priority: medium
category: tech-debt
status: open
estimated_effort: medium
queue_position: 0
blocked_by: []
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
labels: []
---

# Brief Descriptive Title

## Description

Clear description of what needs to be done and why.

## Context

| Aspect | Details |
|--------|---------|
| **Shortcut Taken** | What compromise was made |
| **Reason** | Why it couldn't be done properly at the time |
| **Proper Solution** | What the ideal solution would look like |

## Affected Files

| File | Changes Needed |
|------|----------------|
| `path/to/file.ts` | Description of changes |

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

### Queue Fields

| Field | Values | Description |
|-------|--------|-------------|
| `estimated_effort` | `nano`, `small`, `medium`, `large` | Matches task tier system |
| `queue_position` | integer | Ordering within same priority (0 = unordered) |
| `blocked_by` | list of todo IDs | Todos that must complete before this one |

### Step 3: Link Related Resources

Add references to related work:

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
