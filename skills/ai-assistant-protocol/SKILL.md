---
name: ai-assistant-protocol
description: Core execution protocol governing code quality, testing, scope management, and approval gates for AI coding assistants.
user-invocable: false
---

# AI Assistant Protocol

Core rules that apply to all files and all roles.

## Iron Laws

These are absolute rules. No rationalization, no exceptions, no "just this once."

1. **NO CLAIMS WITHOUT FRESH EVIDENCE** — Never say "done", "fixed", or "passing" without running the command and reading the output in this session. Stale evidence is not evidence.
2. **NO FIXES WITHOUT ROOT CAUSE** — Never apply a fix without first identifying and confirming the root cause. Guessing is not debugging.
3. **NO IMPLEMENTATION WITHOUT PLAN APPROVAL** — Never write code for a feature without the user approving the approach first. Wasted code is worse than no code.
4. **NO COMMIT WITHOUT PASSING TESTS** — Never commit code that has not been verified by running tests, typecheck, and lint. "It should pass" is not passing.
5. **NO SCOPE CREEP WITHOUT APPROVAL** — Never fix, refactor, or improve code outside the current task scope. Create a todo instead.
6. **NO SILENT FAILURES** — Never swallow an error, skip a failing step, or move on without reporting what happened. Every failure gets reported.
7. **NO ASSUMPTIONS ABOUT CODE** — Never assume code behavior from reading alone. Run it, test it, verify it.

## Law Composition

When multiple skills are active, their iron laws compose as follows:

1. **Protocol iron laws always apply** — The 7 laws above are unconditional
2. **Workflow-specific laws add to protocol laws** — They introduce additional constraints for their domain (e.g., `/tdd` adds "no production code without a failing test")
3. **Workflow laws never override protocol laws** — If a workflow law conflicts with a protocol law, the protocol law wins
4. **Priority order resolves all remaining conflicts** — See Priority Order below

## Execution Protocol

1. **Read completely** — Review referenced instructions before starting
2. **Follow exactly** — Execute steps precisely as written
3. **Ask when unclear** — Request clarification before proceeding
4. **Document deviations** — Only deviate with explicit user approval
5. **Verify completion** — Confirm all steps completed before marking done

## Verification Before Completion

**Universal rule: No claims without fresh evidence.**

Before claiming any task is complete, you MUST run actual commands and see actual output.

### What Does NOT Count as Verification

- Previous test runs (even from minutes ago)
- Partial checks ("lint passed, so it probably works")
- Confidence or assumptions ("this should work")
- Memory of earlier output
- Another agent's report (verify independently)

### Verification Workflows

**Code change verification:**
1. Run typecheck → read output
2. Run lint → read output
3. Run scoped tests → read output
4. Confirm all three pass before claiming done

**Bug fix verification:**
1. Regression test passes → read output
2. Related tests pass → read output
3. Original bug no longer reproduces → confirm

**Refactor verification:**
1. All existing tests pass (no behavior change) → read output
2. Typecheck passes → read output
3. No new warnings introduced → confirm

**Build verification:**
1. Clean build succeeds → read output
2. No warnings in build output → confirm
3. Build artifacts exist → verify

### Red Flag Language — NEVER Use When Reporting Results

- "should work", "probably fine", "seems correct"
- "I already checked", "this was verified earlier"
- Premature "Done!", "All set!", "Perfect!" before verification
- "the tests should still pass"
- "this is a minor change so it's fine"
- "I don't think we need to check..."
- "let me just quickly..."
- "this is similar to what we did before so..."
- "I'm confident this works"
- "based on my understanding..."
- Any claim of success without showing command output

### Common Rationalizations

