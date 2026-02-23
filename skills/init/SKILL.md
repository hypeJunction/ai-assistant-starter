---
name: init
description: Bootstrap AI assistant with project-specific configuration by analyzing the codebase and generating populated template files. Use when setting up a new project or re-initializing after major changes.
category: meta
triggers:
  - new project
  - bootstrap
  - initialize
  - set up project
  - first time setup
---

# Init

> **Purpose:** Bootstrap AI assistant with project-specific information
> **Usage:** `/init [--quick] [--update]`
> **Output:** Populated project configuration files in `.ai-project/`

## Constraints

- **Interactive workflow** -- Do NOT skip confirmation questions
- **Replace ALL placeholders** -- No `{{PLACEHOLDER}}` variables may remain unfilled in generated files (see `references/template-variables.md`)
- **Preserve existing customizations** when using `--update`
- **Ask before overwriting** if `.ai-project/` already exists

## Generated Files

| Location | File | Purpose |
|----------|------|---------|
| `.ai-project/` | `.memory.md` | Project tech stack and architecture |
| `.ai-project/` | `.context.md` | Common imports and patterns |
| `.ai-project/` | `config.yaml` | Project configuration overrides |
| `.ai-project/project/` | `commands.md` | Project scripts and commands |
| `.ai-project/project/` | `structure.md` | Directory layout |
| `.ai-project/project/` | `patterns.md` | Code patterns and conventions |
| `.ai-project/project/` | `stack.md` | Technology stack |
| `.ai-project/domains/` | `*.instructions.md` | Stack-specific domain rules |
| Root | `CLAUDE.md` | Project entry point for AI assistants |

## Workflow

### Phase 0: Create Project Layer

#### Step 0.1: Check for Existing Project Layer

```bash
ls -la .ai-project 2>/dev/null
```

If `.ai-project/` exists **and is fully populated** (`.memory.md`, `.context.md`, `config.yaml`, and `project/` files all contain real content without `{{PLACEHOLDER}}` variables), inform the user:

> `.ai-project/` already exists and appears fully configured. Would you like to:
> - **Re-initialize:** Start fresh (overwrites existing files)
> - **Update:** Keep existing, refresh detected patterns
> - **Exit:** Nothing to do

**GATE: Wait for user response. If user chooses Exit, stop here.**

If `.ai-project/` exists but is partially populated or contains placeholders, ask user:
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

The `assets/ai-project/` directory contains all scaffolding templates for project configuration, domains, workflows, todos, history, decisions, and file-lists. Refer to `assets/` for the full directory structure.

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

#### Step 1.2: Detect Package Manager

Detect the package manager from lockfile presence. Check in this order:

```bash
ls pnpm-lock.yaml 2>/dev/null && echo "pnpm" \
  || ls yarn.lock 2>/dev/null && echo "yarn" \
  || ls bun.lockb 2>/dev/null && echo "bun" \
  || ls package-lock.json 2>/dev/null && echo "npm" \
  || echo "npm"
```

| Lockfile | Package Manager | Install Command | Run Prefix |
|----------|----------------|-----------------|------------|
| `pnpm-lock.yaml` | pnpm | `pnpm install` | `pnpm run` |
| `yarn.lock` | yarn | `yarn install` | `yarn` |
| `bun.lockb` | bun | `bun install` | `bun run` |
| `package-lock.json` | npm | `npm ci` | `npm run` |

Use the detected package manager for ALL generated commands (dev, build, test, lint, etc.). Do NOT default to `npm` when another lockfile is present.

#### Step 1.3: Understand Directory Structure

```bash
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  | grep -v node_modules | grep -v dist | head -50
tree -I 'node_modules|dist|.git' -L 3 2>/dev/null
```

Extract: source directories, test locations, configuration files, entry points.

#### Step 1.4: Identify Patterns

