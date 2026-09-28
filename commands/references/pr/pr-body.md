# PR Title and Body Template

Used by `/pr` for both `gh pr create` and `gh pr edit`. Write for a
reviewer with no prior context on the problem or the solution.

## Title

```
[component]: Brief description [TICKETS]
```

`component` is the affected area of the codebase, not a conventional-commit
type. With multiple tickets, list every one back-to-back: `[T-1234][T-1240]`.
Omit the ticket suffix entirely when no ticket is known — never invent one.

## Body

```markdown
## Summary

[One paragraph, plain prose: what this PR does and why, for a reviewer with
no prior context. If it spans multiple tickets, synthesize one narrative
covering all of them rather than a paragraph per ticket.]

## What changed

- [Outcome 1, described by user-visible/behavioral result]
- [Outcome 2]

## Test Plan

[Only if verification is non-obvious — omit otherwise]

## Security

[Only if the change touches auth, secrets, input handling, permissions, or
new dependencies — omit otherwise]

[TICKETS]
```

`[TICKETS]` is every known ticket, one per line, each a markdown link
(`[TICKET](URL)`) when its URL is known, plain text otherwise — never
combined onto one line, never dropped. Omit the whole section if no ticket
is known.

## Updating an existing PR

Rewrite the body fresh — never append to the existing description:

- Re-derive `## Summary` so it still describes the PR's current overall
  direction; edit in place rather than adding a second paragraph.
- Add a `## What changed` bullet only for genuinely new user-facing
  behavior. A commit that just fixes or tweaks something an existing bullet
  already covers doesn't get its own line.
- The description should always read as if written fresh for the branch's
  current state, never as a changelog or edit history.

## Worked example

```markdown
## Summary

Users currently have no way to authenticate — every API endpoint is open.
This adds token-based login so requests can be tied to a user and existing
routes can be locked down behind auth.

## What changed

- Users can register and log in, receiving a token to use for future requests
- Passwords are stored securely rather than in plain text
- Existing API routes now require a valid token

## Security

- Passwords hashed before storage, never logged or returned in responses
- Auth checks added to all previously-open routes

[T-1204]
```

Title: `auth: add token-based login [T-1204]`. No `## Test Plan` — login and
registration are standard flows covered by the included test suite. No file
or variable names anywhere in the body.
