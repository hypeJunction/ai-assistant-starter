---
name: add-story
description: Create comprehensive Storybook stories with test plans, play functions, and validated tests for a component. Use when a component needs Storybook coverage or story files.
triggers:
  - create story
  - storybook
  - component story
  - add stories
---

# Add Story

> **Purpose:** Create comprehensive Storybook stories with test plans, play functions, and validated passing tests
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
- **Test plan must be included** at top of story file
- **Create play functions for all interactive scenarios**
- **Run tests and ensure they pass**
- **Use Testing Library queries** (getByRole, getByLabelText, etc.)
- **Scope tests appropriately** (canvas for component, screen for modals)

## Workflow

### Step 1: Read the Component Structure

- Read the component file to understand props, slots, events, and behavior
- Identify component states and variants
- Note any conditional rendering or dynamic behavior
- List dependencies (API calls, stores, context providers)

### Step 2: Create a Test Plan

Document all meaningful component states to cover using Given/When/Then format. Include the test plan as a block comment at the top of the story file. See `references/story-patterns.md` for the test plan template.

### Step 3: Review Existing Patterns

Before writing stories:
- Check existing stories in the project for conventions
- Identify mocking requirements (MSW, stores, providers)
- Note the project's Storybook configuration

### Step 4: Write Stories for Visual States

Create stories covering all visual states (default, disabled, loading, error, etc.). Use meta configuration with title, component, parameters, and autodocs tag. See `references/story-patterns.md` for templates and the factory pattern.

### Step 5: Write Play Functions for Interactions

Add play functions for all interactive scenarios using `step()` blocks, Testing Library queries, and `waitFor` for async assertions. See `references/story-patterns.md` for play function examples.

### Step 6: Add Mocking If Required

For components with API dependencies, use MSW handlers in story parameters. See `references/testing-best-practices.md` for MSW patterns.

### Step 7: Run Tests and Validate

```bash
npm run test-storybook -- --grep "ComponentName"
```

Fix failures, re-run until all pass. See `references/testing-best-practices.md` for debugging guidance.

## Story File Checklist

Before completing:

- [ ] Test plan documented at top of file
- [ ] Meta configuration complete (title, component, parameters)
- [ ] Default story exists
- [ ] All visual states covered (disabled, loading, error, etc.)
- [ ] Play functions for interactive scenarios
- [ ] MSW handlers for API dependencies (if applicable)
- [ ] Tests pass locally

## References

- `references/story-patterns.md` - Story templates, play functions, factory pattern, test plan format
- `references/testing-best-practices.md` - MSW mocking, Testing Library queries, async handling, example workflow
