# Changelog

All notable changes to AI Assistant Starter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `interaction-boundaries` skill — human-AI interaction boundaries implementing 9 dehumanization rules (no first-person identity, purely functional language, structured output, no uncertainty performance, no empathy simulation, deterministic behavior, focused clarification, no metacognition, fixed interaction patterns)
- `/security-review` skill — systematic security audit with confidence-based reporting
- `/iterate-pr` skill — iterate on PR until CI passes and feedback addressed
- `LICENSE` file (MIT)

## [2.0.0] - 2025-12-15

### Added
- [Agent Skills](https://agentskills.io/specification) compatible skill format
- Distribution via [skills.sh](https://skills.sh) (`npx skills add hypefi/ai-assistant-starter`)
- Selective skill installation (`npx skills add hypefi/ai-assistant-starter -s commit`)
- 40 self-contained skills in `skills/<name>/SKILL.md` format
- New workflow skills: `/cover`, `/deps`, `/docs`, `/hotfix`, `/release`, `/revert`, `/sync`, `/wrap`, `/add-story`, `/create-todo`, `/file-list`
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
2. Install skills:
   ```bash
   npx skills add hypefi/ai-assistant-starter
   ```
3. Re-initialize project context:
   ```
   /init --update
   ```
4. Review `.ai-project/` for compatibility with the new skill format

### Version Compatibility

| Version | Format | Distribution |
|---------|--------|--------------|
| 2.0.x | [Agent Skills spec](https://agentskills.io/specification) | [skills.sh](https://skills.sh) |
| 1.0.x | Custom `.ai-assistant/` framework | Git submodule / copy |

---

[Unreleased]: https://github.com/hypefi/ai-assistant-starter/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/hypefi/ai-assistant-starter/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/hypefi/ai-assistant-starter/releases/tag/v1.0.0
