---
name: init
description: Bootstrap AI assistant with project-specific configuration by analyzing the codebase and generating populated template files. Use when setting up a new project or re-initializing after major changes.
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

#### Step 1.2: Understand Directory Structure

```bash
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  | grep -v node_modules | grep -v dist | head -50
tree -I 'node_modules|dist|.git' -L 3 2>/dev/null
```

Extract: source directories, test locations, configuration files, entry points.

#### Step 1.3: Identify Patterns

```bash
head -30 src/components/*.tsx 2>/dev/null | head -50
head -30 src/**/*.spec.ts 2>/dev/null | head -50
grep -rn "^import" src/ --include="*.ts" | head -20
```

Extract: component structure, test patterns, import conventions, naming conventions.

#### Step 1.4: Identify Tech Stack

Detect: framework, test framework, build tool, linter (ESLint), formatter (Prettier).

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

#### Step 2.1-2.4: Write Project Files

Generate the following files using detected values and user preferences. See `references/template-variables.md` for example output formats:

- `.ai-project/project/commands.md` -- Based on `package.json` scripts
- `.ai-project/project/structure.md` -- Based on directory analysis
- `.ai-project/project/patterns.md` -- Based on code analysis
- `.ai-project/project/stack.md` -- Based on dependencies

#### Step 2.5: Generate Domain Context Files

Detect stack components and generate project-specific domain instruction files. See `references/domain-detection.md` for the full detection table, generation rules, and example output.

#### Step 2.6: Update Project Entry Point

Generate/update `CLAUDE.md` at the project root:
- Should be minimal -- project name, stack summary, key commands
- Reference `.ai-project/` for detailed configuration
- Skills are provider-agnostic

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

## References

- [Domain Detection](references/domain-detection.md) — Detection rules table and example generated domain files
- [Template Variables](references/template-variables.md) — Full variable table and population rules for generated files
