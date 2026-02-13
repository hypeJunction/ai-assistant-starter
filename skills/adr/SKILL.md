---
name: adr
description: Capture an Architecture Decision Record documenting context, reasoning, alternatives, and consequences of a significant technical decision.
triggers:
  - architecture decision
  - record decision
  - document decision
  - adr
  - why did we choose
  - design rationale
---

# ADR

> **Purpose:** Capture Architecture Decision Records documenting the reasoning behind significant technical choices
> **Usage:** `/adr [title]` or `/adr --from-todo <todo-file>`

## Constraints

1. **CAPTURE THE WHY** — The decision itself is visible in code. The ADR exists to record *why* this choice was made and what alternatives were rejected.
2. **ONE DECISION PER ADR** — Each ADR covers a single decision. Split compound decisions into separate records.
3. **CURRENT STATE ONLY** — ADRs reflect the current state of thinking. When a decision is superseded, update the status and link to the replacement. Git history tracks the evolution.

## Prerequisites

Requires `.ai-project/decisions/` directory (created by `/init`). If it does not exist, create it.

## When to Create

- Choosing between significant architectural approaches
- Adopting a new pattern, library, or technology
- Making decisions that affect many files or components
- Establishing conventions for the project
- Completing a planned work item that involved design choices
- Changing or reversing a previous decision

## When NOT to Create

- Trivial implementation details (variable names, formatting)
- Forced decisions with no real alternatives (security patches, dependency updates)
- Temporary scaffolding or experiments

## Workflow

### Step 1: Gather Context

If `--from-todo <todo-file>` is provided, read the todo file to extract:
- The original problem description
- Context about shortcuts taken or design constraints
- Affected files and acceptance criteria
- Any related todos or issues

Otherwise, interview for context:
1. What decision was made?
2. What problem or need prompted it?
3. What alternatives were considered?
4. What are the expected consequences?

**Skip the interview** if the user provided sufficient detail in the command.

### Step 2: Assess Scope

| Scope | Characteristics | ADR Depth |
|-------|-----------------|-----------|
| **Local** | Affects 1-2 files, single module | Brief — context + decision + key consequence |
| **Cross-cutting** | Affects multiple modules, 3-10 files | Standard — full template with alternatives |
| **Architectural** | Affects project structure, conventions, or data model | Comprehensive — full template + migration notes + diagrams |

### Step 3: Create the ADR

**File location:** `.ai-project/decisions/{descriptive-name}.md`

**Naming conventions:**
- Use kebab-case
- Name after the decision topic, not the date: `api-client-pattern.md`, `state-management.md`
- If superseding an existing ADR, use the same name (the old content is in git history)

**Template:**

```markdown
# ADR: {Title}

**Date:** {YYYY-MM-DD}
**Status:** Accepted

## Context

[What problem or need prompted this decision? What constraints existed?
Include relevant technical context — the reader should understand the situation
without needing to look at other documents.]

## Decision

[What was decided? Be specific about the approach, pattern, or technology chosen.
Include code examples if they clarify the decision.]

## Consequences

### Positive
- [Concrete benefit with explanation]

### Negative
- [Concrete drawback with explanation]

### Migration
- [What needs to change to adopt this decision, if anything]
- [Files affected, patterns to update, data to migrate]

## Alternatives Considered

### {Alternative 1}
- **Approach:** [Brief description]
- **Pros:** [Why it was attractive]
- **Cons:** [Why it was rejected]

### {Alternative 2}
- **Approach:** [Brief description]
- **Pros:** [Why it was attractive]
- **Cons:** [Why it was rejected]
```

For **Architectural** scope, also include:

```markdown
## Migration Plan

| Phase | Action | Files Affected |
|-------|--------|----------------|
| 1 | [First step] | [files] |
| 2 | [Second step] | [files] |

## Related Decisions

- [Link to related ADRs if they exist]
```

### Step 4: Verify Quality

Before presenting, check:
- [ ] Context explains the situation without requiring external documents
- [ ] Decision is specific and actionable (not vague)
- [ ] At least one alternative was genuinely considered
- [ ] Consequences include both positive and negative
- [ ] Migration section addresses what changes (if applicable)

### Step 5: Confirm

```markdown
ADR written to `.ai-project/decisions/{name}.md`

**Review the ADR?** (looks good / edit / cancel)
```

## ADR Lifecycle

| Status | Meaning |
|--------|---------|
| **Accepted** | Decision is current and active |
| **Deprecated** | No longer recommended but still exists in codebase |
| **Superseded** | Replaced by a newer ADR (link to replacement) |

When superseding an ADR:
1. Update the old ADR's status to `Superseded by [new-adr-name.md]`
2. Create the new ADR with context referencing the previous decision
3. The old ADR content is preserved in git history

## Creating from a Completed Todo

When invoked with `--from-todo`, the workflow adapts:

1. Read the todo file for context (description, shortcut taken, proper solution, affected files)
2. The "Context" section incorporates the original problem and constraints from the todo
3. The "Decision" section captures what was actually implemented
4. The "Alternatives" section draws from the todo's context about shortcuts vs. proper solutions
5. After the ADR is created, **delete the todo file** — the ADR now holds the decision record, git history preserves the todo's existence