```bash
head -30 src/components/*.tsx 2>/dev/null | head -50
head -30 src/**/*.spec.ts 2>/dev/null | head -50
grep -rn "^import" src/ --include="*.ts" | head -20
```

Extract: component structure, test patterns, import conventions, naming conventions.

#### Step 1.5: Identify Tech Stack

Detect: framework, test framework, build tool, linter (ESLint), formatter (Prettier).

Use these specific detection patterns for common stack components:

| Component | Detection Signal |
|-----------|-----------------|
| Next.js App Router | `next` in dependencies + `src/app/` or `app/` directory exists |
| Next.js Pages Router | `next` in dependencies + `src/pages/` or `pages/` directory exists |
| Tailwind CSS | `tailwindcss` in dependencies + `tailwind.config.*` file exists |
| Prisma | `@prisma/client` in dependencies + `prisma/schema.prisma` exists |
| Drizzle | `drizzle-orm` in dependencies + `drizzle.config.*` exists |
| tRPC | `@trpc/server` or `@trpc/client` in dependencies |
| Storybook | `@storybook/*` in devDependencies + `.storybook/` directory |
| Docker | `Dockerfile` or `docker-compose.yml` exists |
| GitHub Actions | `.github/workflows/` directory exists |

### Phase 1.5: Interactive Confirmation

**Present detected configuration and ask for confirmation:**

```markdown
## Project Analysis Complete

## Project Analysis Results

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

**Confirm detection accuracy:** (yes / fix: [field]=[value] / show more)
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
**Select preferences:** (provide answers or accept defaults)
```

**GATE: Wait for preferences before generating files.**

### Phase 2: Generate Configuration

**CRITICAL:** Replace ALL `{{PLACEHOLDER}}` variables with actual values from detection and user input. See `references/template-variables.md` for the full variable table and population rules.

#### Step 2.1: Populate `.memory.md` with Real Architecture Information

Scan the codebase to populate `.ai-project/.memory.md` with real architecture information. Do NOT leave placeholder variables.

- **Project Overview:** Fill with actual project name, type, and description from `package.json`
- **Technology Stack:** Fill with detected framework, language version, build system, package manager, test framework, and Node version
- **Project Structure:** Replace the template tree with the actual directory layout observed in Phase 1
- **Architecture Decisions:** If no decisions are known yet, replace the placeholder row with "No decisions recorded yet" -- do NOT leave `{{DECISION}}` / `{{DATE}}` / `{{REASONING}}`
- **Domain Guidelines:** List the actual domain instruction files that will be generated in Step 2.5
- **Git Workflow:** Fill with user preferences from Phase 1.6
- **Known Issues:** Replace placeholder row with "None documented yet" -- do NOT leave `{{ISSUE}}` / `{{IMPACT}}` / `{{WORKAROUND}}`
- **Session Context:** Replace `{{RECENT_WORK}}` and `{{ONGOING_WORK}}` with "Initial project setup via /init"

Every `{{PLACEHOLDER}}` in `.memory.md` must be replaced. If a value is unknown, use a descriptive default (e.g., "Not detected -- review manually").

#### Step 2.2: Populate `.context.md` with Actual Import Patterns

Scan the codebase to populate `.ai-project/.context.md` with actual import patterns and references. Do NOT leave placeholder variables.

- **Common Import Patterns:** Extract real import statements from the codebase (from Phase 1.4 analysis). Include framework-specific imports (e.g., `next/image`, `next/link` for Next.js; `@prisma/client` for Prisma), utility imports, and test imports actually used in the project
- **Common Commands:** Replace with real commands using the detected package manager (e.g., `pnpm run test` not `npm run test`)
- **File Locations:** Replace `{{CATEGORY_*}}` and `{{SERVICE_STRUCTURE}}` with actual directory names observed in the codebase
- **Error Patterns:** Replace placeholder row with "None documented yet" -- do NOT leave `{{ERROR}}` / `{{CAUSE}}` / `{{SOLUTION}}`

