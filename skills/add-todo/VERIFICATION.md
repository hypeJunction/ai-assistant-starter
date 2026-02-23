# Add-Todo Skill Verification

## Scenario

During a `/implement` session, the developer encounters a performance issue in `src/services/search.service.ts` — the search function does a full table scan instead of using an indexed query. This is out of scope for the current feature work. They invoke `/add-todo` to document this as deferred work.

**User input:**
> /add-todo The search function in search.service.ts does a full table scan — needs to be optimized

## Expected Outcome

A single todo file is created in `.ai-project/todos/` (e.g., `001-optimize-search-full-table-scan.md`) with:

- A clear description of the full table scan performance issue
- The affected file (`src/services/search.service.ts`)
- A suggested fix approach (add database index, use indexed query)
- Proper metadata: priority, estimated effort, creation date, triggering context

The file follows the single canonical template defined in the skill's workflow section.

## Key Checkpoints

### 1. Clarification Step

The agent asks clarifying questions if metadata is missing:

- **Priority:** "What priority? (P0-critical, P1-high, P2-medium, P3-low)" — since the user did not specify
- **Effort:** "Estimated effort? (nano/small/medium/large)" — since the user did not specify
- The agent should NOT skip these questions and silently default to medium

**Pass criteria:** Agent asks about priority and effort before proceeding.

### 2. Single Consistent Template

The agent uses ONE template — the canonical template from the SKILL.md workflow section. It does not mix fields from different template sources or invent its own structure.

**Pass criteria:** The generated todo matches the canonical template exactly in structure (frontmatter fields, section headings, section order).

### 3. Correct File Location and Naming

The todo is written to `.ai-project/todos/` with a descriptive filename:

- Checks existing files to determine the next sequence number
- Uses the `NNN-{descriptive-name}.md` naming convention
- Example: `001-optimize-search-full-table-scan.md`

**Pass criteria:** File is created in `.ai-project/todos/` with correct naming convention.

### 4. Complete Content

The todo file contains all required sections with meaningful content:

```yaml
---
title: Optimize search function — eliminate full table scan
priority: P2
estimated_effort: small
created: 2026-02-23
context: Found during /implement session
---

## Description

The `searchItems()` function in `search.service.ts` performs a full table scan
on every query instead of using an indexed lookup. This causes degraded
performance as the dataset grows and will become a bottleneck in production.

## Affected Files

- `src/services/search.service.ts`

## Suggested Approach

1. Add a database index on the columns used in search filters
2. Rewrite the query to use the index (e.g., WHERE clause with indexed columns)
3. Add query performance tests to prevent regression

## Acceptance Criteria

- [ ] Search queries use indexed lookups instead of full table scans
- [ ] Query performance is measurably improved (benchmark before/after)
- [ ] No functional regression in search results
```

**Pass criteria:** All four sections (Description, Affected Files, Suggested Approach, Acceptance Criteria) are present and filled in with specifics, not placeholders.

### 5. Confirmation Gate

Before writing the file, the agent shows the complete todo content to the user and waits for approval.

**Pass criteria:** Agent displays the full file content and asks "Does this look good?" or equivalent before writing.

### 6. Success Confirmation

After writing, the agent confirms the file was created successfully, including the file path.

**Pass criteria:** Agent states the file path and confirms creation.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Agent uses different templates from different sections of the skill | Inconsistent output, confusing for consumers who expect one format |
| Agent writes the todo without showing the user first | No opportunity to catch errors or adjust priority/approach |
| Agent skips asking about priority/effort when not provided | Silent defaults lead to inaccurate metadata; the whole point of todos is accurate triage |
| Agent creates the todo in the wrong directory | Breaks discoverability and tooling that reads from `.ai-project/todos/` |
| Agent treats a P0-critical issue as a todo instead of suggesting `/debug` or `/implement` | Critical in-scope issues should be fixed now, not deferred |
| Agent includes fields from multiple conflicting templates | Mixing `id`, `status`, `queue_position`, `labels` from old templates with the canonical template creates noise |

## Known Gaps Addressed

The following gaps existed in the original skill and have been resolved:

1. **4 conflicting template sources** — Consolidated to a single canonical template in the SKILL.md workflow section. The `_template.md` in the init assets and the example todo in references now align with this template.
2. **No confirmation gate** — Added a required approval step before writing the file.
3. **No clarification step** — Added required questions for missing priority and effort metadata.
4. **No "wrong tool" guidance for critical issues** — Added guidance to suggest `/debug` or `/implement` for P0-critical items in current scope.
