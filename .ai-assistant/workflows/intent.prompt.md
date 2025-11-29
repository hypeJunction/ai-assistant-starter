---
chatmode: [developer, tester, reviewer, architect]
priority: high
---

# Intent Workflow

> **Chatmode:** Any chatmode can run this workflow
> **Purpose:** Identify relevant context, patterns, and resources before starting a task

This workflow helps gather comprehensive context for a task before implementation begins. It identifies relevant workflows, domains, patterns, and decisions that should inform the work.

## When to Use

Use this workflow when:
- Starting work on an unfamiliar area of the codebase
- Task involves multiple domains or patterns
- You want to ensure you're following established conventions
- Task requires architectural decisions
- You need to understand dependencies and related components

## Input

The user provides a general description of the task they want to accomplish.

**Example inputs:**
- "Add a new API endpoint for user data"
- "Implement caching for expensive operations"
- "Refactor the authentication module"
- "Add tests for the settings page"

## Discovery Process

### Phase 1: Task Classification

Classify the task to identify primary focus areas:

1. **Task Type** - Identify the nature of the work:
   - `feature` - New functionality
   - `bugfix` - Fix existing behavior
   - `refactor` - Restructure without changing behavior
   - `test` - Add or improve tests
   - `docs` - Documentation updates
   - `config` - Configuration changes

2. **Domains Involved** - Which technology areas does this touch?
   - TypeScript utilities
   - Testing
   - API/Services
   - Components/UI
   - State management
   - Configuration

### Phase 2: Context Gathering

Based on classification, gather relevant context:

1. **Load Domain Instructions**
   - Read applicable domain files from `.ai-assistant/domains/`
   - Note key patterns and rules for the task

2. **Check Architectural Decisions**
   - Review relevant ADRs in `.ai-assistant/decisions/`
   - Understand established patterns and their rationale

3. **Find Existing Patterns**
   - Search for similar code in the codebase
   - Identify patterns to follow or extend

4. **Review Related Workflows**
   - Identify workflows that may apply to this task
   - Note any procedures that must be followed

### Phase 3: Scope Analysis

Analyze the scope of changes:

1. **Identify Affected Files**
   - List files that will likely need changes
   - Estimate if this is small (1-5), medium (6-20), or large (21+) scale

2. **Find Dependencies**
   - What does this code depend on?
   - What depends on this code?

3. **Check Test Coverage**
   - Are there existing tests?
   - What test files will need updates?

### Phase 4: Plan Formulation

Create an actionable plan:

1. **Prerequisites**
   - Information needed before starting
   - Questions to clarify with user

2. **Implementation Steps**
   - Concrete actions in order
   - Which files to create/modify

3. **Validation Steps**
   - How to verify the work
   - Tests to run

## Output Format

Present findings in this structure:

```markdown
# Intent Analysis: [Brief Task Description]

## Task Classification
- **Type:** [feature/bugfix/refactor/test/docs/config]
- **Domains:** [list of domains]
- **Scope:** [small/medium/large] ([N] files estimated)

## Relevant Context

### Domain Guidelines
Load these instruction files:
- [ ] [domain].instructions.md - [reason to load]

### Architectural Decisions
Review these ADRs:
- [ ] [decision-name].md - [relevance]

### Existing Patterns
Reference these examples:
- `path/to/example` - [what to learn from it]

### Applicable Workflows
Consider using:
- [ ] [workflow-name] - [when/why to use]

## Dependencies
- **Uses:** [components/utilities this depends on]
- **Used by:** [what depends on this]

## Questions for User
[List any clarifications needed before proceeding]

## Proposed Plan

### Prerequisites
1. [What needs to happen first]

### Implementation Steps
1. [Step with specific file/action]
2. [Step with specific file/action]
...

### Validation
1. [How to verify correctness]

---

**Proceed with this plan?** (yes / adjust / questions)
```

## Quick Reference: Resources to Consider

### Domain Instructions
| Domain | File | When Relevant |
|--------|------|---------------|
| TypeScript | `typescript.instructions.md` | Any .ts file changes |
| Testing | `testing.instructions.md` | Adding/modifying tests |

### Common Workflows
| Workflow | Command | When to Use |
|----------|---------|-------------|
| Validate | `/validate` | Before committing |
| Refactor | `/refactor` | Large-scale changes |
| Create Todo | `/create-todo` | Document deferred work |

## Execution Notes

- **Be thorough** - Missing context leads to inconsistent implementations
- **Ask early** - Better to clarify before starting than to redo work
- **Check scale** - Large changes should use the refactor workflow
- **Note gaps** - If patterns are unclear, propose adding documentation
