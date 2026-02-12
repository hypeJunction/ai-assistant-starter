---
name: finish
description: End-of-session routine. Ensures test coverage, runs validation, performs self-review, and commits cleanly. Use when finishing a unit of work.
---

# Finish

> **Purpose:** Systematically conclude a unit of work — test, validate, review, commit
> **Usage:** `/finish`

## Constraints

- Never commit with failing tests
- Never skip validation (minimum: type check + lint)
- Never commit `any` types without documenting as todo
- Never force push without explicit request
- Never commit secrets

## Related Skills

This skill performs lightweight end-of-session versions of these workflows:
- `/test-coverage` — Phase 2 (test coverage check)
- `/validate` — Phase 3 (quality validation)
- `/review` — Phase 4 (self-review)
- `/commit` — Phase 6 (commit changes)

For more thorough execution of any phase, use the individual skill.

## Workflow

### Phase 1: Assess Current State

```bash
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

git branch --show-current
git status --short
git log --oneline $MAIN..HEAD
```

**Decision:** If uncommitted changes exist, run full workflow. If only commits, skip to Phase 4 (Review).

### Phase 2: Cover with Tests

Ensure changed code has test coverage.

1. **Identify changed files:**
   ```bash
   git diff --name-only $MAIN..HEAD
   git diff --name-only
   ```

2. **Check for missing tests:** Each changed `.ts` file should have a `.spec.ts`

3. **Create missing tests** with Gherkin test plans

4. **Run tests:**
   ```bash
   npm run test -- ChangedComponent
   ```

**Exit criteria:** All changed code has tests, all tests pass.

### Phase 3: Validate

Run checks in order — stop and fix if any fail:

```bash
npm run typecheck
npm run lint
npm run test -- "path/to/changed/"
```

**Exit criteria:** All checks pass.

### Phase 4: Review

Self-review before committing:

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

3. **Security checklist:**
   - [ ] No hardcoded secrets, API keys, or credentials
   - [ ] No `eval()`, `innerHTML`, or `dangerouslySetInnerHTML` with unsanitized input
   - [ ] No raw SQL with string interpolation
   - [ ] No `child_process.exec()` with user-controlled input
   - [ ] Input validation present at system boundaries
   - [ ] No disabled security controls (`rejectUnauthorized: false`)

4. **Note issues by severity:**
   - Critical — must fix before commit
   - Warning — should fix, document if deferred
   - Suggestion — nice to have

**Exit criteria:** No critical issues. Warnings documented if deferred.

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

### Phase 7: Final Verification (Optional)

If preparing to push:
```bash
git log -1 --stat
git status
```

## Output Format

```markdown
## Wrap Summary

### Work Assessed
- **Branch:** feature/my-feature
- **Files changed:** 5

### Test Coverage
- utility.spec.ts - created, 6 tests passing

### Validation
- Type checking - passed
- Linting - passed
- Scoped tests - 10/10 passing

### Review
- No critical issues

### Commit
- Committed: `feat: add data export feature`
- SHA: abc1234

---
Wrap complete!
```
