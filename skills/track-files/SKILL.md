---
name: track-files
description: Track batches of files that need similar changes for large-scale work. Use when refactoring affects many files, migrating patterns, or coordinating batch operations across sessions.
category: meta
triggers:
  - batch operation
  - track files
  - many files to change
  - file list
---

# Track Files

> **Purpose:** Track batches of files that need similar changes for large-scale work
> **Usage:** `/track-files <description of what to track>`

## Constraints

- **Always search the codebase** -- Use glob patterns and grep to find matching files. Do not rely on the user to provide the full list.
- **Always search across all packages** -- In monorepos, search all workspaces and sub-packages, not just the project root.
- **Always document search criteria** -- Record how files were found so the list can be reproduced
- **Always document skip reasons** -- Explain why any file was excluded
- **Always confirm before persisting** -- Present the discovered file list to the user and wait for confirmation before writing the manifest
- **Keep progress updated** -- Move files between sections as work progresses

## Prerequisites

Requires `.ai-project/file-lists/` directory (created by `/init`). If the directory does not exist, create it or suggest running `/init`.

## When to Create a File List

Create a file list when:

- Refactoring affects more than 5 files
- Migrating patterns across the codebase
- Batch operations need progress tracking
- Multiple files need the same type of change
- Work spans multiple sessions

## Workflow

### Step 1: Understand the Pattern

Clarify what needs to be tracked:

1. What file pattern, naming convention, or code pattern defines the set?
2. What operation will be performed on these files? (rename, refactor, migrate, etc.)
3. Are there directories or patterns to exclude?

### Step 2: Search the Codebase

Search the codebase using glob patterns and grep to find all matching files. Do not rely on the user to provide the full list.

- Use glob patterns to match file names (e.g., `**/*.helper.ts`)
- Use grep to find files containing specific patterns (e.g., imports, function calls)
- **In monorepos:** Search across all packages, workspaces, and sub-projects -- not just the project root. Check for `packages/`, `apps/`, workspace configurations in `package.json`, `pnpm-workspace.yaml`, or similar.
- Exclude `node_modules/`, `dist/`, build output, and generated files

**If no files match the search criteria:** Report "No files match the specified pattern — nothing to track" and exit.

### Step 3: Gather Per-File Context

For each discovered file, note relevant context that helps the downstream batch operation:

- **What imports it** -- Grep for import/require statements referencing the file. Note the count and list key dependents.
- **What it exports** -- Summarize the public API (exported functions, types, classes).
- **Special handling needed** -- Re-exports from barrel files, cross-package imports, circular dependencies, or other considerations.

This context helps the batch operation skill (e.g., `/refactor`) understand the full impact of changes.

### Step 4: Confirm with User

**GATE: Present the full discovered file list to the user before persisting.**

Show:
- Total count of discovered files
- Each file path with its per-file context note
- The search criteria used (so the user can verify completeness)

Wait for the user to confirm. The user may want to:
- Exclude specific files
- Add files that were missed
- Adjust the scope

Do NOT write the manifest until the user approves the list.

### Step 5: Create the Manifest

After user confirmation, create a new file in `.ai-project/file-lists/`:

```bash
.ai-project/file-lists/{descriptive-name}.md
```

**Naming conventions:**
- Use kebab-case
- Be descriptive: `components-without-tests.md`, `refactor-api-calls.md`

Write the manifest with the following structure:

```markdown
# {Title}

**Created:** {date}
**Status:** In Progress | Complete | Paused

## Search Criteria

How these files were identified:

\`\`\`bash
# Command used to find files
grep -r "pattern" src/ --include="*.ts"
find packages/*/src -name "*.helper.ts" -type f
\`\`\`

## Selection Criteria

- Include: {what makes a file relevant}
- Exclude: {what disqualifies a file}
```

### Step 6: List the Files

Organize with checkboxes for tracking. Each file must include a context note describing its dependents, exports, or special handling:

```markdown
## Files

### Pending

- [ ] `src/components/Button.ts` - Imported by 3 files (Form.ts, Page.ts, index.ts); exports ButtonProps type
- [ ] `src/components/Input.ts` - Imported by 2 files; re-exported from barrel
- [ ] `src/services/api.ts` - Imported by 5 files; cross-package import from packages/web

### In Progress

- [ ] `src/components/Form.ts` - Started, waiting for review

### Completed

- [x] `src/utils/helpers.ts` - Done
- [x] `src/utils/formatters.ts` - Done

### Skipped

- `src/legacy/old.ts` - Reason: deprecated, will be removed
```

