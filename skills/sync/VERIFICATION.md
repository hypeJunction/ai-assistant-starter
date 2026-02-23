# Sync Skill Verification

## Scenario

A developer runs `/sync` after a sprint where:

- 3 new API routes were added (`/api/orders`, `/api/orders/:id`, `/api/payments/webhook`) not documented in `.ai-project/.context.md`
- The project migrated from `express` to `fastify` — `.ai-project/domains/backend.instructions.md` still references express middleware patterns
- 2 todos in `.ai-project/todos/` are completed: `001-add-pagination.md` and `003-fix-auth-middleware.md`
- ADR `session-based-auth.md` should be superseded (JWT was adopted) but status still says "Accepted"
- `.ai-project/.memory.md` "Recent Work Areas" section was last updated 4 weeks ago
- Last documented date in `.memory.md` is "2026-01-26"

## Expected Outcome

The agent scans git history from 2026-01-26 to HEAD (not just last 50 commits), audits all `.ai-project/` files, presents a structured audit report listing all discrepancies, and waits for user approval before writing any changes. After approval, the agent applies changes: updates `.memory.md` with current work areas and a new "Last Updated" date, updates `.context.md` with the 3 new API routes, rewrites `backend.instructions.md` to reflect fastify patterns found in the actual codebase, marks the 2 completed todos as done, flags the ADR status discrepancy for confirmation, and presents a final summary report.

## Key Checkpoints

### 1. Prerequisite check — `.ai-project/` structure verified

**Phase:** Before Phase 1

The agent confirms that the `.ai-project/` directory exists with the expected structure (`.memory.md`, `.context.md`, `project/`, `domains/`, `decisions/`, `todos/`). If the structure is missing or incomplete, the agent suggests running `/init` instead of proceeding.

**Pass criteria:** Agent checks for `.ai-project/` existence before any git history scan.

### 2. Git history scanned from "Last Updated" date to HEAD

**Phase:** Phase 1 (Assess Current State)

The agent reads `.memory.md`, finds the "Last Updated" date (2026-01-26), and runs `git log --oneline --since="2026-01-26"` rather than a hardcoded `git log --oneline -50`. This ensures all commits from the past 4 weeks are captured, even if there are more than 50.

**Pass criteria:** The git log command uses `--since="2026-01-26"` (or equivalent date-based scan), not a fixed count.

### 3. `.memory.md` "Recent Work Areas" refreshed from git log

**Phase:** Phase 2 (Validate Core Documentation)

The agent analyzes the git log output to identify the main work areas (orders API, payments webhook, express-to-fastify migration, auth middleware fix, pagination) and updates the "Recent Work Areas" section of `.memory.md` accordingly.

**Pass criteria:** "Recent Work Areas" reflects the actual sprint work, not stale 4-week-old content.

### 4. `.context.md` updated with 3 new API routes

**Phase:** Phase 2 (Validate Core Documentation)

The agent detects that `/api/orders`, `/api/orders/:id`, and `/api/payments/webhook` are present in the codebase but missing from `.context.md`. The agent adds them to the appropriate section (e.g., "API Routes" or "Quick Reference").

**Pass criteria:** All 3 routes appear in the updated `.context.md`.

### 5. Backend domain file identified as stale (express to fastify mismatch)

**Phase:** Phase 3 (Validate Domain Instructions)

The agent spot-checks patterns in `backend.instructions.md` against the codebase and detects that the file references express middleware patterns (e.g., `app.use()`, `express.Router()`) while the actual code uses fastify (e.g., `fastify.register()`, `fastify.route()`).

**Pass criteria:** Agent explicitly flags the express-to-fastify mismatch in the audit report.

### 6. Domain file update uses actual fastify patterns from codebase

**Phase:** Phase 3 (Validate Domain Instructions)

When updating `backend.instructions.md`, the agent searches the codebase for actual fastify usage patterns (route registration, plugin patterns, hooks, schema validation) and uses those patterns in the updated domain file — not generic fastify documentation.

**Pass criteria:** Updated domain file contains patterns found in the project's own code, not boilerplate from external docs.

### 7. Completed todos identified and marked done

**Phase:** Phase 4 (Review Decisions and Todos)

The agent cross-references git history against todo descriptions and identifies that `001-add-pagination.md` and `003-fix-auth-middleware.md` describe work that has been completed. The agent marks these todos as done (e.g., updating their status or moving them).

**Pass criteria:** Both completed todos are identified and marked in the audit report.

