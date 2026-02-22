# Task Decomposition

How to break implementation work into verifiable micro-steps, handle surprises during execution, and maintain evidence-based progress.

## Decomposition Method

### The Micro-Step Pattern

Every feature can be decomposed into a sequence of steps where each step:
- Takes 2-5 minutes
- Targets exactly 1 file (occasionally 2 if tightly coupled)
- Has a single verifiable outcome
- Can be independently committed if needed

### Decomposition Flow

```
Feature Request
  └─ Break into components (what new modules/functions/types are needed?)
       └─ For each component:
            ├─ Write failing test (1 step)
            ├─ Verify test fails for right reason (1 step)
            ├─ Implement minimal code (1 step)
            ├─ Verify test passes (1 step)
            └─ Refactor if needed (1 step)
       └─ Integration:
            ├─ Wire components together (1 step per connection)
            ├─ Write integration test (1 step)
            └─ Verify end-to-end (1 step)
```

### Example: Decomposing "Add User Profile Page"

**Bad decomposition (too coarse):**
1. Create profile page component
2. Add API endpoint
3. Write tests

**Good decomposition (bite-sized):**
1. Add `UserProfile` type to `src/types/user.ts` → typecheck passes
2. Write failing test for `GET /api/users/:id` → test fails (route doesn't exist)
3. Add `GET /api/users/:id` route handler → test passes
4. Write failing test for `<UserProfile>` component → test fails
5. Create `<UserProfile>` component with props → test passes
6. Write failing test for profile data fetching hook → test fails
7. Add `useUserProfile(id)` hook → test passes
8. Wire hook into component → typecheck passes
9. Write integration test: render profile with mock data → test passes
10. Commit: `feat(profile): add user profile page with data fetching`

### Splitting Heuristics

| Signal | Action |
|--------|--------|
| Step touches 3+ files | Split by file |
| Step has "and" in description | Split at the "and" |
| Step requires >5 minutes | Find the midpoint deliverable |
| Step has no verify command | It's not a step — it's a description |
| Step says "implement the feature" | Decompose into sub-steps |

## Surprise Handling

When implementation deviates from the plan, follow these decision trees:

### Scope Expansion

The change requires more work than planned.

```
Scope expansion detected
  ├─ Is the extra work <15 minutes?
  │   ├─ Yes → Note it, include in current plan, inform user
  │   └─ No → STOP implementation
  │        ├─ Present the additional scope clearly
  │        ├─ Estimate additional effort
  │        ├─ Options: (a) expand plan, (b) defer to todo, (c) abort
  │        └─ Wait for user decision
  └─ Does it change the architecture?
      └─ Yes → STOP. Return to Phase 2 (Plan). New plan needed.
```

### Missing Dependency

A package, API, or module is needed that wasn't in the plan.

```
Missing dependency detected
  ├─ Is it a dev dependency (testing tool, type package)?
  │   └─ Note it, install, continue
  ├─ Is it a runtime dependency?
  │   ├─ Present: package name, version, size, license
  │   ├─ Alternatives: could we avoid the dependency?
  │   └─ Wait for approval before installing
  └─ Is it an internal module that doesn't exist yet?
      ├─ Can we stub it? → Stub and create a todo
      └─ Must we build it? → STOP. Expand plan.
```

### Design Conflict

The planned approach conflicts with existing code patterns.

```
Design conflict detected
  ├─ Is the existing pattern clearly intentional?
  │   └─ Yes → Adapt to match existing pattern. Update plan.
  ├─ Is the existing pattern outdated/inconsistent?
  │   ├─ Present both approaches with tradeoffs
  │   ├─ Recommend: follow existing pattern now, create refactor todo
  │   └─ Wait for user decision
  └─ Is the conflict a sign of a deeper architecture issue?
      └─ STOP. Explain the issue. May need `/explore` first.
```

### Existing Bug Found

Discovered a bug in code you're working near (not in your feature).

```
Existing bug found
  ├─ Does it block your implementation?
  │   ├─ Yes → Propose minimal workaround + create todo for proper fix
  │   └─ No → Create todo. Do NOT fix. Continue with plan.
  └─ Is it a security issue?
      └─ Yes → Flag immediately to user regardless of scope
```

## Evidence-Before-Claims

Never claim success without fresh evidence from the current step.

### Rationalization Prevention

| What you're tempted to say | Why it's wrong | What to do instead |
|---------------------------|----------------|-------------------|
| "Should work now" | You haven't run anything | Run the verify command. Show output. |
| "Tests passed earlier" | State may have changed since then | Run tests again. Show fresh output. |
| "Linter is clean" | Linter ≠ type checker ≠ test runner | Run ALL verification for the current tier. |
| "I only changed one line" | One line can break everything | Verify. Single-line changes cause the hardest bugs. |
| "It's the same pattern as the other file" | Copy-paste bugs are real | Verify independently. |
| "The types guarantee correctness" | Types don't catch runtime logic errors | Write a test. Types are necessary, not sufficient. |
| "Build passes" | Build ≠ correctness | Run tests. Build verifies compilation, not behavior. |

### Evidence Requirements by Phase

| Phase | Minimum Evidence |
|-------|-----------------|
| After each file edit | Fresh typecheck output |
| After implementing a step | Fresh test run output (pass or fail as expected) |
| Before presenting completion | Fresh typecheck + lint + test + build output |
| Before committing | All of the above in the current message |

### The Freshness Rule

Evidence is **stale** if:
- It was produced before your most recent file edit
- It was produced in a previous message/turn
- You're referencing a prior run without re-running

Evidence is **fresh** if:
- The command was run AFTER the last file change
- The output is visible in the current message
- No file edits happened between the run and the claim
