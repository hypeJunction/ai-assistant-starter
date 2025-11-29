# AI Assistant Starter Template

A comprehensive starter template for setting up AI coding assistant instructions in your project. This template provides structured guidance for AI assistants like Claude Code, GitHub Copilot, and others.

## Quick Start

1. **Copy to your project:**
   ```bash
   cp -r .ai-assistant .claude CLAUDE.md /path/to/your/project/
   ```

2. **Customize for your project:**
   - Edit `CLAUDE.md` with your project's commands
   - Update `.ai-assistant/.memory.md` with your tech stack
   - Update `.ai-assistant/.context.md` with common patterns
   - Add domain-specific instructions as needed

3. **Start using:**
   - AI assistants will read `CLAUDE.md` as the entry point
   - Use slash commands like `/validate`, `/refactor`, `/happy-hour`

## Structure Overview

```
your-project/
├── CLAUDE.md                    # Entry point for AI assistants
├── .ai-assistant/               # Detailed instructions
│   ├── .instructions.md         # Global rules
│   ├── .memory.md               # Project context (customize)
│   ├── .context.md              # Quick reference (customize)
│   ├── INDEX.md                 # Documentation index
│   ├── chatmodes/               # Role-based behaviors
│   │   ├── developer.chatmode.md
│   │   ├── tester.chatmode.md
│   │   ├── reviewer.chatmode.md
│   │   └── architect.chatmode.md
│   ├── domains/                 # Technology-specific rules
│   │   ├── typescript.instructions.md
│   │   └── testing.instructions.md
│   ├── workflows/               # Step-by-step procedures
│   │   ├── validate.prompt.md
│   │   ├── refactor.prompt.md
│   │   ├── happy-hour.prompt.md
│   │   └── ...
│   ├── decisions/               # Architecture Decision Records
│   ├── todos/                   # Technical debt tracking
│   ├── history/                 # Significant work records
│   └── file-lists/              # Batch operation tracking
├── .claude/                     # Claude Code configuration
│   ├── settings.json            # Permissions and settings
│   └── commands/                # Slash commands
└── .github/
    └── copilot-instructions.md  # GitHub Copilot config
```

## What's Included

### Core Instructions

- **Global rules** for code quality, testing, documentation
- **Scope management** for large-scale changes
- **Communication style** guidelines
- **Task tracking** with todos and file lists

### Chatmodes (Role-Based Behavior)

- **Developer** - Full access for implementation
- **Tester** - Focus on test creation and quality
- **Reviewer** - Read-only code review
- **Architect** - Design and planning focus

### Workflows

- **Validate** - Type checking, linting, tests
- **Refactor** - Systematic multi-file changes
- **Happy Hour** - End-of-session wrap-up routine
- **Intent** - Context gathering before implementation

### Domain Templates

- **TypeScript** - Type usage, patterns, best practices
- **Testing** - Test plans, patterns, mocking

## Customization Guide

### Step 1: Update Project Context

Edit `.ai-assistant/.memory.md`:

```markdown
## Project Overview

**Name:** `your-project-name`
**Type:** web application
**Purpose:** Your project description

### Technology Stack

- **Framework:** React / Vue / Angular
- **Language:** TypeScript 5.x
- **Build System:** Vite / Webpack
- **Testing:** Vitest / Jest
```

### Step 2: Add Quick Reference

Edit `.ai-assistant/.context.md`:

```markdown
## Common Import Patterns

\`\`\`typescript
// Your common imports
import { yourUtility } from './utils';
\`\`\`

## Common Commands

\`\`\`bash
npm run dev     # Your dev command
npm run test    # Your test command
\`\`\`
```

### Step 3: Customize Commands

Edit `CLAUDE.md`:

```markdown
## Quick Commands

\`\`\`bash
npm run dev          # Your dev server
npm run test         # Your test command
npm run typecheck    # Your type check
\`\`\`
```

### Step 4: Add Domain Instructions

Create domain files for your technologies:

- `.ai-assistant/domains/react.instructions.md`
- `.ai-assistant/domains/vue.instructions.md`
- `.ai-assistant/domains/api.instructions.md`

### Step 5: Update Permissions

Edit `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run test:*)",
      "Bash(npm run lint:*)",
      "Bash(your-safe-commands:*)"
    ]
  }
}
```

## Placeholders to Replace

Search for these placeholders and replace with your values:

| Placeholder | Description |
|-------------|-------------|
| `{{PROJECT_NAME}}` | Your project name |
| `{{PROJECT_TYPE}}` | Type of project |
| `{{PROJECT_DESCRIPTION}}` | Brief description |
| `{{FRAMEWORK}}` | Main framework |
| `{{BUILD_SYSTEM}}` | Build tool |
| `{{TEST_FRAMEWORK}}` | Testing framework |
| `{{MAIN_BRANCH}}` | Default branch name |
| `{{DATE}}` | Current date |

## Key Concepts

### Instruction Hierarchy

1. User's explicit request (highest)
2. Global instructions (`.instructions.md`)
3. Domain instructions (e.g., `typescript.instructions.md`)
4. Workflow instructions (e.g., `refactor.prompt.md`)
5. General best practices (lowest)

### Scope Management

| Scope | Files | Action |
|-------|-------|--------|
| Small | 1-5 | Proceed directly |
| Medium | 6-20 | Confirm with user |
| Large | 21+ | Use refactor workflow |

### Task Tracking

- **Todos** - Document shortcuts and technical debt
- **File Lists** - Track multi-file operations
- **History** - Record significant work

## Best Practices

1. **Keep instructions focused** - Don't overload with rules
2. **Update context regularly** - Keep `.memory.md` current
3. **Document decisions** - Use ADRs for architectural choices
4. **Track technical debt** - Use todos for deferred work
5. **Use workflows** - Follow established procedures

## Contributing

Feel free to adapt this template for your needs. Consider sharing improvements back to help others.

## License

MIT - Use freely in your projects.
