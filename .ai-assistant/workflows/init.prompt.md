# Workflow: Initialize Project

> **Purpose:** Bootstrap AI assistant with project-specific information
> **Chatmode:** Explorer → Developer
> **Output:** Populated project configuration files
> **Command:** `/init [--quick] [--update]`

## Overview

This workflow sets up the project layer for the AI assistant framework. It copies the `.ai-project/` template from `.ai-assistant/` and populates it with project-specific information.

## Interactive Setup

**IMPORTANT:** This workflow uses an interactive wizard to gather project information. Do NOT skip the questions - they ensure proper configuration.

### Wizard Flow

```
┌────────────────────────────────────────────────────────────────┐
│ Step 1: Analyze Project                                         │
│ - Read package.json / config files                              │
│ - Detect frameworks, tools, structure                           │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ Step 2: Confirm Detection                                       │
│ - Show what was detected                                        │
│ - Ask user to confirm or correct                                │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ Step 3: Ask About Preferences                                   │
│ - Main branch name                                              │
│ - Branch naming convention                                      │
│ - Test patterns                                                 │
│ - Any custom rules                                              │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│ Step 4: Generate Configuration                                  │
│ - Create .ai-project/ with populated templates                  │
│ - NO {{PLACEHOLDER}} variables left unfilled                    │
└────────────────────────────────────────────────────────────────┘
```

## Prerequisites

The `.ai-assistant/` directory must exist (symlink to cloned repo, or local copy).

## Generated Files

| Location | File | Purpose |
|----------|------|---------|
| `.ai-project/` | `.memory.md` | Project tech stack and architecture |
| `.ai-project/` | `.context.md` | Common imports and patterns |
| `.ai-project/project/` | `commands.md` | Project scripts and commands |
| `.ai-project/project/` | `structure.md` | Directory layout |
| `.ai-project/project/` | `patterns.md` | Code patterns and conventions |
| `.ai-project/project/` | `stack.md` | Technology stack |
| Root | Provider entry point | e.g., `CLAUDE.md`, `.cursorrules` |

---

## Phase 0: Create Project Layer

### Step 0.1: Check for Existing Project Layer

```bash
# Check if .ai-project already exists
ls -la .ai-project 2>/dev/null
```

If `.ai-project/` exists, ask user:
- **Overwrite:** Replace with fresh template
- **Update:** Keep existing, only add missing files
- **Skip:** Proceed to analysis without copying

### Step 0.2: Copy Project Template

```bash
# Copy template from .ai-assistant
cp -r .ai-assistant/.ai-project .ai-project

# Verify structure
ls -la .ai-project/
```

Creates:
- `.ai-project/.memory.md` - Project memory template
- `.ai-project/.context.md` - Quick reference template
- `.ai-project/project/` - Project configuration
- `.ai-project/todos/` - Technical debt tracking
- `.ai-project/history/` - Work history
- `.ai-project/decisions/` - ADRs
- `.ai-project/file-lists/` - Batch tracking
- `.ai-project/domains/` - Override domain rules
- `.ai-project/workflows/` - Custom workflows

---

## Phase 1: Analyze Project (Explorer)

### Step 1.1: Read Package Configuration

```bash
# Find package manager and scripts
cat package.json 2>/dev/null || cat Cargo.toml 2>/dev/null || cat pyproject.toml 2>/dev/null
```

Extract:
- Project name
- Dependencies
- Available scripts
- Build tools

### Step 1.2: Understand Directory Structure

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

### Step 1.3: Identify Patterns

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

### Step 1.4: Identify Tech Stack

Look for:
- Framework (React, Vue, Angular, etc.)
- Test framework (Jest, Vitest, etc.)
- Build tool (Vite, Webpack, etc.)
- Linter (ESLint config)
- Formatter (Prettier config)

---

## Phase 1.5: Interactive Confirmation

**Present detected configuration and ask for confirmation:**