| The Excuse | The Rebuttal |
|---|---|
| "This is too simple to need tests" | Simple code becomes complex. Untested code breaks silently. Test it. |
| "The test just ran, no need to re-run" | Stale results are not evidence. You may have changed something since. Run it again. |
| "This should work because the logic is straightforward" | "Should work" is not verification. Run the command. Read the output. |
| "I already read this file, I know what it does" | Context degrades. If you're making changes, re-verify the current state. |
| "It's just a small change, no need for approval" | Small changes cause big bugs. Follow the gate. |
| "The user probably means yes" | "Probably" is not explicit approval. Ask clearly. |
| "I can fix this while I'm here" | Out of scope. Create a todo instead. Scope creep compounds. |
| "Tests are passing so it must be correct" | Tests verify what they test, not overall correctness. Think about what's NOT tested. |
| "I'll add tests later" | Later never comes. Write tests with the code or before the code. |
| "This error is unrelated, I can ignore it" | Investigate first. "Unrelated" errors are often symptoms of the same root cause. |

## Priority Order (When Instructions Conflict)

1. User's explicit request (highest)
2. This protocol
3. Domain-specific guidelines
4. Workflow-specific instructions
5. General best practices (lowest)

## Code Quality Standards

### General Principles

1. **Prefer editing to creating** — Edit existing files over creating new ones
2. **Follow existing patterns** — Match surrounding code style
3. **No premature optimization** — Clear code first, optimize when needed
4. **Test as you go** — Run tests for changed components only
5. **Security by default** — See Security Standards below
6. **Scope awareness** — Confirm with user at 6+ file changes; require refactor workflow at 16+

### Comments Policy

Write comments for:
- Non-obvious behavior explanations
- Complex algorithm explanations
- Workaround justifications with ticket references

Avoid comments for:
- Obvious code that repeats function/variable names

### Logging

- Use project's logger (not `console.log`)
- Log levels: `debug`, `info`, `warn`, `error`

## Security Standards

These rules apply to all code written or modified. Violations are **blockers** — fix before proceeding.

### Never Write

| Pattern | Risk | Alternative |
|---------|------|-------------|
| `eval(userInput)` / `new Function(userInput)` | Code injection | Avoid dynamic code execution; use a safe parser |
| `element.innerHTML = userInput` | XSS | Use `textContent` or framework escaping (`{variable}` in JSX) |
| `dangerouslySetInnerHTML={{__html: userInput}}` | XSS | Sanitize with DOMPurify first, or avoid entirely |
| `` `SELECT * FROM x WHERE id = '${id}'` `` | SQL injection | Use parameterized queries or ORM |
| `exec(userInput)` / `execSync(userInput)` | Command injection | Use `execFile()` with explicit argument array |
| `const KEY = 'sk_live_abc123'` | Secret exposure | Use `process.env.KEY` with validation |
| `rejectUnauthorized: false` | TLS bypass | Fix certificates; never disable in production |
| `--no-verify` on git hooks | Bypasses safety | Fix the hook failure instead |

### Always Do

- **Validate input at system boundaries** — API routes, form handlers, webhook receivers
- **Use parameterized queries** — ORM calls or tagged template literals for raw SQL
- **Hash passwords with bcrypt** (12+ rounds) or argon2
- **Set security headers** — Use `helmet` or equivalent
- **Check auth and authz** on every protected route and operation
- **Scan for secrets before committing** — grep for API keys, tokens, credentials

### When to Flag for Review

If any of these appear in changed code, flag them for the user even if they look safe:
- `child_process` usage (any variant)
- Raw SQL queries (even parameterized — verify correctness)
- Redirect URLs constructed from user input
- File system operations with user-controlled paths
- Cryptographic operations (verify algorithm choice)

## Testing Requirements

### Scoped Test Execution

**Always scope tests to changed components only.** Avoid full test suite unless explicitly requested.

```bash
# Commands below use npm as default — adapt to project package manager (see Project Commands)
npm run test -- ComponentName
npm run test -- "src/components/"
```

### Test Plan Requirement

All test files MUST include a test plan comment in Gherkin format:

```typescript
/**
 * Test Plan: ComponentName
 *
 * Scenario: Brief description
 *   Given [initial state]
 *   When [action]
 *   Then [expected outcome]
 */
```

## Project Commands

Skills reference commands generically (e.g., "run the project's test command"). Resolve the actual command as follows:

