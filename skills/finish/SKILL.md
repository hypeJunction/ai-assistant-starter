---
name: finish
description: End-of-session routine. Ensures test coverage, performs self-review, runs validation, and commits cleanly. Use when finishing a unit of work.
category: process
triggers:
  - done for now
  - wrap up
  - end of session
  - finishing up
---

# Finish

> **Purpose:** Systematically conclude a unit of work — test, review, validate, commit
> **Usage:** `/finish`

## Constraints

- Never commit with failing tests
- Never skip validation (minimum: type check + lint)
- Never commit `any` types without documenting as todo
- Never force push without explicit request
- Never commit secrets

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Related Skills

This skill performs lightweight end-of-session versions of these workflows:
- `/test-coverage` — Phase 2 (test coverage check)
- `/review` — Phase 3 (self-review)
- `/validate` — Phase 4 (quality validation, runs after review fixes)
- `/commit` — Phase 6 (commit changes)
- `/adr` + `/add-todo` — Phase 8 (close completed todos)

For more thorough execution of any phase, use the individual skill.

## Workflow

### Phase 1: Assess Current State

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

git branch --show-current
git status --short
git log --oneline $MAIN..HEAD
```

**If no uncommitted changes and no commits ahead of base branch:** Report "Nothing to finish — working tree is clean and branch is up to date" and exit.

**Decision:** If uncommitted changes exist, run full workflow. If only commits, skip to Phase 3 (Review).

### Phase 2: Cover with Tests

Ensure changed code has test coverage.

1. **Identify changed files:**
   ```bash
   git diff --name-only $MAIN..HEAD
   git diff --name-only
   ```

2. **Check for missing tests:** Each changed `.ts` file should have a `.spec.ts`

3. **Create missing tests** with Gherkin test plans. If a test cannot be created (e.g., no testing framework configured, untestable code pattern, missing test utilities), report this to the user with the reason rather than silently skipping. Let the user decide whether to proceed without coverage for that file.

4. **Run tests:**
   ```bash
   npm run test -- ChangedComponent
   ```

5. **Fix failing tests:** If any tests fail, investigate and fix the cause. Re-run to confirm the fix.

**Phase 2 evidence:**
```markdown
### Test Coverage
- component.spec.ts — created, 4 tests passing
- utils.spec.ts — existing, 3 tests passing
- SKIPPED: config.ts — no testable exports (reported to user)
```

**Exit criteria:** All changed code has tests (or gaps reported to user), all tests pass.

### Phase 3: Review

Self-review before validation. Fixes made here will be validated in Phase 4.

1. **Get the diff:**
   ```bash
   git diff HEAD
   git diff --staged
   ```

2. **Review checklist:**
   - [ ] No `any` types
   - [ ] Proper TypeScript patterns
   - [ ] Tests have test plans
   - [ ] No `console.log` statements

3. **`any` type handling:** If `any` types are found, fix them with proper types before proceeding. Common replacements:
   - `any` -> `unknown` for truly unknown types (e.g., error handlers, generic middleware)
   - `any` -> specific interface/type for known shapes (e.g., API responses, props)
   - `any` -> generic type parameter (`<T>`) for reusable utilities
   - If an `any` type genuinely cannot be replaced (rare — e.g., third-party library constraint), document it as a todo with `/add-todo` and add a `// TODO:` comment explaining why

4. **Security checklist:**
   - [ ] No hardcoded secrets, API keys, or credentials
   - [ ] No `eval()`, `innerHTML`, or `dangerouslySetInnerHTML` with unsanitized input
   - [ ] No raw SQL with string interpolation
   - [ ] No `child_process.exec()` with user-controlled input
   - [ ] Input validation present at system boundaries
   - [ ] No disabled security controls (`rejectUnauthorized: false`)

5. **Note issues by severity:**
   - Critical — must fix before commit (includes `any` types)
   - Warning — should fix, document if deferred
   - Suggestion — nice to have

6. **Fix all critical issues** before proceeding to validation.

