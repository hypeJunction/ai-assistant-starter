---
name: init
description: Bootstrap AI assistant with project-specific configuration by analyzing the codebase and generating populated template files. Use when setting up a new project or re-initializing after major changes.
---

# Init

> **Purpose:** Bootstrap AI assistant with project-specific information
> **Usage:** `/init [--quick] [--update]`
> **Output:** Populated project configuration files in `.ai-project/`

## Constraints

- **Interactive workflow** -- Do NOT skip confirmation questions
- **Replace ALL placeholders** -- No `{{PLACEHOLDER}}` variables may remain unfilled in generated files
- **Preserve existing customizations** when using `--update`
- **Ask before overwriting** if `.ai-project/` already exists

## Generated Files

| Location | File | Purpose |
|----------|------|---------|
| `.ai-project/` | `.memory.md` | Project tech stack and architecture |
| `.ai-project/` | `.context.md` | Common imports and patterns |
| `.ai-project/` | `config.md` | Project configuration overrides |
| `.ai-project/project/` | `commands.md` | Project scripts and commands |
| `.ai-project/project/` | `structure.md` | Directory layout |
| `.ai-project/project/` | `patterns.md` | Code patterns and conventions |
| `.ai-project/project/` | `stack.md` | Technology stack |
| `.ai-project/domains/` | `*.instructions.md` | Stack-specific domain rules |

## Workflow

### Phase 0: Create Project Layer

#### Step 0.1: Check for Existing Project Layer

```bash
ls -la .ai-project 2>/dev/null
```

If `.ai-project/` exists, ask user:
- **Overwrite:** Replace with fresh template
- **Update:** Keep existing, only add missing files
- **Skip:** Proceed to analysis without copying

#### Step 0.2: Copy Project Template

Copy the template from `assets/ai-project/` within this skill directory to `.ai-project/` at the project root.

```bash
cp -r <skill-dir>/assets/ai-project .ai-project

# Verify structure
ls -la .ai-project/
```

Creates:
- `.ai-project/.memory.md` -- Project memory template
- `.ai-project/.context.md` -- Quick reference template
- `.ai-project/config.md` -- Configuration overrides
- `.ai-project/project/` -- Project configuration
- `.ai-project/domains/` -- Stack-specific domain rules (populated in Phase 2)
- `.ai-project/workflows/` -- Custom workflow extensions
- `.ai-project/todos/` -- Technical debt tracking
- `.ai-project/history/` -- Work history
- `.ai-project/decisions/` -- ADRs
- `.ai-project/file-lists/` -- Batch tracking

### Phase 1: Analyze Project

#### Step 1.1: Read Package Configuration

```bash
cat package.json 2>/dev/null || cat Cargo.toml 2>/dev/null || cat pyproject.toml 2>/dev/null
```

Extract:
- Project name
- Dependencies
- Available scripts
- Build tools

#### Step 1.2: Understand Directory Structure

```bash
# Get project structure (excluding common ignores)
find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
  | grep -v node_modules | grep -v dist | head -50

# Or use tree if available
tree -I 'node_modules|dist|.git' -L 3
```

Extract:
- Source directories
- Test locations
- Configuration files
- Entry points

#### Step 1.3: Identify Patterns

```bash
# Find component patterns
head -30 src/components/*.tsx 2>/dev/null | head -50

# Find test patterns
head -30 src/**/*.spec.ts 2>/dev/null | head -50

# Find import patterns
grep -rn "^import" src/ --include="*.ts" | head -20
```

Extract:
- Component structure
- Test patterns
- Import conventions
- Naming conventions

#### Step 1.4: Identify Tech Stack

Look for:
- Framework (React, Vue, Angular, etc.)
- Test framework (Jest, Vitest, etc.)
- Build tool (Vite, Webpack, etc.)
- Linter (ESLint config)
- Formatter (Prettier config)

### Phase 1.5: Interactive Confirmation

**Present detected configuration and ask for confirmation:**

```markdown
## Project Analysis Complete

I've analyzed your project. Here's what I detected:

### Basic Info
| Field | Detected Value | Correct? |
|-------|----------------|----------|
| Project Name | `my-app` | ? |
| Project Type | Web Application | ? |

### Tech Stack
| Layer | Detected | Correct? |
|-------|----------|----------|
| Language | TypeScript 5.x | ? |
| Framework | React 18 | ? |
| Build Tool | Vite | ? |
| Test Framework | Vitest | ? |
| Package Manager | npm | ? |

### Commands
| Task | Detected Command | Correct? |
|------|------------------|----------|
| Dev | `npm run dev` | ? |
| Build | `npm run build` | ? |
| Test | `npm run test` | ? |
| Lint | `npm run lint` | ? |
| Type Check | `npm run typecheck` | ? |

---
**Is this detection accurate?**

Reply with:
- `yes` or `correct` - All looks good, continue
- `fix: [field] = [value]` - Correct a specific field
- `show more` - See additional detected information
```

**GATE: Wait for confirmation before proceeding.**

### Phase 1.6: Gather Preferences

**Ask about project conventions:**

