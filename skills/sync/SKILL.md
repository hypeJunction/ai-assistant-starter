---
name: sync
description: Audit and align AI documentation with the actual state of the codebase. Use when documentation feels stale, after significant refactoring, periodically at sprint boundaries, or when AI assistance seems to follow outdated patterns.
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

1. **Check recent git history**:
   ```bash
   git log --oneline -50
   ```

2. **Identify documentation last updated**:
   - Check "Last Updated" dates in documentation files
   - Compare against recent commit dates

3. **List modified areas** since documentation was last updated

### Phase 2: Validate Core Documentation

Review and update these files for accuracy:

#### Architecture and Patterns

1. **Session Context section**:
   - Update "Recent Work Areas" based on git history
   - Review "Ongoing Work" for completed items
   - Update "Last Updated" date

2. **Git Workflow section**:
   - Confirm main branch is current: `git remote show origin | grep 'HEAD branch'`
   - Review commit prefixes against recent commits: `git log --oneline -20`

3. **Architecture sections**:
   - Verify patterns and conventions are current
   - Check if new patterns have emerged

#### Quick Reference

1. **Import patterns**: Check for new libraries or changed imports
2. **Common patterns**: Verify documented patterns are still in use
3. **File locations**: Confirm paths are still accurate

#### Documentation Index

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

## Output Format

After completing the audit, provide a status report:

```markdown
# Documentation Audit Report

## Summary
- **Last documented**: [date]
- **Commits since then**: [N commits]
- **Files updated**: [list of files modified]

## Changes Made

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

For a faster refresh (e.g., end of day):

1. Update session context with recent work
2. Add any new errors/patterns to documentation index
3. Update "Last Updated" date

Skip the full domain instruction review unless patterns seem wrong.

## Rules

### Required
- Systematic check of each documentation file
- Verify patterns exist in code before documenting
- Update "Last Updated" dates when modifying files
- Provide audit report at completion

### Recommended
- Run after significant refactoring
- Run periodically (weekly or at sprint boundaries)
- Use quick mode for end-of-day refreshes
- Flag areas of uncertainty for user input
