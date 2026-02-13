# Template Variables

When generating files, replace ALL `{{PLACEHOLDER}}` variables with actual values from detection and user input. No placeholder should remain unfilled.

## Variable Reference

| Placeholder | Source |
|-------------|--------|
| `{{PROJECT_NAME}}` | From package.json `name` field |
| `{{PROJECT_TYPE}}` | Detected (web app, library, CLI, etc.) |
| `{{FRAMEWORK}}` | Detected framework |
| `{{VERSION}}` | From package.json or detected |
| `{{BUILD_SYSTEM}}` | Detected build tool |
| `{{PACKAGE_MANAGER}}` | Detected (npm, yarn, pnpm) |
| `{{TEST_FRAMEWORK}}` | Detected test framework |
| `{{NODE_VERSION}}` | From .nvmrc or package.json engines |
| `{{MAIN_BRANCH}}` | From user input (default: main) |
| `{{FEATURE_BRANCH_PATTERN}}` | From user input |
| `{{PROJECT_DESCRIPTION}}` | From package.json `description` or detected |
| `{{LANGUAGE}}` | Detected language (e.g., TypeScript, JavaScript) |
| `{{DEV_COMMAND}}` | From package.json scripts (e.g., `npm run dev`) |
| `{{BUILD_COMMAND}}` | From package.json scripts (e.g., `npm run build`) |
| `{{TEST_COMMAND}}` | From package.json scripts (e.g., `npm run test`) |
| `{{LINT_COMMAND}}` | From package.json scripts (e.g., `npm run lint`) |
| `{{TYPECHECK_COMMAND}}` | From package.json scripts (e.g., `npm run typecheck`) |
| `{{CONVENTION_*}}` | Detected project conventions (replace with 2-4 items) |

## Rules

- **If a value cannot be detected:** Use a sensible default and add a comment noting it should be reviewed.
- **Replace ALL placeholders** -- No `{{PLACEHOLDER}}` variables may remain unfilled in generated files.

## Example Output Files

### commands.md

```markdown
# Project Commands

## Development
| Task | Command |
|------|---------|
| Dev server | `npm run dev` |
| Build | `npm run build` |

## Quality
| Task | Command |
|------|---------|
| Type check | `npm run typecheck` |
| Lint | `npm run lint` |

## Testing
| Task | Command |
|------|---------|
| Run tests | `npm run test` |
```

### structure.md

```markdown
# Project Structure

## Directory Layout
\`\`\`
src/
├── components/    # UI components
├── utils/         # Utility functions
├── hooks/         # Custom hooks
└── types/         # Type definitions
\`\`\`
```

### patterns.md

```markdown
# Code Patterns

## Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Utilities | camelCase | `formatDate.ts` |
```

### stack.md

```markdown
# Tech Stack

## Core Technologies
| Layer | Technology |
|-------|------------|
| Language | TypeScript |
| Framework | React |
| Testing | Vitest |
```
