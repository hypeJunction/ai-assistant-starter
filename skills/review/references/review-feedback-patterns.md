# Review Feedback Patterns

Guide to providing constructive, actionable code review feedback. Good feedback is specific, kind, and actionable — it tells the author exactly what to change and why.

## Feedback Labels

Use labels to set clear expectations about what requires action:

| Label | Meaning | Author Action |
|-------|---------|--------------|
| **blocking** | Must be fixed before merge — correctness, security, or data integrity issue | Fix required |
| **important** | Should be fixed — significant quality or maintainability concern | Fix expected (author can push back with justification) |
| **nit** | Minor style or naming suggestion | Optional — author's discretion |
| **suggestion** | Alternative approach worth considering | Optional — for future consideration |
| **question** | Need clarification to complete review | Respond with explanation |
| **praise** | Something done well worth calling out | None (enjoy the recognition) |

### Usage

```markdown
**[blocking]** `auth.ts:42` — This endpoint doesn't check if the user owns the resource.
Any authenticated user can access any other user's data by changing the ID in the URL.

**[important]** `api.ts:18` — The error response leaks the full stack trace.
In production, this could reveal internal file paths and dependency versions.

**[nit]** `utils.ts:7` — Consider renaming `processData` to `normalizeUserInput`
for clarity about what this function actually does.

**[suggestion]** `cart.ts:55` — This discount logic could use a strategy pattern
if you anticipate adding more discount types. Not needed now, but worth noting.

**[question]** `middleware.ts:23` — Is this rate limit (100 req/min) intentional
for the admin endpoints? Seems low for internal tools.

**[praise]** `auth.test.ts` — Excellent edge case coverage, especially the
expired token + refresh race condition test.
```

## The Question Approach

Frame concerns as questions rather than commands. This invites dialogue and respects the author's context.

| Instead of... | Try... |
|--------------|--------|
| "This is wrong" | "What happens when `items` is empty?" |
| "You should use X" | "Have you considered X? It would handle the null case." |
| "This will break" | "Could this fail if the API returns 429? I don't see retry logic." |
| "Don't use any" | "What type should this be? I can help figure it out if the shape is complex." |
| "This is too complex" | "I'm having trouble following this — could we break it into smaller functions?" |
| "Bad variable name" | "What does `d` represent here? A more descriptive name would help future readers." |

### Why Questions Work

- They assume the author might have context you lack
- They invite explanation rather than defensive reactions
- They surface the reasoning behind decisions
- They catch cases where you're wrong about the issue

## Feedback Structure

### For Blocking/Important Issues

```markdown
**[blocking]** `file.ts:line` — **Brief title of the issue**

**What I see:** [describe the current code behavior]
**The concern:** [why this is a problem — concrete impact, not theoretical]
**Suggested fix:** [specific code change or approach]

// Optional: show before/after
```

### For Suggestions

```markdown
**[suggestion]** `file.ts:line` — **Brief title**

[Current approach works, but here's an alternative worth considering]

```typescript
// Current
const result = items.filter(i => i.active).map(i => i.name);

// Alternative: single pass
const result = items.reduce((acc, i) => {
  if (i.active) acc.push(i.name);
  return acc;
}, []);
```

[Trade-off: slightly more code but better performance for large arrays]
```

### For Praise

```markdown
**[praise]** `auth.ts:15-30` — Nice use of the builder pattern here.
It makes the token configuration readable and hard to misuse.
```

Don't overdo praise — 1-2 genuine positive notes per review is ideal. Forced praise feels performative.

## Tone Guidelines

### Do

- Be specific — "Line 42 could throw if `user` is null" not "There might be issues"
- Be constructive — Always include what to do, not just what's wrong
- Acknowledge trade-offs — "This adds complexity but improves safety, which seems worth it here"
- Separate preferences from requirements — Label nits clearly so the author knows what's optional
- Assume competence — The author probably had a reason; ask before criticizing

### Don't

- Use condescending language — "Obviously you should..." / "As everyone knows..."
- Pile on — If the same pattern appears 5 times, comment once and say "same issue in X other places"
- Make it personal — Comment on the code, not the person. "This function is unclear" not "You wrote this poorly"
- Demand perfection — If the code works, is tested, and is readable, minor style differences are nits
- Bikeshed — Don't spend 10 comments on naming when there's a correctness issue to discuss

## When to Approve vs. Request Changes

| Findings | Action |
|----------|--------|
| No blocking or important issues | **Approve** (optionally with nits) |
| Nits only | **Approve** with comments |
| 1+ important, 0 blocking | **Request changes** — but acknowledge the overall quality |
| 1+ blocking | **Request changes** — clearly explain what must change |
| Unsure about an issue | **Comment** without requesting changes — ask the question |

### The "Approve with Comments" Pattern

If everything is correct but you have suggestions:

```markdown
**Approved** — Code is correct, tested, and ready to merge.

A few optional suggestions if you want to improve before merging:
- [nit] ...
- [suggestion] ...

These are not blocking. Merge whenever you're ready.
```

## Anti-Patterns in Code Review

### Over-Reviewing

- Commenting on every line — focus on what matters
- Requesting changes for style preferences not in the project's conventions
- Blocking for things the linter should catch
- Re-reviewing code you already approved (unless it changed)

### Under-Reviewing

- Approving without reading ("LGTM" on 500-line PR)
- Only checking the happy path
- Skipping test files
- Not checking for security issues on endpoints

### Unhelpful Feedback

- "This could be better" — HOW?
- "I don't like this" — WHY? What specifically?
- "Consider refactoring" — INTO WHAT?
- "Needs more tests" — WHICH scenarios?

Every comment should be specific enough that the author knows exactly what to change.
