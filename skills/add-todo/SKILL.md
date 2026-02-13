---
name: add-todo
description: Document deferred work, shortcuts, and technical debt for future resolution. Use when taking a shortcut, finding tech debt, or deferring out-of-scope work.
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

## Constraints

- **Always provide full context** -- Future readers need to understand without extra research
- **Use the template format** -- Consistent structure aids discovery and tracking
- **Set realistic priorities** -- Not everything is high priority

## Prerequisites

Requires `.ai-project/todos/` directory (created by `/init`). If it does not exist, create it or suggest running `/init`.

## When to Create a Todo

Create a todo entry when:

- Taking a shortcut that should be addressed later
- Identifying technical debt during development
- Discovering issues that are out of scope for current work
- Noting improvements that would require significant effort
- Deferring non-critical work to maintain focus

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
.ai-project/todos/{descriptive-name}.md
```

**Naming conventions:**
- Use kebab-case
- Be descriptive but concise
- Include category if helpful: `refactor-api-client.md`, `tech-debt-config-loading.md`

### Step 2: Use the Template

Fill in the template:

```markdown
---
id: {unique-id}
title: Brief Descriptive Title
priority: medium
category: tech-debt
status: open
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

### Step 3: Link Related Resources

Add references to related work:

```markdown
## Related

- **Todos:** [related-todo-id](./related-todo-id.md)
- **Issues:** [#123](https://github.com/org/repo/issues/123)
```

## Todo Lifecycle

1. **Created** -- Todo documented with full context
2. **In Progress** -- Actively being worked on
3. **Completed** -- Work finished, todo can be archived
4. **Cancelled** -- No longer relevant, document why

## Maintaining Todos

### Regular Review

- Review open todos periodically
- Update priorities based on current needs
- Close completed or obsolete todos

### When Completing

- Verify all acceptance criteria met
- Update status to `completed`
- Add completion notes if helpful
- Consider if documentation needs updating

## References

- [Example Todo](references/example-todo.md) -- Worked example of a fully filled-in todo entry
