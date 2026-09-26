# Track Files — Verification Scenario

## Scenario

A developer needs to rename all `utils/*.helper.ts` files to `utils/*.util.ts` across a monorepo with 3 packages. They invoke `/track-files` to discover and track all affected files before using `/refactor` to apply the renames.

**Invocation:** `/track-files rename *.helper.ts to *.util.ts across all packages`

## Expected Outcome

A tracking manifest in `.ai-project/file-lists/` listing every `*.helper.ts` file in the repo, with per-file notes about what imports reference each file, ready for batch refactoring.

Example manifest at `.ai-project/file-lists/rename-helper-to-util.md`:

```markdown
# Rename *.helper.ts to *.util.ts

**Created:** 2025-07-10
**Status:** In Progress

## Search Criteria

How these files were identified:

```bash
# Glob search for all *.helper.ts files across the monorepo
find packages/*/src -name "*.helper.ts" -type f
```

## Selection Criteria

- Include: All `*.helper.ts` files under any `packages/*/` workspace
- Exclude: Files in `node_modules/`, `dist/`, or generated directories

## Progress

| Status | Count |
|--------|-------|
| Total | 9 |
| Completed | 0 |
| In Progress | 0 |
| Pending | 9 |
| Skipped | 0 |

## Files

### Pending

- [ ] `packages/core/src/utils/string.helper.ts` - Imported by 4 files (packages/core/src/services/formatter.ts, ...)
- [ ] `packages/core/src/utils/date.helper.ts` - Imported by 2 files (packages/core/src/models/event.ts, ...)
- [ ] `packages/core/src/utils/array.helper.ts` - Imported by 3 files; re-exported from packages/core/src/utils/index.ts
- [ ] `packages/api/src/utils/auth.helper.ts` - Imported by 5 files; used in middleware chain
- [ ] `packages/api/src/utils/validation.helper.ts` - Imported by 3 files
- [ ] `packages/api/src/utils/response.helper.ts` - Imported by 6 files; re-exported from barrel
- [ ] `packages/web/src/utils/dom.helper.ts` - Imported by 2 files
- [ ] `packages/web/src/utils/format.helper.ts` - Imported by 4 files; also imported cross-package from packages/core
- [ ] `packages/web/src/utils/test.helper.ts` - Imported by 8 test files

### Completed

### Skipped
```

## Key Checkpoints

| # | Checkpoint | What to verify |
|---|-----------|----------------|
| 1 | Agent searches the actual codebase for matching files | Agent runs glob patterns (e.g., `**/*.helper.ts`) and/or grep to discover files. Does NOT ask the user to provide the list manually. |
| 2 | Agent finds files across all 3 packages | Results include files from `packages/core/`, `packages/api/`, and `packages/web/` (or equivalent workspace directories). Not limited to project root. |
| 3 | Each tracked file has a note about its importers/dependents | For each discovered file, the agent greps for import statements referencing that file and records a brief dependency note (e.g., "Imported by 4 files"). |
| 4 | User is shown the full list and asked to confirm before persisting | Agent presents the complete discovered file list with notes and explicitly asks the user to confirm, exclude files, or adjust before writing the manifest. |
| 5 | Manifest file is written to `.ai-project/file-lists/` | After user confirmation, the agent writes the tracking manifest to `.ai-project/file-lists/rename-helper-to-util.md` (or similar descriptive name). |
| 6 | Agent reports count and asks what to do next | After persisting, agent reports the total file count and suggests next steps: `/refactor` to apply renames, `/review` to inspect, etc. |

## Anti-patterns

| Anti-pattern | Why it fails |
|-------------|-------------|
| Agent asks the user to manually list files | Defeats the purpose of the skill. The agent must search the codebase itself. |
| Agent skips the actual codebase search | Without searching, the manifest will be incomplete or empty. The skill must perform real discovery. |
| Agent tracks files without showing the list first | User loses the ability to exclude files or correct mistakes. A confirmation gate is required. |
| Agent ignores files in sub-packages | In a monorepo, files exist across multiple packages. Searching only the root `src/` misses the majority of matches. |
| Agent writes the manifest before user confirms | Premature persistence. The user must review and approve the file list before it is written to disk. |
| Agent omits dependency context per file | Without noting importers/dependents, the downstream `/refactor` skill lacks the information needed to update all references. |

## Known Gaps

These are deficiencies in the current skill definition that this verification scenario exposes:

1. **No codebase search step** -- The skill never instructs the agent to actually search the codebase using glob or grep. It assumes the user provides files or the agent somehow knows them.
2. **No confirmation gate** -- The skill does not require the agent to present the discovered list and wait for user approval before writing the manifest.
3. **No per-file note guidance** -- The skill template includes a `{brief note}` placeholder but does not instruct the agent to gather dependency/importer context for each file.
4. **No monorepo awareness** -- The skill does not mention searching across workspaces, packages, or sub-projects. An agent following the skill literally would only search the project root.