### Step 7: Add Progress Summary and Report

Track overall progress:

```markdown
## Progress

| Status | Count |
|--------|-------|
| Total | 25 |
| Completed | 10 |
| In Progress | 2 |
| Pending | 12 |
| Skipped | 1 |

**Last Updated:** {date}
```

After writing the manifest, report to the user:
- Total file count and breakdown
- Where the manifest was saved
- Suggested next steps: `/refactor` to apply changes, `/review` to inspect, or continue tracking manually

## Example File List

```markdown
# Components Without Stories

**Created:** 2025-01-15
**Status:** In Progress

## Search Criteria

Vue components without corresponding Storybook stories:

\`\`\`bash
# Find Vue files without stories
for f in $(find src/components -name "*.vue"); do
  story="${f%.vue}.stories.ts"
  if [ ! -f "$story" ]; then
    echo "$f"
  fi
done
\`\`\`

## Selection Criteria

- Include: Vue components in `src/components/`
- Exclude: Layout wrappers, internal components with `_` prefix

## Progress

| Status | Count |
|--------|-------|
| Total | 15 |
| Completed | 5 |
| In Progress | 1 |
| Pending | 8 |
| Skipped | 1 |

**Last Updated:** 2025-01-16

## Files

### Pending

- [ ] `src/components/buttons/PrimaryButton.vue` - Interactive component
- [ ] `src/components/buttons/SecondaryButton.vue` - Interactive component
- [ ] `src/components/forms/TextField.vue` - Form input
- [ ] `src/components/forms/SelectField.vue` - Form input
- [ ] `src/components/cards/UserCard.vue` - Display component
- [ ] `src/components/cards/ProductCard.vue` - Display component
- [ ] `src/components/modals/ConfirmModal.vue` - Modal component
- [ ] `src/components/modals/AlertModal.vue` - Modal component

### In Progress

- [ ] `src/components/navigation/Sidebar.vue` - Complex component, drafting stories

### Completed

- [x] `src/components/buttons/IconButton.vue` - 3 stories created
- [x] `src/components/forms/Checkbox.vue` - 4 stories created
- [x] `src/components/forms/Radio.vue` - 3 stories created
- [x] `src/components/indicators/Badge.vue` - 2 stories created
- [x] `src/components/indicators/Spinner.vue` - 2 stories created

### Skipped

- `src/components/_internal/PortalTarget.vue` - Internal utility, no visual output

## Notes

- Prioritizing interactive components first
- Form components need accessibility testing in stories
```

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| TRK-T1 | Positive | "Track all files that need migration" | Skill triggers |
| TRK-T2 | Positive | "Create a file list for the refactor" | Skill triggers |
| TRK-T3 | Positive | "Find all components without stories" | Skill triggers |
| TRK-T4 | Negative | "Rename all helpers to utils" | Does NOT trigger (-> /refactor) |
| TRK-T5 | Negative | "Find how this function is used" | Does NOT trigger (-> /explore) |
| TRK-T6 | Boundary | "List all files that use the old API pattern" | Triggers (tracking files for batch operation) |
| TRK-T7 | Early-exit | No files match the search criteria | Reports "No files match" and exits |

## Working with File Lists

### During Refactoring

1. Move file from "Pending" to "In Progress"
2. Make the changes
3. Verify changes (type check, tests)
4. Move file to "Completed" with note
5. Update progress counts

### When Skipping Files

Always document why:

```markdown
### Skipped

- `src/legacy/old.ts` - Reason: deprecated, will be removed in v2
- `src/generated/types.ts` - Reason: auto-generated, changes would be overwritten
```

### Resuming Work

When returning to a file list:

1. Check current status
2. Review "In Progress" items
3. Continue with next "Pending" item
4. Update progress summary

## Archiving Completed Lists

When all files are processed:

1. Update status to "Complete"
2. Add completion date
3. Optionally move to a completed folder or archive

```markdown
# Components Without Stories

**Created:** 2025-01-15
**Completed:** 2025-01-20
**Status:** Complete

...
```
