---
name: adr
description: Capture an Architecture Decision Record documenting context, reasoning, alternatives, and consequences of a significant technical decision.
category: meta
model: sonnet
effort: medium
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

## Iron Laws

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

#### Step 1.1: Read Existing ADRs

Before interviewing or creating anything, read all existing ADRs in `.ai-project/decisions/`:

```bash
ls .ai-project/decisions/
```

For each existing ADR, note:
- Title and status
- Whether it relates to the current decision topic
- Whether the new decision supersedes it

**If a related ADR exists with status "Accepted":** Confirm with the user whether the new decision supersedes it.

#### Step 1.2: Interview (if needed)

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

#### Step 1.3: Search for Related ADRs

Search existing ADRs for references to the decision topic:

```bash
grep -ril "<topic keyword>" .ai-project/decisions/ 2>/dev/null
```

Any ADR that references the topic domain should be noted in the "Related Decisions" section of the new ADR, with a brief note about whether it needs updating as a consequence.

**If the decision is trivial or forced (see "When NOT to Create"):** Suggest skipping the ADR and explain why:
- Forced decision (e.g., security patch with no alternatives) — not worth recording
- Trivial implementation detail — too granular for an ADR
- Already documented — point to existing ADR

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
- **When superseding:** Create a NEW file with a descriptive name for the new decision (e.g., `jwt-authentication.md`). Do NOT reuse the old ADR's filename — even though git history preserves the old content, having two distinct files makes the superseding relationship explicit and both decisions discoverable.

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
1. Create a NEW ADR file with a descriptive name for the new decision
2. Update the old ADR's status to `Superseded by [new-adr-name.md]`
3. The new ADR's context should reference the previous decision so it stands alone
4. Both files remain in `.ai-project/decisions/` — the old content is preserved in place, not just in git history

## Creating from a Completed Todo

When invoked with `--from-todo`, the workflow adapts:

1. Read the todo file for context (description, shortcut taken, proper solution, affected files)
2. The "Context" section incorporates the original problem and constraints from the todo
3. The "Decision" section captures what was actually implemented
4. The "Alternatives" section draws from the todo's context about shortcuts vs. proper solutions
5. After the ADR is created, **delete the todo file** — the ADR now holds the decision record, git history preserves the todo's existence

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| ADR-T1 | Positive | "Record why we chose React over Vue" | Skill triggers |
| ADR-T2 | Positive | "Create an ADR for the API pattern" | Skill triggers |
| ADR-T3 | Positive | "Document the architecture decision" | Skill triggers |
| ADR-T4 | Negative | "How does the API work?" | Does NOT trigger (-> /explore) |
| ADR-T5 | Negative | "Add documentation to the codebase" | Does NOT trigger (-> /docs) |
| ADR-T6 | Negative | "Note this tech debt for later" | Does NOT trigger (-> /add-todo) |
| ADR-T7 | Boundary | "Why did we choose this approach?" | Context-dependent — if asking about an existing decision, route to /explore; if recording a new decision, trigger /adr |
| ADR-T8 | Positive | `/adr` when existing ADR will be superseded | Agent reads existing ADRs, detects superseding relationship, creates new file (does NOT reuse old filename), updates old ADR status |
| ADR-T9 | Boundary | `/adr` for a trivial formatting decision | Agent suggests skipping — too granular for an ADR per "When NOT to Create" |
| ADR-T10 | Boundary | `/adr` for a forced security patch | Agent suggests skipping — forced decision with no real alternatives |
