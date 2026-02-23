# Test Coverage — Verification Scenario

## Scenario

A developer has just implemented a new `UserService` class in `src/services/user.service.ts` with methods `createUser()`, `updateUser()`, and `deleteUser()`. The branch has 4 changed files. They invoke `/test-coverage` to ensure adequate test coverage before merging.

## Expected Outcome

New test file `src/services/user.service.spec.ts` exists with tests covering all 3 methods, including happy paths and error cases. Coverage measurement shows the new code is covered. A report shows what was tested and any remaining gaps.

## Key Checkpoints

1. **Agent identifies changed files on the branch** — Runs `git diff --name-only` against the base branch (e.g., `main`) and lists all 4 changed files.
2. **Agent discovers existing test file locations and patterns** — Searches for existing test files (`*.spec.ts`, `*.test.ts`, `__tests__/`) to determine naming convention, directory structure (co-located vs separate), import style, and mock patterns.
3. **Agent measures current coverage baseline** — Checks for coverage tooling (vitest.config, jest.config, package.json scripts) and runs coverage on affected files to establish a baseline before writing new tests.
4. **Agent categorizes each changed file by verification type** — Classifies files as needing unit tests, integration tests, or skip (type-only, config-only, generated code).
5. **Agent matches existing test patterns** — Reads 1-2 existing test files and adopts their describe/it structure, setup/teardown patterns, assertion style, and mock approach.
6. **Agent writes tests that follow project conventions** — Creates `src/services/user.service.spec.ts` with tests for `createUser()`, `updateUser()`, and `deleteUser()`, covering happy paths, error paths, and edge cases, using the patterns discovered in checkpoint 5.
7. **Agent runs the new tests and they pass** — Executes the test file and confirms all tests are green before proceeding.
8. **Agent measures coverage after adding tests** — Re-runs coverage to show improvement (before vs after) on the affected files.
9. **User is shown a coverage report and asked to approve** — Agent presents a structured report (files tested, coverage percentages, tests written, gaps remaining) and waits for explicit user approval before committing.

## Anti-patterns

- Agent should NOT skip measuring actual coverage despite the skill being named "test-coverage."
- Agent should NOT write tests without first discovering existing test patterns in the project.
- Agent should NOT assume test file locations without checking the project's conventions.
- Agent should NOT create tests for type-only files (e.g., `types.ts`, `interfaces.ts`).
- Agent should NOT commit test files without presenting a coverage report and receiving user approval.
- Agent should NOT use a generic test structure when the project has established conventions that differ.

## Known Gaps (Pre-Improvement)

- The skill never measures actual coverage despite the name — no baseline or post-test measurement step.
- No approval gate — tests are written and reported without waiting for user confirmation before committing.
- No test file location discovery step — the agent may create tests in the wrong directory or with the wrong naming convention.
- No existing pattern matching guidance — the agent may produce tests that do not match the project's established style.
- No early exit for "nothing to do" — if all changed files are type-only or already covered, the agent proceeds through the full workflow unnecessarily.
