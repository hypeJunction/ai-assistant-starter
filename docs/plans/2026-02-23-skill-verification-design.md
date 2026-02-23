# Skill Verification & Improvement Plan

## Overview

Desk review of all 29 workflow skills. For each: define a concrete scenario with known outcome, walk backwards through expected steps, evaluate SKILL.md coverage, identify gaps, and apply fixes.

## Verification Case Format

Each skill gets a `skills/<name>/VERIFICATION.md`:

```markdown
# Verification: <skill-name>

## Scenario
<!-- Concrete situation with specific filenames, errors, project state -->

## Expected Outcome
<!-- What must be true when the skill completes -->

## Checkpoints
<!-- Intermediate states that must be reached, in order -->
- [ ] Checkpoint 1: ...

## Anti-patterns
<!-- Things that must NOT happen -->
- Agent should not ...

## Gap Analysis
| Checkpoint | Coverage | Notes |
|------------|----------|-------|
| ... | Covered / Implicit / Missing / Wrong | ... |

## Findings
- **Gaps**: ...
- **Improvements**: ...
- **Structural**: ...
```

## Methodology

Based on [Anthropic's eval framework](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents):
- Grade outcomes, not paths
- Checkpoints define what must happen, not exactly how
- Anti-patterns catch known failure modes
- Gap Analysis connects checkpoints to actual SKILL.md coverage

## Cross-Cutting Issues Found

### Systemic (affect 5+ skills)

1. **Missing approval gates** — docs, sync, test-coverage, api-test, track-files, add-todo
2. **No re-validation after fixes** — commit, pr, finish, iterate-pr
3. **Package manager hardcoded as npm** — e2e, release, init, validate, accessibility-review
4. **Security scanning inconsistency** — commit has grep cmds, hotfix has own cmds, pr has checklist only, iterate-pr has none
5. **Scope flags documented but not operationalized** — release, deps, e2e
6. **No "nothing to do" early exit** — deps, sync, docs, test-coverage, release
7. **Reference files not linked from main workflow** — api-test, review, e2e
8. **`gh` auth never verified** — iterate-pr, pr, hotfix

### Critical Per-Skill

| Skill | Gap |
|-------|-----|
| init | `.memory.md` and `.context.md` never populated (70+ placeholders left) |
| track-files | Never instructs agent to actually search the codebase |
| test-coverage | Never measures actual coverage despite the name |
| finish | Review phase after validation — fixes invalidate validation |
| add-todo | 4 conflicting template sources |
| migrate | 3-step NOT NULL pattern described but Prisma workflow not spelled out |
| revert | Reference file recommends `git reset --hard` while SKILL.md forbids it |

## Task Structure for Subagent-Driven Development

Each task is independent: **write VERIFICATION.md + apply improvements to SKILL.md/references**.

### Batch 1: Critical Fixes (5 tasks)

1. **init** — Add .memory.md/.context.md population, package manager detection, config.yaml persistence, Next.js/Tailwind domain detection
2. **track-files** — Add actual codebase search step, confirmation gate, per-file note guidance
3. **test-coverage** — Add coverage measurement step, approval gate, test file location discovery, existing pattern matching
4. **finish** — Add re-validation loop after review fixes, clarify `any` type handling, test creation failure handling
5. **add-todo** — Consolidate templates to single source, add clarification step, add confirmation gate

### Batch 2: Missing Gates & Safety (4 tasks)

6. **commit** — Add re-scan loop after secret fix, handle unrelated unstaged changes
7. **pr** — Add uncommitted changes handling, validation failure + re-validation loop, security scan commands, existing PR detection
8. **iterate-pr** — Add gh auth preflight, explicit CI failure fixing sequence, local validation before push, conflict handling
9. **hotfix** — Add Phase 0 (stash current work, create hotfix branch from main, verify gh auth)

### Batch 3: Review & Security Skills (4 tasks)

10. **review** — Add mass assignment to inline checklist, mitigation search instruction, large diff review strategy, clarify read-only/fix mode transition
11. **security-review** — Add security error handling check, attack chain analysis note, cross-file data flow tracing
12. **accessibility-review** — Add layout-level scope guidance, accessible library misuse detection, tooling recommendations, non-descriptive alt to inline checks
13. **e2e** — Add package manager detection, third-party iframe guidance, dev server management, browser installation, link e2e-patterns.md from workflow

### Batch 4: Dev Workflow Skills (5 tasks)

14. **explore** — Add Deep-level section templates, cross-strategy techniques for Deep explorations, monorepo guidance
15. **plan** — Add alternatives analysis template, connect security checklist to plan steps, clarify plan/implement overlap
16. **implement** — Add security-guidelines to context-aware table, new file creation guidance, evidence freshness cross-reference
17. **debug** — Add production-only bug guidance, database/ORM debugging references, escalation report template
18. **refactor** — Add phased refactor guidance, batch grouping strategy, "Introduce Abstraction Layer" pattern

### Batch 5: Testing Skills (3 tasks)

19. **migrate** — Spell out Prisma 3-step NOT NULL workflow, backfill value guidance, fix rollback command conflict
20. **validate** — Clarify intra-Level 1 execution order, link security-scan-patterns.md proactively, expand CI mode
21. **tdd** — Add multi-cycle behavior tracking, initial test file creation, commit frequency guidance, feature decomposition strategy

### Batch 6: Testing Skills cont. + Git (2 tasks)

22. **api-test** — Add auth requirement detection step, nested resource testing, approval gate, link api-test-patterns.md, test server setup in main skill
23. **release** — Handle package-lock.json regeneration, operationalize scope flags, explicit moderate vuln handling, fix phase numbering

### Batch 7: Maintenance & Utility Skills (6 tasks)

24. **revert** — Fix reference contradiction (git reset --hard), add merge commit detection in main workflow, fix dry-run cleanup, add build to validation
25. **deps** — Add security+major version conflict guidance, early exit path, deprecated package detection, operationalize scope flags
26. **docs** — Add @throws to function template, TypeScript interface guidance, approval gate, next steps, test file location guidance
27. **sync** — Dynamic commit depth, map abstract section names to file paths, add confirmation gates, partial migration guidance, add references directory
28. **adr** — Add existing ADR reading step, fix superseding workflow contradiction, related ADR discovery
29. **add-story** — Add file naming/location guidance, context provider decorator guidance, Storybook running prerequisite check

### Cross-Cutting Task (after all batches)

30. **Cross-cutting standardization** — Verify all skills now have: package manager note (where applicable), acceptance tests section, "nothing to do" early exit, consistent gate markers (GATE:)