```markdown
## Project Analysis Complete

I've analyzed your project. Here's what I detected:

### Basic Info
| Field | Detected Value | Correct? |
|-------|----------------|----------|
| Project Name | `my-app` | ✓ / ✗ |
| Project Type | Web Application | ✓ / ✗ |

### Tech Stack
| Layer | Detected | Correct? |
|-------|----------|----------|
| Language | TypeScript 5.x | ✓ / ✗ |
| Framework | React 18 | ✓ / ✗ |
| Build Tool | Vite | ✓ / ✗ |
| Test Framework | Vitest | ✓ / ✗ |
| Package Manager | npm | ✓ / ✗ |

### Commands
| Task | Detected Command | Correct? |
|------|------------------|----------|
| Dev | `npm run dev` | ✓ / ✗ |
| Build | `npm run build` | ✓ / ✗ |
| Test | `npm run test` | ✓ / ✗ |
| Lint | `npm run lint` | ✓ / ✗ |
| Type Check | `npm run typecheck` | ✓ / ✗ |

---
**Is this detection accurate?**

Reply with:
- `yes` or `correct` - All looks good, continue
- `fix: [field] = [value]` - Correct a specific field
- `show more` - See additional detected information
```

**⏸️ Wait for confirmation before proceeding.**

---

## Phase 1.6: Gather Preferences

**Ask about project conventions:**

```markdown
## Project Preferences

A few questions to complete setup:

### Git Workflow
1. **Main branch name?**
   Default: `main`
   _Your answer:_

2. **Feature branch pattern?**
   Examples: `feature/description`, `ft/TICKET-description`
   Default: `feature/[description]`
   _Your answer:_

### Commit Style
3. **Commit message format?**
   - (A) Conventional: `feat: add login`
   - (B) Ticket prefix: `PROJ-123: Add login`
   - (C) Simple: `Add login feature`
   Default: (A) Conventional
   _Your choice:_

### Testing
4. **Test file location?**
   - (A) Co-located: `Component.spec.ts` next to `Component.ts`
   - (B) Separate: `tests/` directory
   - (C) Both
   Default: (A) Co-located
   _Your choice:_

---
Reply with your preferences (or press Enter for defaults):
```

**⏸️ Wait for preferences before generating files.**

---

## Phase 2: Generate Configuration (Developer)

**CRITICAL:** When generating files, replace ALL `{{PLACEHOLDER}}` variables with actual values from detection and user input. No placeholder should remain unfilled.

Write all files to `.ai-project/project/` directory.

### Template Population Rules

When writing `.ai-project/.memory.md` and `.ai-project/.context.md`:

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

### Step 2.1: Write .ai-project/project/commands.md

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

### Step 2.2: Write .ai-project/project/structure.md

Based on directory analysis:

```markdown
# Project Structure

## Directory Layout
```
src/
├── components/    # UI components
├── utils/         # Utility functions
├── hooks/         # Custom hooks
└── types/         # Type definitions
```
```

### Step 2.3: Write .ai-project/project/patterns.md

Based on code analysis:

```markdown
# Code Patterns

## Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Utilities | camelCase | `formatDate.ts` |

## Component Template
[Insert actual pattern from codebase]
```

### Step 2.4: Write .ai-project/project/stack.md

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

### Step 2.5: Update Provider Entry Point

Generate/update provider-specific entry point (e.g., `CLAUDE.md`, `.cursorrules`):
- Should be minimal, referencing `.ai-assistant/.instructions.md`
- Include quick command reference
- Link to detailed docs in `.ai-assistant/` and `.ai-project/`

---

## Phase 3: Verify

### Step 3.1: Review Generated Files

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
- [x] Provider entry point updated

### Detected Configuration
- **Framework:** [detected]
- **Test Runner:** [detected]
- **Package Manager:** [detected]

### Next Steps
1. Review generated files for accuracy
2. Add project-specific patterns
3. Update any incorrect commands
```

### Step 3.2: Ask for Review

```markdown
**Review the generated configuration?** (yes / looks good / modify [file])
```

---

## Quick Mode

For faster initialization:

```
/init --quick
```

Generates minimal configuration without deep analysis:
- Basic commands from package.json
- Simple directory structure
- Default patterns

---

## Re-initialization

To update after project changes:

```
/init --update
```

- Preserves custom additions
- Updates detected patterns
- Refreshes command list