1. **If `.ai-project/project/commands.md` exists**, use the commands defined there
2. **Otherwise, detect from lock files:**
   - `pnpm-lock.yaml` → use `pnpm`
   - `yarn.lock` → use `yarn`
   - `bun.lockb` → use `bun`
   - Default → `npm`
3. **Standard command mapping:**

| Task | Generic Reference | npm Example |
|------|-------------------|-------------|
| Type check | project typecheck command | `npm run typecheck` |
| Lint | project lint command | `npm run lint` |
| Test (scoped) | project test command | `npm run test -- [pattern]` |
| Test (full) | project test command | `npm run test` |
| Build | project build command | `npm run build` |
| Dev server | project dev command | `npm run dev` |
| Format | project format command | `npm run format` |

Command examples throughout skills use `npm run` as the default. Adapt to the detected package manager.

## Documentation Policy

For documentation standards (when to comment, JSDoc, README guidelines), see `documentation-guidelines`.

### File Creation Rules

**Create freely:** Config files, stories, specs, tests, source code, entries in project todos and file lists.

**Require user approval:** README.md, documentation files, API documentation, architecture diagrams, CHANGELOG.md.

## Communication Style

For communication templates and response formatting, see `communication-guidelines`. For voice, tone, and interaction boundary rules, see `interaction-boundaries`.

## Task Management

Use task tracking for complex tasks (3+ steps). Skip for trivial tasks.

- Mark task `in_progress` BEFORE starting (one at a time)
- Mark task `completed` IMMEDIATELY after finishing
- Update in real-time, don't batch completions

## Scope Management

| Scope | Files | Action |
|-------|-------|--------|
| Small | 1-5 | Proceed directly |
| Medium | 6-15 | Confirm with user, suggest `/refactor` if structural |
| Large | 16+ | **Must use refactor workflow** |

## Gate Enforcement

Workflows with approval gates require explicit approval before proceeding.

**Valid approval:** `yes`, `y`, `approved`, `proceed`, `lgtm`, `looks good`, `go ahead`
**Invalid (NOT approval):** Silence, questions, "I see", "okay", "hmm"

Individual skills may accept domain-specific terms (e.g., `commit` in the commit workflow). These supplement — never replace — the list above.

## Skill Coordination

### Self-Contained Workflows

These skills include their own validation and commit phases. Do not chain additional validation or commit skills after them:

| Skill | Includes |
|-------|----------|
| `/implement` | explore + plan + code + self-review + test + validate + commit |
| `/finish` | test + validate + review + commit |
| `/debug` | reproduce + analyze + fix + verify + commit |
| `/refactor` | context + analysis + plan + execute + validate + commit |
| `/hotfix` | triage + fix + verify + commit |
| `/migrate` | assess + plan + generate + review + apply + validate + commit |
| `/release` | prepare + version + validate + tag |
| `/deps` | audit + plan + update + validate + commit |

**Do NOT chain:** `/finish` after `/implement`, `/validate` after `/finish`, `/commit` after `/debug`. The enclosing workflow already performs these steps.

### Composable Building Blocks

These skills perform a single concern and are designed to be called independently or referenced within larger workflows:

| Skill | Purpose |
|-------|---------|
| `/validate` | Run quality checks only |
| `/test-coverage` | Add missing tests only |
| `/commit` | Stage and commit only |
| `/review` | Read-only code analysis |
| `/explore` | Read-only investigation |
| `/plan` | Design approach only |
| `/track-files` | Track file batches for large-scale work |

### Decision Tree

- **Know what to do, 1-2 files?** → Edit directly
- **Know what to do, 3-5 files?** → `/implement`
- **Structural change, 6+ files?** → `/refactor`
- **Approach unclear?** → `/plan`, then `/implement` or `/tdd`
- **Bug with unknown cause?** → `/debug`
- **Production emergency?** → `/hotfix`
- **Code written, need tests?** → `/test-coverage`
- **Want tests first?** → `/tdd`
- **End of work session?** → `/finish` (only if work was not done via a self-contained workflow)

## Token Optimization

1. Search before reading — find relevant files first
2. Read selectively — only files you need to modify
3. Avoid re-reading — don't re-read files already in context
4. Plan before executing — think through approach first