```markdown
## Project Preferences

A few questions to complete setup:

### Git Workflow
1. **Main branch name?**
   Default: `main`

2. **Feature branch pattern?**
   Examples: `feature/description`, `ft/TICKET-description`
   Default: `feature/[description]`

### Commit Style
3. **Commit message format?**
   - (A) Conventional: `feat: add login`
   - (B) Ticket prefix: `PROJ-123: Add login`
   - (C) Simple: `Add login feature`
   Default: (A) Conventional

### Testing
4. **Test file location?**
   - (A) Co-located: `Component.spec.ts` next to `Component.ts`
   - (B) Separate: `tests/` directory
   - (C) Both
   Default: (A) Co-located

---
Reply with your preferences (or press Enter for defaults):
```

**GATE: Wait for preferences before generating files.**

### Phase 2: Generate Configuration

**CRITICAL:** When generating files, replace ALL `{{PLACEHOLDER}}` variables with actual values from detection and user input. No placeholder should remain unfilled.

#### Template Population Rules

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

**If a value cannot be detected:** Use a sensible default and add a comment noting it should be reviewed.

#### Step 2.1: Write .ai-project/project/commands.md

Based on `package.json` scripts, generate:

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

#### Step 2.2: Write .ai-project/project/structure.md

Based on directory analysis:

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

#### Step 2.3: Write .ai-project/project/patterns.md

Based on code analysis:

```markdown
# Code Patterns

## Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Utilities | camelCase | `formatDate.ts` |
```

#### Step 2.4: Write .ai-project/project/stack.md

Based on dependencies:

```markdown
# Tech Stack

## Core Technologies
| Layer | Technology |
|-------|------------|
| Language | TypeScript |
| Framework | React |
| Testing | Vitest |
```

#### Step 2.5: Generate Domain Context Files

Generate project-specific domain instruction files in `.ai-project/domains/` based on detected stack. These complement the base background skills (installed via skills.sh) with project-specific conventions.

**Domain Detection Rules:**

| Detection | Generate When |
|-----------|---------------|
| Language: TypeScript | `package.json` has TypeScript |
| Language: Python | `pyproject.toml` or `requirements.txt` exists |
| Test: Vitest | Vitest in devDependencies |
| Test: Jest | Jest in devDependencies |
| Test: Pytest | pytest in Python deps |
| Framework: React | React in dependencies |
| Framework: Vue | Vue in dependencies |
| Framework: Express | Express in dependencies |
| Framework: FastAPI | FastAPI in Python deps |
| Storybook | Storybook in devDependencies |
| ORM: Prisma | Prisma in dependencies |
| ORM: Drizzle | Drizzle in dependencies |
| Validation: Zod | Zod in dependencies |
| Validation: Pydantic | Pydantic in Python deps |
| Docker | Dockerfile exists |
| CI: GitHub Actions | `.github/workflows/` exists |

**What to generate:** For each detected domain, create a `<domain>.instructions.md` file containing project-specific conventions observed from the codebase (e.g., import patterns, naming conventions, test organization). These override and supplement the generic base guideline skills.

**Example generated file:**
```markdown
<!-- .ai-project/domains/typescript.instructions.md -->
# TypeScript — Project Conventions

## Import Order
1. Node built-ins
2. External packages
3. Internal aliases (@/components, @/utils)
4. Relative imports

## Path Aliases
- `@/` maps to `src/`
- `@test/` maps to `tests/`

## Patterns
- Prefer `type` imports for type-only usage
- Use barrel exports in `index.ts` files
```

Present to user which domains were detected:

```markdown
### Domain Context Generated

Based on your stack, project-specific domain files were created in `.ai-project/domains/`:

**Detected domains:**
- typescript.instructions.md (TypeScript detected)
- vitest.instructions.md (Vitest detected)
- react.instructions.md (React detected)

These contain project-specific conventions observed from your codebase.
Base domain guideline skills (installed via skills.sh) provide generic best practices.
Project domain files take precedence when rules conflict.
```

#### Step 2.6: Update Project Entry Point

Generate/update `CLAUDE.md` at the project root:
- Should be minimal — project name, stack summary, key commands
- Reference `.ai-project/` for detailed configuration
- Skills are provider-agnostic (managed by skills.sh)

### Phase 3: Verify

#### Step 3.1: Review Generated Files

Show summary of what was generated:

```markdown
## Initialization Complete

### Files Created/Updated
- [x] `.ai-project/` - Project layer directory
- [x] `.ai-project/.memory.md` - Project memory
- [x] `.ai-project/.context.md` - Quick reference
- [x] `.ai-project/project/commands.md` - Commands
- [x] `.ai-project/project/structure.md` - Structure
- [x] `.ai-project/project/patterns.md` - Patterns
- [x] `.ai-project/project/stack.md` - Tech stack
- [x] `.ai-project/domains/` - Domain context (N files generated)
- [x] `CLAUDE.md` - Project entry point updated

### Detected Configuration
- **Language:** [detected]
- **Framework:** [detected]
- **Test Runner:** [detected]
- **Package Manager:** [detected]

### Next Steps
1. Review generated files for accuracy
2. Customize domain instructions in `.ai-project/domains/` if needed
3. Add project-specific patterns
4. Update any incorrect commands
```

#### Step 3.2: Ask for Review

```markdown
**Review the generated configuration?** (yes / looks good / modify [file])
```

## Quick Mode

For faster initialization:

```
/init --quick
```

Generates minimal configuration without deep analysis:
- Basic commands from package.json
- Simple directory structure
- Default patterns

## Re-initialization

To update after project changes:

```
/init --update
```

- Preserves custom additions
- Updates detected patterns
- Refreshes command list