**Phase 3 evidence:**
```markdown
### Review
- Found 2 `any` types — fixed (UserProfile.tsx, formatUser.ts)
- No security issues
- No console.log statements
- 0 critical issues remaining
```

**Exit criteria:** No critical issues. Warnings documented if deferred.

### Phase 4: Validate

Run checks in order — stop and fix if any fail. This phase runs AFTER review to ensure review fixes have not introduced new issues.

```bash
npm run typecheck
npm run lint
npm run test -- "path/to/changed/"
```

**Re-validation loop:** If any check fails, fix the issue and re-run all validation checks from the beginning. Maximum 3 iterations. If validation still fails after 3 iterations, report the remaining failures to the user and ask how to proceed.

**Phase 4 evidence:**
```markdown
### Validation
- Typecheck: PASSED (0 errors)
- Lint: PASSED (0 warnings)
- Scoped tests: 10/10 passing
- Iterations: 1 (passed on first run)
```

**Exit criteria:** All checks pass.

### Phase 5: Docs (Optional)

Prompt whether documentation is needed:
- `ai` — Update AI context
- `user` — User documentation
- `readme` — README
- `skip` — No documentation

**Wait for response.**

### Phase 6: Commit

**Requires explicit user confirmation.**

1. Stage changes
2. Review staged diff
3. Show commit preview and ask for confirmation
4. Only after "yes": commit

```markdown
Ready to commit with message:
\`\`\`
<type>: <concise description>
\`\`\`

**Confirm commit?** (yes / edit message / cancel)
```

**Do NOT commit without explicit approval.**

### Phase 7: Final Verification and Next Steps

Present structured exit options (see `references/finish-options.md` for the full decision tree, post-merge verification, and session summary template).

If preparing to push:
```bash
git log -1 --stat
git status
```

### Phase 8: Close Todos

Check for todos completed by the work in this session.

1. **Scan for related todos:**
   ```bash
   ls .ai-project/todos/*.md 2>/dev/null
   ```

2. **For each open todo**, compare its acceptance criteria and affected files against the committed changes. If all criteria are met:
   - Invoke `/adr --from-todo <todo-file>` if the work involved design decisions (chose between approaches, adopted a pattern, established a convention)
   - **Skip the ADR** if the work was purely mechanical
   - Delete the completed todo file
   - Stage and commit the ADR creation and todo deletion together

3. **Report closures:**
   ```markdown
   ### Todos Closed
   - `refactor-api-client.md` — closed, ADR created: `api-client-pattern.md`
   - `add-input-validation.md` — closed, no ADR needed
   ```

**Skip this phase** if no `.ai-project/todos/` directory exists or no todos match the session's work.

## Output Format

```markdown
## Wrap Summary

### Work Assessed
- **Branch:** feature/my-feature
- **Files changed:** 5

### Test Coverage
- utility.spec.ts — created, 6 tests passing
- helper.spec.ts — existing, 3 tests passing

### Review
- Found 1 `any` type — fixed (utility.ts: `any` -> `UtilityResult`)
- No security issues
- 0 critical issues remaining

### Validation
- Typecheck: PASSED
- Lint: PASSED
- Scoped tests: 10/10 passing
- Iterations: 1

### Commit
- Committed: `feat: add data export feature`
- SHA: abc1234

### Todos Closed
- `refactor-api-client.md` — closed, ADR: `api-client-pattern.md`
- (or: No todos matched this session's work)

```

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| FIN-T1 | Positive | "I'm done for now" | Skill triggers |
| FIN-T2 | Positive | "Wrap up this session" | Skill triggers |
| FIN-T3 | Positive | "Finishing up" | Skill triggers |
| FIN-T4 | Negative | "Commit my changes" | Does NOT trigger (→ /commit) |
| FIN-T5 | Negative | "Run the tests" | Does NOT trigger (→ /validate) |
| FIN-T6 | Negative | "Review the code" | Does NOT trigger (→ /review) |
| FIN-T7 | Boundary | "Done, commit and push" | Triggers (finish encompasses commit) |
