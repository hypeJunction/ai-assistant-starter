# Changelog

All notable changes to AI Assistant Starter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `/adr` skill — capture Architecture Decision Records documenting context, reasoning, alternatives, and consequences of technical decisions; supports `--from-todo` for creating ADRs from completed todos
- `triggers` frontmatter field on all 28 workflow skills — short keyword phrases for intent-based auto-routing, enabling the assistant to match natural language requests to the right skill without explicit slash commands
- `/tdd` skill — strict RED-GREEN-REFACTOR cycle with Iron Laws, rationalization rebuttals, red flags, and testing anti-patterns reference
- `/api-test` skill — API endpoint testing with framework auto-detection, test categories by status code, and patterns reference
- `/e2e` skill — end-to-end testing with Playwright/Cypress, Page Object Model, selector strategies, and CI integration patterns
- `/migrate` skill — database/schema migrations with ORM-agnostic support (Prisma, Drizzle, TypeORM, Knex, raw SQL), risk classification, and rollback planning
- `/accessibility-review` skill — WCAG 2.1 AA audit with automated scanning, manual review checklists, P0-P3 severity, and comprehensive WCAG checklist reference
- `interaction-boundaries` skill — human-AI interaction boundaries implementing 9 dehumanization rules (no first-person identity, purely functional language, structured output, no uncertainty performance, no empathy simulation, deterministic behavior, focused clarification, no metacognition, fixed interaction patterns)
- `/security-review` skill — systematic security audit with confidence-based reporting
- `/iterate-pr` skill — iterate on PR until CI passes and feedback addressed
- `LICENSE` file (MIT)

### Changed
- Updated `/implement` — added `--todo` flag to drive implementation from an existing todo; added Phase 8 (Close) that verifies acceptance criteria, creates ADR if design decisions were made, and deletes the completed todo
- Updated `/plan` — after plan approval, persists each step as a todo via `/add-todo` for trackable work items (Step 7); removed optional `.plans/` file persistence in favor of todo-based tracking
- Updated `/add-todo` — completing a todo now creates an ADR via `/adr --from-todo` and deletes the todo file; ADRs capture current state, git history tracks evolution; no completed todos kept
- Standardized scope thresholds across all skills: Small (1-5 files), Medium (6-15, confirm with user), Large (16+, must use `/refactor`)
- Standardized approval gates — centralized valid/invalid terms in `ai-assistant-protocol`; workflow skills now reference the protocol instead of defining their own
- Added package-manager awareness note to 16 workflow skills — all command examples reference `ai-assistant-protocol` Project Commands for lock-file detection
- Added Law Composition section to `ai-assistant-protocol` — clarifies how protocol and workflow iron laws compose
- Added Skill Coordination section to `ai-assistant-protocol` — self-contained vs composable workflows, decision tree, "Do NOT chain" guidance
- Added Project Commands section to `ai-assistant-protocol` — resolution order (commands.md → lock file detection → npm fallback), standard command mapping
- Added TDD-lite preference to `/implement` Phase 5 — new functions/modules prefer test-first; strict TDD via `/tdd`
- Fixed `interaction-boundaries` violations in `/init`, `/debug`, `/finish`, `communication-guidelines`, `/refactor` templates, `/migrate` — replaced first-person language, conversational questions, and sign-offs with structured functional prompts
- Added `.ai-project/` fallback guidance to `/track-files` (Prerequisites section) and `/sync` (create directory structure or suggest `/init`)
- Upgraded `ai-assistant-protocol` — added Iron Laws (7 absolute rules), Rationalization Table (10 entries with rebuttals), expanded Red Flag Language (11+ patterns), Verification Workflows (4 types)
- Upgraded `/debug` — added Iron Laws, When to Use/NOT, Pattern Analysis phase, Debugging Decision Tree, Escalation Rule, Never Do list
- Upgraded `/plan` — added Iron Laws, Complexity Tiers (Trivial/Standard/Complex/Risky), Plan Quality Checklist, Execution Handoff options
- Upgraded `/implement` — added Iron Laws, Two-Stage Self-Review, Surprise Handling table, Completion Evidence requirement
- Upgraded `/test-coverage` (was `/cover`) — added Iron Laws, Test Quality Criteria, Coverage Targets by file type, Don't Test list, Test Smell Detection
- Upgraded `/explore` — added Iron Laws, Exploration Strategies by question type, Depth Levels (Surface/Standard/Deep)
- Added Iron Laws to `/validate`, `/refactor`, `/review`, `/security-review`, `/hotfix`
- Added When to Use / When NOT to Use sections to `/validate`, `/refactor`, `/review`, `/security-review`
- Added `--files` scope flag to `/review` and `/test-coverage`
- Renamed 5 skills for clarity and ecosystem alignment: `/cover` → `/test-coverage`, `/wrap` → `/finish`, `/e2e-test` → `/e2e`, `/create-todo` → `/add-todo`, `/file-list` → `/track-files`

