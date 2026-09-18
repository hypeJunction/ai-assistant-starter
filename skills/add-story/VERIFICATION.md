# Add-Story Skill Verification

## Scenario

A developer runs `/add-story src/components/UserProfile.tsx` on a React component with the following characteristics:

- **Props:** `user: User`, `onEdit: () => void`, `isLoading: boolean`
- **Conditional rendering:** loading skeleton when `isLoading=true`, profile content when `false`
- **Context dependency:** uses `ThemeContext` from `src/contexts/ThemeContext` for styling
- **API dependency:** fetches preferences via `useEffect` calling `/api/users/:id/preferences`
- **Existing story convention:** stories live in `src/components/__stories__/Button.stories.tsx` (dedicated `__stories__/` directory, `.stories.tsx` suffix)
- **Package manager:** pnpm (`pnpm-lock.yaml` exists)
- **Storybook:** `.storybook/` config directory exists

## Expected Outcome

The agent verifies Storybook is installed, reads the component file, identifies the visual states to cover, discovers the existing story convention (`__stories__/` directory, `.stories.tsx` suffix), writes stories covering default, loading, and error states with play functions for interactions (edit button click), mocks the `/api/users/:id/preferences` endpoint with MSW, wraps all stories in a ThemeContext decorator, creates the file at `src/components/__stories__/UserProfile.stories.tsx`, and runs tests with `pnpm run test-storybook`.

## Key Checkpoints

### 1. Agent checks Storybook is installed

**Phase:** Step 0 (Verify Storybook Setup)

The agent checks for the `.storybook/` directory or `storybook` in `package.json` before proceeding. It also detects pnpm as the package manager from `pnpm-lock.yaml`.

**Pass criteria:** Agent confirms Storybook is present and identifies pnpm as the package manager.

### 2. Agent reads the component file to understand props, states, and dependencies

**Phase:** Step 1 (Read the Component Structure)

The agent reads `src/components/UserProfile.tsx` and identifies:
- Props: `user: User`, `onEdit: () => void`, `isLoading: boolean`
- Conditional rendering: loading skeleton vs. profile content
- Context dependency: `ThemeContext`
- API dependency: `useEffect` calling `/api/users/:id/preferences`

**Pass criteria:** Agent lists all props, conditional states, context usage, and API calls.

### 3. Agent discovers existing story convention

**Phase:** Step 3 (Review Existing Patterns)

The agent searches for existing story files and discovers the `__stories__/` directory pattern with `.stories.tsx` suffix from `src/components/__stories__/Button.stories.tsx`.

**Pass criteria:** Agent identifies the `__stories__/` directory convention and plans to use it for the new story file.

### 4. Default story renders profile content with mock user data

**Phase:** Step 4 (Write Stories for Visual States)

The Default story provides mock `user` data, `onEdit` callback, and `isLoading: false`. It renders the profile content (not the skeleton).

**Pass criteria:** Default story has complete args with realistic mock data.

### 5. Loading story renders skeleton with isLoading=true

**Phase:** Step 4 (Write Stories for Visual States)

The Loading story sets `isLoading: true` to render the skeleton state instead of profile content.

**Pass criteria:** Loading story exists with `isLoading: true` in args.

### 6. ThemeContext decorator wraps all stories via meta.decorators

**Phase:** Step 4 (Write Stories for Visual States)

Since the component uses `ThemeContext`, the meta configuration includes a decorator that wraps all stories with the ThemeContext provider.

**Pass criteria:** `meta.decorators` array contains a ThemeContext/ThemeProvider wrapper.

### 7. MSW handler mocks /api/users/:id/preferences endpoint

**Phase:** Step 6 (Add Mocking If Required)

The agent adds MSW handlers in story parameters to mock the `/api/users/:id/preferences` GET endpoint. An error story uses an MSW handler that returns a 500 status.

**Pass criteria:** MSW handler exists for `/api/users/:id/preferences` with both success and error variants.

### 8. Play function tests edit button click with userEvent.click() and assertion

**Phase:** Step 5 (Write Play Functions for Interactions)

A story with a play function simulates clicking the edit button using `userEvent.click()` on a button found via `getByRole('button', { name: ... })`. The play function uses `step()` blocks and `waitFor` for any async assertions.

**Pass criteria:** Play function uses Testing Library queries (not querySelector), userEvent.click(), and step() blocks.

### 9. Story file created at correct location

**Phase:** Step 4 (Write Stories for Visual States)

The story file is created at `src/components/__stories__/UserProfile.stories.tsx`, matching the project's existing convention discovered in checkpoint 3.

**Pass criteria:** File path is `src/components/__stories__/UserProfile.stories.tsx`, not colocated at `src/components/UserProfile.stories.tsx`.

### 10. Tests run with correct package manager

**Phase:** Step 7 (Run Tests and Validate)

The agent runs `pnpm run test-storybook -- --grep "UserProfile"`, using the package manager detected in Step 0.

**Pass criteria:** Command uses `pnpm`, not `npm` or `yarn`.

## Anti-Patterns

### 1. Creating story file in wrong location

**Wrong:** Agent creates `src/components/UserProfile.stories.tsx` (colocated) when the project uses the `__stories__/` directory convention.

The project already has `src/components/__stories__/Button.stories.tsx`, establishing a clear convention. Ignoring this convention creates inconsistency and makes stories harder to find for developers expecting the established pattern.

### 2. Not adding ThemeContext decorator

**Wrong:** Agent writes stories without wrapping them in the ThemeContext provider.

The component imports and uses `ThemeContext`. Without the provider decorator, all stories will crash at runtime with a missing context error. The agent must identify context dependencies in Step 1 and add corresponding decorators in Step 4.

### 3. Hardcoding npm when project uses pnpm

**Wrong:** Agent runs `npm run test-storybook` instead of `pnpm run test-storybook`.

The project has `pnpm-lock.yaml`, indicating pnpm is the package manager. Using npm may fail (missing node_modules structure) or produce different dependency resolution. The agent must detect and use the correct package manager.

### 4. Using querySelector instead of Testing Library queries in play functions

**Wrong:** Agent writes `canvasElement.querySelector('.edit-btn')` instead of `canvas.getByRole('button', { name: 'Edit' })`.

Testing Library queries are accessibility-first and resilient to implementation changes. querySelector couples tests to CSS classes or DOM structure, making them brittle and providing no accessibility coverage.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No Storybook prerequisite check | The skill listed Storybook as a prerequisite but never verified it was installed before proceeding | Added Step 0 that checks for `.storybook/` directory and `storybook` in package.json. If not found, inform the user and halt. |
| No package manager detection | Step 7 hardcoded `npm run test-storybook`, failing for pnpm/yarn/bun projects | Added package manager detection in Step 0 (checks lock files) and updated Step 7 to use the detected manager. |
| No file naming/location guidance | No guidance on where to create the story file or how to match existing project conventions | Added convention discovery in Step 3: search for existing stories, identify the pattern (\_\_stories\_\_/, colocated, root dir), and follow it. Default to colocated if no stories exist. |
| No context provider/decorator guidance | No instructions for wrapping stories with required React context providers | Added decorator guidance in Step 4: identify context usage from component imports and wrap stories with corresponding providers via meta.decorators. |
| No acceptance tests | No way to verify the skill triggers correctly or distinguish from similar skills like /test-coverage | Added acceptance tests table with positive, negative, and boundary cases for trigger routing. |