Every `{{PLACEHOLDER}}` in `.context.md` must be replaced with real content or sensible defaults.

#### Step 2.3: Write `config.yaml` with Detected Settings

Write detected settings to `.ai-project/config.yaml`. Update the template defaults with actual detected values:

- Set `package_manager` to the detected value from Step 1.2
- Set `main_branch` to the user's preference from Phase 1.6
- Set `commit_style` to the user's preference from Phase 1.6
- Add a `detected` section at the end of the file:

```yaml
# --- Detected (auto-populated by /init) ---
detected:
  package_manager: pnpm          # from pnpm-lock.yaml
  domains:                        # stack components found
    - typescript
    - nextjs
    - prisma
    - tailwind
  source_dir: src                 # primary source directory
  test_dir: src                   # test file location (co-located)
  app_router: true                # Next.js App Router detected
```

#### Step 2.4: Write Project Files

Generate the following files using detected values and user preferences. See `references/template-variables.md` for example output formats:

- `.ai-project/project/commands.md` -- Based on `package.json` scripts (use detected package manager)
- `.ai-project/project/structure.md` -- Based on directory analysis
- `.ai-project/project/patterns.md` -- Based on code analysis
- `.ai-project/project/stack.md` -- Based on dependencies

#### Step 2.5: Generate Domain Context Files

Detect stack components and generate project-specific domain instruction files. See `references/domain-detection.md` for the full detection table, generation rules, and example output.

#### Step 2.6: Update Project Entry Point

Generate/update `CLAUDE.md` at the project root using `assets/CLAUDE.md` as the template:
- Replace all `{{PLACEHOLDER}}` variables with detected values
- If a `CLAUDE.md` already exists, merge new content below any existing user content
- The template is minimal by design -- project name, stack summary, key commands, and a pointer to `.ai-project/`
- Remove table rows for commands that don't exist (e.g., no typecheck script)
- Replace `{{CONVENTION_*}}` placeholders with 2-4 actual project conventions detected from the codebase (e.g., "Use PascalCase for components", "Co-located test files with `.spec.ts` extension")

### Phase 2.7: Pre-Write Confirmation

**Before writing any files to disk**, present the user with a summary of what will be created or modified:

```markdown
## Files to Write

The following files will be created/updated:

| File | Action | Key Content |
|------|--------|-------------|
| `.ai-project/.memory.md` | Create | Architecture: [framework] + [orm] + [css] |
| `.ai-project/.context.md` | Create | [N] import patterns extracted |
| `.ai-project/config.yaml` | Update | packageManager: [detected] |
| `.ai-project/project/commands.md` | Create | [N] commands |
| `.ai-project/project/structure.md` | Create | Directory layout |
| `.ai-project/project/patterns.md` | Create | Code conventions |
| `.ai-project/project/stack.md` | Create | [N] technologies |
| `.ai-project/domains/*.instructions.md` | Create | [list of domain files] |
| `CLAUDE.md` | Create/Update | Project entry point |

**Proceed with writing these files?** (yes / review [file] / modify [file])
```

**GATE: Wait for user approval before writing files to disk.**

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

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| INI-T1 | Positive | "Set up the AI assistant for this project" | Skill triggers |
| INI-T2 | Positive | "Bootstrap project configuration" | Skill triggers |
| INI-T3 | Positive | "Initialize the project" | Skill triggers |
| INI-T4 | Negative | "Create a new feature" | Does NOT trigger (-> /implement) |
| INI-T5 | Negative | "Update the documentation" | Does NOT trigger (-> /docs or /sync) |
| INI-T6 | Boundary | "Re-initialize after major refactor" | Triggers with --update flag |
| INI-T7 | Boundary | `.ai-project/` fully populated and user chooses Exit | Reports "Nothing to do" and exits |

## References

- [Domain Detection](references/domain-detection.md) — Detection rules table and example generated domain files
- [Template Variables](references/template-variables.md) — Full variable table and population rules for generated files