### 8. ADR status discrepancy flagged

**Phase:** Phase 4 (Review Decisions and Todos)

The agent detects that `session-based-auth.md` has status "Accepted" but the codebase now uses JWT-based authentication. The agent flags this discrepancy in the audit report but does NOT change the ADR status without user confirmation.

**Pass criteria:** ADR discrepancy appears in the audit report. Agent asks for confirmation before changing status.

### 9. Audit report presented BEFORE any changes are written

**Phase:** Phase 6 (Present Audit Report and Confirm)

The agent compiles all findings into a structured audit report (summary, changes proposed, gaps identified, recommendations) and presents it to the user. No files have been modified at this point.

**Pass criteria:** The audit report is shown before any `write` or `edit` operations on `.ai-project/` files.

### 10. User approval gate before writing changes

**Phase:** Phase 6 (Present Audit Report and Confirm)

After presenting the audit report, the agent explicitly asks for user approval before proceeding. The agent does NOT silently apply changes. Only after the user confirms does the agent begin writing updates.

**Pass criteria:** Agent waits for explicit user approval. No file modifications occur until approval is given.

## Anti-Patterns

### 1. Rewriting domain files from scratch instead of targeted updates

**Wrong:** Agent deletes the entire contents of `backend.instructions.md` and writes a generic fastify guide from scratch.

The domain file may contain project-specific conventions, team preferences, and patterns unrelated to the express/fastify migration. A full rewrite destroys this context. The agent should make targeted updates: replace express-specific patterns with fastify equivalents while preserving everything else.

### 2. Using hardcoded `git log -50` instead of scanning from last documented date

**Wrong:** Agent runs `git log --oneline -50` regardless of when documentation was last updated.

If the sprint produced 80 commits over 4 weeks, the last 50 would miss the earliest changes. The agent should read the "Last Updated" date from `.memory.md` and use `--since` to capture the full window.

### 3. Modifying files without presenting audit report first

**Wrong:** Agent scans the git history, identifies discrepancies, and immediately starts editing `.memory.md` and `.context.md` without showing the user what will change.

The user needs to review proposed changes to catch errors (e.g., an ADR the agent wants to mark as superseded may actually still be valid). The audit report is a required gate.

### 4. Marking ADRs as superseded without user confirmation

**Wrong:** Agent detects that `session-based-auth.md` references session-based auth while the code uses JWT, and automatically changes the ADR status to "Superseded."

ADR status changes have architectural implications. The agent should flag the discrepancy and ask the user whether to update the status, create a new ADR, or leave it as-is.

### 5. Skipping the prerequisite check and erroring on missing `.ai-project/`

**Wrong:** Agent jumps straight into scanning git history and reading `.memory.md`, then fails with a file-not-found error because `.ai-project/` was never created.

The agent should check for the `.ai-project/` directory structure at the start and, if missing, suggest running `/init` to scaffold it.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| Hardcoded git log depth | Phase 1 used `git log --oneline -50` regardless of how far back documentation was last updated, missing older commits in long sprints | Replaced with date-based scan using the "Last Updated" date from `.memory.md`, falling back to `-50` only when no date exists |
| Abstract section names | Phases 2-3 referenced "Session Context," "Architecture," and "Quick Reference" without mapping them to specific file paths, leaving ambiguity about which files to update | Added explicit file path mapping table linking each section name to its `.ai-project/` file and section |
| No confirmation gate | The skill applied changes immediately after scanning, with no opportunity for the user to review or reject proposed updates | Added Phase 6 requiring a structured audit report and explicit user approval before any files are modified |
| No partial migration guidance | Domain file updates had no strategy for technology migrations (e.g., express to fastify), risking generic rewrites that lose project-specific context | Added migration detection guidance: search codebase for actual new-technology patterns, handle partial migrations, and ask user when migration completeness is uncertain |
| No early exit for current docs | The skill ran the full 5-phase workflow even when documentation was already in sync, wasting time | Added early exit after Phase 1: if no commits since last documented date and all files appear current, report "in sync" and exit |
| Missing acceptance tests | No test cases existed to verify the skill triggers on correct intents and rejects incorrect ones | Added acceptance tests table covering positive triggers, negative non-triggers, and boundary cases |
| Quick mode underspecified | Quick mode listed 3 bullet points but did not clarify which phases were included vs. skipped, or whether the confirmation gate still applied | Rewrote quick mode with explicit required/skipped phase lists and noted that the confirmation gate still applies |
