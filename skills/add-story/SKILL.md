---
name: add-story
description: Create comprehensive Storybook stories with play functions and validated tests for a component. Use when a component needs Storybook coverage or story files.
category: meta
model: sonnet
effort: medium
triggers:
  - create story
  - storybook
  - component story
  - add stories
---

# Add Story

> **Purpose:** Create comprehensive Storybook stories with play functions and validated passing tests
> **Usage:** `/add-story <ComponentName or path>`

## Prerequisites

- **Storybook** installed and configured in the project
- **@storybook/test** for `expect`, `userEvent`, `within`, `waitFor`
- **MSW (Mock Service Worker)** if the component has API dependencies
- **@storybook/addon-interactions** for play function debugging

## Constraints

- **Do not modify the original component** without explicit permission
- **Do not run full test suites** (`npm test`) -- scope to the component
- **Do not use querySelector** in tests -- use Testing Library queries
- **Do not skip waitFor** for async assertions
- **Create play functions for all interactive scenarios**
- **Run tests and ensure they pass**
- **Use Testing Library queries** (getByRole, getByLabelText, etc.)
- **Scope tests appropriately** (canvas for component, screen for modals)

## Workflow

### Step 0: Verify Storybook Setup

Mechanical check — delegate to the `dispatch` subagent (haiku) rather than running inline: "Check whether Storybook is installed/configured in this repo (`.storybook/` dir, `storybook` in package.json) and detect the package manager (pnpm/yarn/bun/npm from lockfile). Report: installed yes/no, and PKG_MGR." Use its answer directly.

**If Storybook is not installed:** Inform the user and suggest installation. Do not proceed without Storybook.

### Step 1: Read the Component Structure

- Read the component file to understand props, slots, events, and behavior
- Identify component states and variants
- Note any conditional rendering or dynamic behavior
- List dependencies (API calls, stores, context providers)

### Step 2: Identify States to Cover

Identify the meaningful component states to cover (default, disabled, loading, error, etc.) before writing stories.

### Step 3: Review Existing Patterns

Before writing stories:
- Check existing stories in the project for conventions
- Identify mocking requirements (MSW, stores, providers)
- Note the project's Storybook configuration

**Story file location and naming:**

Search for existing story files to discover project conventions:
```bash
find . -name "*.stories.tsx" -o -name "*.stories.ts" -o -name "*.story.tsx" | head -5
```

Common patterns:
| Pattern | Example |
|---------|---------|
| `__stories__/` directory | `src/components/__stories__/Button.stories.tsx` |
| Colocated | `src/components/Button.stories.tsx` |
| Root stories dir | `stories/Button.stories.tsx` |

**Always follow the existing project convention.** If no stories exist, default to colocated (next to the component file).

### Step 4: Write Stories for Visual States

Create stories covering all visual states (default, disabled, loading, error, etc.). Use meta configuration with title, component, parameters, and autodocs tag. See `references/story-patterns.md` for templates and the factory pattern.

**Context providers and decorators:**

If the component uses React context (identified in Step 1), wrap stories with the required providers via decorators:

```typescript
const meta: Meta<typeof Component> = {
  component: Component,
  decorators: [
    (Story) => (
      <ThemeProvider theme={defaultTheme}>
        <Story />
      </ThemeProvider>
    ),
  ],
};
```

Check the component's imports for context usage:
- `useContext(SomeContext)` → needs `SomeContext.Provider` decorator
- `useTheme()`, `useAuth()`, etc. → needs the corresponding provider
- Router-dependent components → wrap with `MemoryRouter` or equivalent

### Step 5: Write Play Functions for Interactions

Add play functions for all interactive scenarios using `step()` blocks, Testing Library queries, and `waitFor` for async assertions. See `references/story-patterns.md` for play function examples.

### Step 6: Add Mocking If Required

For components with API dependencies, use MSW handlers in story parameters. See `references/testing-best-practices.md` for MSW patterns.

### Step 7: Run Tests and Validate

Delegate the run itself to `dispatch` (mechanical): "Run `$PKG_MGR run test-storybook -- --grep \"ComponentName\"` and report full pass/fail output." Only bring failures back into the main loop to diagnose and fix — re-run via `dispatch` after each fix until green. See `references/testing-best-practices.md` for debugging guidance.

## Story File Checklist

Before completing:

- [ ] Meta configuration complete (title, component, parameters)
- [ ] Default story exists
- [ ] All visual states covered (disabled, loading, error, etc.)
- [ ] Play functions for interactive scenarios
- [ ] MSW handlers for API dependencies (if applicable)
- [ ] Tests pass locally

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| STR-T1 | Positive | "Create a story for Button component" | Skill triggers |
| STR-T2 | Positive | "Add Storybook coverage for UserProfile" | Skill triggers |
| STR-T3 | Positive | "Write stories for this component" | Skill triggers |
| STR-T4 | Negative | "Write unit tests for this component" | Does NOT trigger (-> /test-coverage or /tdd) |
| STR-T5 | Negative | "How does this component work?" | Does NOT trigger (-> /explore) |
| STR-T6 | Boundary | "Test this component" | Context-dependent — if Storybook is the project's testing approach, trigger; otherwise route to /test-coverage |

## References

- `references/story-patterns.md` - Story templates, play functions, factory pattern
- `references/testing-best-practices.md` - MSW mocking, Testing Library queries, async handling, example workflow
