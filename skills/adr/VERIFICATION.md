# ADR Skill Verification

## Scenario

A developer runs `/adr API authentication strategy` on a project that has an existing `.ai-project/decisions/` directory containing 2 accepted ADRs:

| Existing ADR | Status | Content |
|---|---|---|
| `session-based-auth.md` | Accepted | Decided to use session-based authentication with cookies for all API endpoints |
| `api-client-pattern.md` | Accepted | Established the API client pattern; includes the line "Auth tokens are managed via session cookies per session-based-auth.md" |

**The new decision:** Migrate from session-based auth to JWT tokens for API endpoints. This decision supersedes `session-based-auth.md`.

## Expected Outcome

The agent reads all existing ADRs before drafting anything, discovers that `session-based-auth.md` is directly related and will be superseded, discovers that `api-client-pattern.md` references the auth approach, creates a new ADR file `jwt-authentication.md` with the JWT decision, includes alternatives (session-based auth, OAuth, API keys) with honest pros/cons, lists both positive and negative consequences, updates `session-based-auth.md` status to "Superseded by jwt-authentication.md", notes the relationship with `api-client-pattern.md` and that it needs updating, and presents the full draft for user approval before writing any files.

## Key Checkpoints

### 1. Agent reads ALL existing ADRs before starting

**Phase:** Step 1.1 (Read Existing ADRs)

The agent lists `.ai-project/decisions/` and reads every ADR file to understand the current decision landscape. It does not skip this step even though the user already provided a topic.

**Pass criteria:** Agent runs `ls .ai-project/decisions/` and reads the content of both `session-based-auth.md` and `api-client-pattern.md` before doing anything else.

### 2. Agent discovers `session-based-auth.md` is related to the auth topic

**Phase:** Step 1.1 (Read Existing ADRs)

After reading the existing ADRs, the agent identifies `session-based-auth.md` as directly related to the new decision topic (API authentication) and recognizes that the new JWT decision will supersede it.

**Pass criteria:** Agent explicitly states that `session-based-auth.md` is related and asks the user to confirm whether the new decision supersedes it.

### 3. Agent discovers `api-client-pattern.md` references auth approach

**Phase:** Step 1.3 (Search for Related ADRs)

The agent searches existing ADRs for references to auth-related terms and finds that `api-client-pattern.md` contains a reference to session cookies and the session-based-auth ADR.

**Pass criteria:** Agent identifies `api-client-pattern.md` as having a dependency on the auth approach and notes it for the "Related Decisions" section.

### 4. New ADR uses descriptive name `jwt-authentication.md`

**Phase:** Step 3 (Create the ADR)

The agent creates a new file with a name that describes the new decision (`jwt-authentication.md`), NOT reusing the old filename `session-based-auth.md`. Both files remain in the decisions directory, making the superseding relationship explicit and both decisions discoverable.

**Pass criteria:** The new file is named `jwt-authentication.md` (or similar descriptive name for the JWT decision). The old `session-based-auth.md` file is NOT overwritten or deleted.

### 5. Context section is standalone

**Phase:** Step 3 (Create the ADR) / Step 4 (Verify Quality)

The Context section of the new ADR explains the full situation: the project currently uses session-based auth, why a change is needed, what constraints exist. A reader should understand the situation without needing to open `session-based-auth.md` first.

**Pass criteria:** The Context section mentions the current session-based approach, its limitations, and why JWT was considered — all within the ADR itself.

### 6. Alternatives section includes session-based auth with honest pros/cons

**Phase:** Step 3 (Create the ADR)

The Alternatives Considered section includes at least session-based auth (the current approach being replaced), and ideally other options like OAuth or API keys. Each alternative has genuine pros and cons — session-based auth is not dismissed with strawman arguments.

**Pass criteria:** Session-based auth appears as an alternative with real pros (e.g., simpler server-side session management, CSRF protection built-in) alongside its cons.

### 7. Consequences include both positive AND negative impacts

**Phase:** Step 3 (Create the ADR) / Step 4 (Verify Quality)

The Consequences section has both Positive and Negative subsections with concrete, specific entries. Negative consequences might include: token storage security concerns, token revocation complexity, larger request payload.

