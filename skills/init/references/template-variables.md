# Template Variables

When generating files, replace ALL `{{PLACEHOLDER}}` variables with actual values from detection and user input. No placeholder should remain unfilled.

## Variable Reference

### Core Project

| Placeholder | Source |
|-------------|--------|
| `{{PROJECT_NAME}}` | From package.json `name` field |
| `{{PROJECT_TYPE}}` | Detected (web app, library, CLI, etc.) |
| `{{PROJECT_DESCRIPTION}}` | From package.json `description` or detected |

### Technology Stack

| Placeholder | Source |
|-------------|--------|
| `{{LANGUAGE}}` | Detected language (e.g., TypeScript, JavaScript) |
| `{{LANGUAGE_VERSION}}` | Detected language version (e.g., 5.0) |
| `{{FRAMEWORK}}` | Detected framework (e.g., React, Vue, Next.js) |
| `{{FRAMEWORK_VERSION}}` | Detected framework version (e.g., 18.2) |
| `{{RUNTIME}}` | Detected runtime (e.g., Node.js, Bun, Deno) |
| `{{RUNTIME_VERSION}}` | From .nvmrc or package.json engines |
| `{{BUILD_SYSTEM}}` | Detected build tool (e.g., Vite, Webpack, esbuild) |
| `{{PACKAGE_MANAGER}}` | Detected (npm, yarn, pnpm) |
| `{{TEST_FRAMEWORK}}` | Detected test framework (e.g., Vitest, Jest) |
| `{{LINTER}}` | Detected linter (e.g., eslint, biome) |
| `{{FORMATTER}}` | Detected formatter (e.g., prettier, biome) |

### Commands

| Placeholder | Source |
|-------------|--------|
| `{{DEV_COMMAND}}` | From package.json scripts (e.g., `npm run dev`) |
| `{{BUILD_COMMAND}}` | From package.json scripts (e.g., `npm run build`) |
| `{{TEST_COMMAND}}` | From package.json scripts (e.g., `npm run test`) |
| `{{LINT_COMMAND}}` | From package.json scripts (e.g., `npm run lint`) |
| `{{TYPECHECK_COMMAND}}` | From package.json scripts (e.g., `npm run typecheck`) |
| `{{INSTALL_COMMAND}}` | From package manager (e.g., `npm ci`) |
| `{{LINT_FIX_COMMAND}}` | From package.json scripts (e.g., `npm run lint -- --fix`) |
| `{{TEST_COVERAGE_COMMAND}}` | From package.json scripts (e.g., `npm run test:coverage`) |

### Git & Workflow

| Placeholder | Source |
|-------------|--------|
| `{{MAIN_BRANCH}}` | From user input (default: main) |
| `{{FEATURE_BRANCH_PATTERN}}` | From user input |
| `{{CONVENTION_*}}` | Detected project conventions (replace with 2-4 items) |

### Directories & Files

| Placeholder | Source |
|-------------|--------|
| `{{SOURCE_DIR}}` | Detected source directory (e.g., src, lib, app) |
| `{{TEST_DIR}}` | Detected test directory (e.g., tests, __tests__, src) |
| `{{ENTRY_POINT}}` | Detected entry point (e.g., index.ts, main.ts) |

Templates also contain structural placeholders (e.g., `{{PROJECT_STRUCTURE}}`, `{{COMPONENT_TEMPLATE}}`, `{{IMPORT_ORDER}}`) that are populated from codebase analysis rather than simple key-value detection. These are filled contextually during generation — see the template files themselves for the full set.

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