## [2.0.0] - 2025-12-15

### Added
- [Agent Skills](https://agentskills.io/specification) compatible skill format
- Installation from cloned repo (`npx skills add ./ai-assistant-starter`)
- Selective skill installation (`npx skills add ./ai-assistant-starter -s commit`)
- 40 self-contained skills in `skills/<name>/SKILL.md` format
- New workflow skills: `/test-coverage`, `/deps`, `/docs`, `/hotfix`, `/release`, `/revert`, `/sync`, `/finish`, `/add-story`, `/add-todo`, `/track-files`
- 19 background skills: core execution protocol + 18 domain guideline skills (auto-loaded when relevant)
- Progressive disclosure: metadata at startup, full instructions on activation
- `/init` scaffolds `.ai-project/` with domain-aware context layering
- Explicit gate enforcement patterns with valid/invalid response lists

### Changed
- **BREAKING:** Migrated from `.ai-assistant/` monolithic framework to flat `skills/` directory
- **BREAKING:** Removed chatmode system (explorer, planner, developer, etc.) — replaced by workflow skills
- **BREAKING:** Removed `tasks/` atomic task definitions — consolidated into skill instructions
- **BREAKING:** Removed provider-specific adapter files (`.cursorrules`, `.windsurfrules`, `AGENTS.md`, etc.) — skills are provider-agnostic
- **BREAKING:** Removed `.claude/commands/` directory — replaced by skill invocation via `/name`
- Skills follow the [Agent Skills specification](https://agentskills.io/specification) frontmatter format
- Codebase reduced ~70% (from ~15,100 lines across 90+ files to ~4,300 lines across 40 skills)

### Removed
- `.ai-assistant/` directory (chatmodes, tasks, workflows, providers, universal instructions)
- Provider entry point files (`.cursorrules`, `.windsurfrules`, `.clinerules`, `.junie/`, `AGENTS.md`, `GEMINI.md`, `JULES.md`, `.github/copilot-instructions.md`)
- `.claude/commands/` slash command definitions
- `INDEX.md`, `scope.md`, `.instructions.md`

## [1.0.0] - 2025-11-29

### Added
- Initial release of AI Assistant Framework
- Layered architecture: `.ai-assistant/` (base) + `.ai-project/` (overrides)
- Workflow system with approval gates
  - `/implement` - Full implementation workflow
  - `/debug` - Bug investigation and fixing
  - `/refactor` - Multi-file changes with tracking
  - `/validate` - Code quality checks
  - `/commit` - Review and commit changes
  - `/pr` - Create pull requests
- Chatmode system for role-based permissions
- Domain instruction files (TypeScript, Testing, Git, API, Security, etc.)
- Atomic task definitions in `tasks/`
- Scope system with `--files`, `--uncommitted`, `--branch` flags
- Provider entry points: CLAUDE.md, .cursorrules, .github/copilot-instructions.md

---

## Upgrading

### From 1.0 to 2.0

The 2.0 release is a complete rewrite. To migrate:

1. Remove old framework files:
   ```bash
   rm -rf .ai-assistant .claude/commands
   rm -f .cursorrules .windsurfrules .clinerules AGENTS.md GEMINI.md JULES.md
   rm -rf .junie .github/copilot-instructions.md
   ```
2. Clone and install skills:
   ```bash
   git clone https://github.com/hypefi/ai-assistant-starter.git
   npx skills add ./ai-assistant-starter
   ```
3. Re-initialize project context:
   ```
   /init --update
   ```
4. Review `.ai-project/` for compatibility with the new skill format

### Version Compatibility

| Version | Format | Distribution |
|---------|--------|--------------|
| 2.0.x | [Agent Skills spec](https://agentskills.io/specification) | Git clone + `npx skills add` |
| 1.0.x | Custom `.ai-assistant/` framework | Git submodule / copy |

---

[Unreleased]: https://github.com/hypefi/ai-assistant-starter/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/hypefi/ai-assistant-starter/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/hypefi/ai-assistant-starter/releases/tag/v1.0.0