**Pass criteria:** At least 2 positive and 2 negative consequences are listed, each with a brief explanation.

### 8. Related Decisions section mentions `api-client-pattern.md`

**Phase:** Step 3 (Create the ADR)

The new ADR includes a "Related Decisions" section that references `api-client-pattern.md` with a note that its auth token management approach will need updating as a consequence of this decision.

**Pass criteria:** `api-client-pattern.md` appears in the Related Decisions section with a note about the needed update.

### 9. Old ADR status updated to "Superseded by jwt-authentication.md"

**Phase:** Step 3 (Create the ADR) — after user approval

The agent updates the `session-based-auth.md` file's Status field from "Accepted" to "Superseded by jwt-authentication.md". The rest of the old ADR content is preserved.

**Pass criteria:** `session-based-auth.md` status reads `Superseded by jwt-authentication.md`. No other content in the file is removed or altered.

### 10. User approval gate before writing

**Phase:** Step 5 (Confirm)

The agent presents the complete new ADR content and the proposed status change to the old ADR, then waits for explicit user approval before writing any files. It does not write the new ADR or update the old one until the user confirms.

**Pass criteria:** Agent shows the full ADR draft and the old ADR status change, then asks for approval. No files are written until the user responds.

## Anti-Patterns

### 1. Creating ADR without reading existing ADRs first

**Wrong:** Agent skips reading `.ai-project/decisions/` and immediately starts drafting the new ADR based solely on the user's input.

This misses the superseding relationship with `session-based-auth.md` and the reference in `api-client-pattern.md`. The new ADR would lack proper context about what it replaces, and the old ADR would remain with status "Accepted" — creating a contradictory decision record.

### 2. Reusing the old ADR filename

**Wrong:** Agent overwrites `session-based-auth.md` with the new JWT decision, relying on git history to preserve the old content.

This makes the old decision invisible in the file system. Anyone browsing `.ai-project/decisions/` would only see the JWT decision and have no idea a previous session-based auth decision existed without checking git history. Both decisions should be discoverable as files.

### 3. Writing only positive consequences

**Wrong:** Agent lists benefits of JWT (stateless, scalable, mobile-friendly) but omits drawbacks (token revocation complexity, storage security, larger payloads).

An ADR with only positive consequences is a sales pitch, not an honest decision record. Future developers need to understand the tradeoffs that were accepted, not just the benefits that were expected.

### 4. Not updating the superseded ADR's status field

**Wrong:** Agent creates the new `jwt-authentication.md` but leaves `session-based-auth.md` with status "Accepted".

This creates contradictory records — two "Accepted" ADRs for authentication that recommend different approaches. Anyone reading `session-based-auth.md` would have no indication that it has been replaced.

### 5. Writing context that requires reading other ADRs to understand

**Wrong:** Agent writes the Context section as "See session-based-auth.md for background. We are switching to JWT."

This violates the quality check that context should be standalone. A reader opening `jwt-authentication.md` should understand the full situation without needing to open another document.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No "read existing ADRs" step | The workflow jumped straight to interviewing without reading existing decisions, missing superseding relationships and related ADRs | Added Step 1.1 (Read Existing ADRs) that reads all files in `.ai-project/decisions/` before any other action, noting status, topic relevance, and superseding candidates |
| Superseding naming contradiction | The skill said "if superseding, use the same name" which overwrites the old decision and makes it undiscoverable in the file system | Changed naming guidance to always create a NEW file with a descriptive name for the new decision, keeping both files visible and the superseding relationship explicit |
| No related ADR discovery | The skill had no step to search existing ADRs for references to the decision topic, missing cross-references like `api-client-pattern.md` referencing auth | Added Step 1.3 (Search for Related ADRs) that greps existing ADRs for topic keywords and notes references in the Related Decisions section |
| No early exit for trivial/forced decisions | The skill listed "When NOT to Create" criteria but had no workflow step to check them and suggest skipping | Added early exit guidance after Step 1 that checks whether the decision is trivial, forced, or already documented, and suggests skipping with an explanation |
| Acceptance tests missing boundary cases | The acceptance tests table lacked scenarios for superseding, related ADR discovery, and early exit conditions | Verified acceptance tests cover positive, negative, and boundary cases including the superseding workflow |
