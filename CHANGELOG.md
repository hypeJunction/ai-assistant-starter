# Changelog

All notable changes to the AI Assistant Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Provider-specific configurations in `.ai-assistant/providers/`
  - `claude.provider.md` - Full feature support documentation
  - `cursor.provider.md` - Adapted workflows for Cursor
  - `copilot.provider.md` - GitHub Copilot limitations
  - `windsurf.provider.md` - Windsurf/Codeium configuration
  - `gemini.provider.md` - Google Gemini support
- Provider compatibility matrix in `providers/README.md`
- Explicit gate enforcement patterns in all workflows
- Interactive wizard flow for `/init` command
- Template population rules to eliminate unfilled placeholders

### Changed
- Strengthened gate enforcement language in `implement.prompt.md`
- Strengthened gate enforcement language in `refactor.prompt.md`
- Strengthened gate enforcement language in `debug.prompt.md`
- Strengthened gate enforcement language in `commit.prompt.md`
- Enhanced `/init` workflow with confirmation and preference steps

### Fixed
- Gates now include explicit list of valid approval responses
- Gates now list invalid responses that should NOT be treated as approval

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
  - Explorer, Planner, Developer, Tester, Reviewer
  - Architect, Debugger, Committer, Refactorer, Releaser
- Domain instruction files
  - TypeScript, Testing, Git, API, Security, etc.
- Atomic task definitions in `tasks/`
- Scope system with `--files`, `--uncommitted`, `--branch` flags
- Communication templates with visual hierarchy
- Provider entry points: CLAUDE.md, .cursorrules, .github/copilot-instructions.md

---

## Upgrading

### From Pre-1.0 to 1.0.0

If you were using an earlier version:

1. Pull the latest `.ai-assistant/` submodule or update symlink
2. Run `/init --update` to refresh project configuration
3. Review any custom overrides in `.ai-project/` for compatibility

### Version Compatibility

| Framework Version | Compatible Providers |
|-------------------|---------------------|
| 1.0.x | Claude Code, Cursor, Copilot, Windsurf, Gemini |

---

## Migration Notes

### Gate Enforcement Changes

If you have custom workflows, update gate patterns to match the new format:

**Old:**
```markdown
**Approve?** (yes / no)

**⛔ GATE: Wait for approval.**
```

**New:**
```markdown
**Approve?**

Reply with:
- `yes` or `approved` - Proceed
- `no` - Cancel
- `modify: [changes]` - Request changes

**⛔ GATE: STOP HERE. Do NOT proceed until user responds with explicit approval.**

**Waiting for:** `yes`, `approved`, `proceed`, `lgtm`, or `go ahead`
```

### Provider-Specific Behavior

If using multiple providers, check `providers/README.md` for the compatibility matrix. Some workflows may need adaptation for providers other than Claude Code.

---

[Unreleased]: https://github.com/hypefi/ai-assistant-starter/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/hypefi/ai-assistant-starter/releases/tag/v1.0.0
