---
name: sync
description: Audit and align AI documentation with the actual state of the codebase. Use when documentation feels stale, after significant refactoring, periodically at sprint boundaries, or when AI assistance seems to follow outdated patterns.
category: meta
triggers:
  - docs out of date
  - stale documentation
  - sync docs
  - align docs
---

# Sync Documentation

> **Purpose:** Align AI documentation with the actual state of the codebase
> **Usage:** `/sync`

## Constraints

- **Be systematic** -- check each file type methodically
- **Verify before updating** -- confirm patterns exist in code before documenting
- **Keep it current** -- update "Last Updated" dates when modifying files
- **Don't over-document** -- only document patterns that are actually used
- **Flag uncertainty** -- if unsure about a pattern, ask the user

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Prerequisites

Requires project configuration scaffolded by `/init`. The following `.ai-project/` structure must exist:
- `.ai-project/.memory.md` — Architecture overview
- `.ai-project/.context.md` — Quick reference
- `.ai-project/project/` — Project configuration files
- `.ai-project/domains/` — Domain-specific instructions
- `.ai-project/decisions/` — Architecture decision records
- `.ai-project/todos/` — Technical debt tracking

If these files do not exist, create the directory structure or suggest running `/init`.

## When to Use

- Documentation feels out of sync with the code
- After significant refactoring or architectural changes
- Periodically (e.g., weekly or at sprint boundaries)
- Before onboarding new team members to AI-assisted development
- When the AI assistant seems to be following outdated patterns

## Workflow

### Phase 1: Assess Current State

Start by understanding what has changed:

1. **Check recent git history** from the "Last Updated" date:
   ```bash
   # Find the "Last Updated" date in .memory.md
   # Then scan commits since that date
   git log --oneline --since="YYYY-MM-DD"
   ```
   If no "Last Updated" date exists, fall back to `git log --oneline -50`.

2. **Identify documentation last updated**:
   - Check "Last Updated" dates in documentation files
   - Compare against recent commit dates

3. **List modified areas** since documentation was last updated

**If no commits since last documented date and all files appear current:** Report "Documentation is in sync — no changes needed" and exit.

### Phase 2: Validate Core Documentation

Review and update these files for accuracy. Use the following mapping to locate each section:

| Section Reference | File Path |
|---|---|
| Session Context | `.ai-project/.memory.md` → "Recent Work Areas" section |
| Git Workflow | `.ai-project/project/git.md` |
| Architecture | `.ai-project/.memory.md` → "Architecture" section |
| Quick Reference / Import Patterns | `.ai-project/.context.md` |
| Documentation Index | `.ai-project/.context.md` → "Quick Reference" section |

#### Architecture and Patterns

1. **Session Context** (`.ai-project/.memory.md` → "Recent Work Areas"):
   - Update "Recent Work Areas" based on git history
   - Review "Ongoing Work" for completed items
   - Update "Last Updated" date

2. **Git Workflow** (`.ai-project/project/git.md`):
   - Confirm main branch is current: `git remote show origin | grep 'HEAD branch'`
   - Review commit prefixes against recent commits: `git log --oneline -20`

3. **Architecture** (`.ai-project/.memory.md` → "Architecture"):
   - Verify patterns and conventions are current
   - Check if new patterns have emerged

#### Quick Reference (`.ai-project/.context.md`)

1. **Import patterns**: Check for new libraries or changed imports
2. **Common patterns**: Verify documented patterns are still in use
3. **File locations**: Confirm paths are still accurate

#### Documentation Index (`.ai-project/.context.md` → "Quick Reference")

1. **Cross-references**: Ensure all links work
2. **Error patterns**: Add any new common errors discovered
3. **Topic coverage**: Add new patterns or topics

### Phase 3: Validate Domain Instructions

For each domain documentation file:

1. **Spot-check patterns** against actual code:
   - Search for a few documented patterns in the codebase
   - Verify they're still in use

2. **Check for new patterns** not yet documented:
   - Look at recent commits for new conventions
   - Search for repeated patterns in new code

3. **Flag outdated guidance**:
   - Mark deprecated patterns
   - Update or remove obsolete instructions

**Technology migration detected:** If a domain file references a technology that has been replaced (e.g., express → fastify):
1. Search the codebase for actual usage patterns of the NEW technology
2. Update the domain file with patterns found in the actual code — do NOT use generic templates
3. If the migration is partial (both old and new coexist), document both and note the migration status
4. If unsure about migration completeness, ask the user before rewriting the domain file

### Phase 4: Review Decisions and Todos

#### Architecture Decision Records

1. Check if any decisions have been superseded
2. Add new ADRs if significant patterns have changed
3. Update status of existing ADRs if applicable

#### Long-term Todos

1. Mark completed items
2. Remove stale entries
3. Add any new discoveries

### Phase 5: Scan for Gaps

Look for undocumented areas:

1. **New directories or packages** not mentioned in docs
2. **New patterns** not covered in domain instructions
3. **New error types** not listed in documentation
4. **Changed workflows** that don't match documentation

### Phase 6: Present Audit Report and Confirm

Present all findings as a structured audit report (using the Output Format below). Do NOT write any changes yet.

**GATE: User must approve changes before any files are modified.**

After approval, apply changes in this order:
1. Core docs (`.memory.md`, `.context.md`)
2. Domain files
3. Todos (mark complete)
4. ADR status updates

## Output Format

Present this report BEFORE writing any changes:

```markdown
# Documentation Audit Report

## Summary
- **Last documented**: [date]
- **Commits since then**: [N commits]
- **Files updated**: [list of files modified]

## Changes Proposed

### Architecture and Patterns
- [What was updated]

### Quick Reference
- [What was updated]

### Documentation Index
- [What was updated]

### Domain Instructions
- [Which files updated and why]

### Decisions
- [New/updated ADRs]

### Todos
- [Items completed/added/removed]

## Gaps Identified
- [Areas needing future documentation]

## Recommendations
- [Suggestions for improving documentation]
```

## Quick Mode

For a faster refresh (e.g., end of day), run only these steps:

**Required in quick mode:**
1. Phase 1: Assess Current State (git history scan)
2. Phase 2: Update `.memory.md` "Recent Work Areas" and "Last Updated" date
3. Phase 2: Add any new error patterns or imports to `.context.md`

**Skipped in quick mode:**
- Phase 3: Full domain instruction review
- Phase 4: ADR and todo review
- Phase 5: Gap scanning

Quick mode still requires the confirmation gate before writing changes.

## Rules

### Required
- Systematic check of each documentation file
- Verify patterns exist in code before documenting
- Update "Last Updated" dates when modifying files
- Present audit report and get user approval BEFORE writing any changes
- Provide final summary after changes are applied

### Recommended
- Run after significant refactoring
- Run periodically (weekly or at sprint boundaries)
- Use quick mode for end-of-day refreshes
- Flag areas of uncertainty for user input

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| SYN-T1 | Positive | "Docs are out of date" | Skill triggers |
| SYN-T2 | Positive | "Sync AI documentation" | Skill triggers |
| SYN-T3 | Positive | "Align docs with code" | Skill triggers |
| SYN-T4 | Negative | "Add JSDoc to this file" | Does NOT trigger (-> /docs) |
| SYN-T5 | Negative | "How does the API work?" | Does NOT trigger (-> /explore) |
| SYN-T6 | Boundary | "Update documentation after refactor" | Context-dependent — if updating AI project docs, trigger; if updating code docs, route to /docs |
