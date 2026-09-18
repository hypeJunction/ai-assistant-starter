# Changelog

All notable changes to AI Assistant Starter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `apply-template` CLAUDE.md template gains a "Response Formatting" section: use markdown structure (bold key terms, tables for comparisons, headers for multi-section answers) in chat responses, explicitly scoped to presentation rather than length so it doesn't conflict with a stricter verbosity-focused output style like Concise
- `prompt-context-router` enforcement skill — a `UserPromptSubmit` hook that classifies each incoming prompt by task class (reusing the existing mechanical/implementation/debugging/architecture/extreme taxonomy) and by whether it looks like a topic pivot versus a continuation of the current thread, then injects `additionalContext` advising standalone treatment for clear asides — with a `dispatch`-subagent delegation suggestion for cheap ones, and a "verify it still depends on context" caution for debugging/architecture/extreme ones. Independently, it also nudges Plan Mode based on task class alone: `abstain`-classified prompts get pointed at `context-disambiguation` (ask a clarifying question first), `architecture`-classified prompts get an `additionalContext` suggestion to call `EnterPlanMode`, and the first `extreme`-classified prompt per session gets denied outright (`permissionDecision: "deny"`) to force that check — since hooks can't set `permission_mode` themselves (it's read-only input), a deny is the only way to force engagement; every later `extreme` prompt in the same session downgrades to the same advisory nudge, tracked via a one-boolean session-keyed state file in `os.tmpdir()` (mirroring `context-circuit-breaker`'s state pattern) so an already-approved extreme-scope task doesn't get re-denied on every continuation. Configurable via `PROMPT_CONTEXT_ROUTER_EXTREME_MODE` (`enforce` default, `warn-only` to disable the deny). Otherwise stateless, fails silent on continuations and when already in Plan Mode, never blocks debugging/architecture prompts. `apply-template` gains a Step 5.8 install gate, and `scripts/merge-settings-hook.js` gains an `--event <event>` flag (defaulting to `PreToolUse` for backward compatibility) so hooks can be merged under `hooks.UserPromptSubmit` instead. `context-disambiguation` and `plan` each gain a one-line "See also" cross-reference to this hook
- `apply-template` gains a Step 5.7 offering verified, opt-in `settings.json` env vars (`DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `CLAUDE_CODE_FORK_SUBAGENT`, and the `BASH_*` timeout/output-length bounds), each selected individually via `AskUserQuestion`; `scripts/merge-settings-hook.js` gains `--env KEY=VALUE` support (repeatable, combinable with `--command`/`--matcher`), merging into `settings.json`'s top-level `env` object with the same idempotent/dry-run/backup-first guarantees as the existing hook merge. `docs/cost-optimization.md` documents the new lever and its `settings.json` skeleton, and adds a "Fork mode" section clarifying what `CLAUDE_CODE_FORK_SUBAGENT` actually controls (whether Claude can spawn `fork`-type subagents at all, and their background-scheduling behavior) versus what it doesn't (non-fork subagents are always isolated regardless of this setting) — a circulating PSA about this var overstated the latter
- `start` workflow skill — scope a new work session to a ticket, worktree, and goal before any code is written, auto-triggering on session start and also invocable manually
- `done` workflow skill — close out a /start session: commit, create or update the PR, record the session outcome, and nudge context compaction

### Changed
- `cost-audit` now scopes every Langfuse query to one user by default: `langfuse_queries.py` gains a `--user`/`LANGFUSE_USER_ID`-sourced filter (a shared org-wide Langfuse project previously mixed every engineer's traces into one audit), and `RATES` gains entries for `claude-sonnet-5` (corrected to $2/$10), `claude-opus-5`, `claude-haiku-4-5`/`-20251001`, `claude-sonnet-4-6`, `claude-sonnet-4-5-20250929`, and `claude-fable-5`/`-5-1` so `reconcile` no longer reports untracked models. `SKILL.md` documents the new env var and a "Scope to one user by default" constraint
- `CLAUDE.md.template`'s "Verification Reporting" section now also covers ad-hoc verification scripts (Playwright/Node one-offs) and dev-server process management (start/stop/kill), not just named test/lint/build commands, and its "Delegate long sequential traces" bullet in "Context & Process Hygiene" names checking status/log/diff or reading files across multiple git worktrees of the same repo as a concrete trigger — both sourced from a `/cost-audit` run that found a 337-tool-call trace running `go test`/`go vet`/`golangci-lint`/Playwright checks inline, and two other traces doing dozens of sequential worktree checks inline
- Verification-subagent reporting is now sized to outcome instead of uniformly maximal: `ai-assistant-protocol` § Validation Execution's "How to Delegate" step now requires full raw output only on failure/ambiguous results, and only a command+exit-code+one-line-result plus one representative raw-output sample per scenario on a clean pass; the 8 skills that cross-reference that section (`finish`, `test-coverage`, `e2e`, `api-test`, `tdd`, `hotfix`, `migrate`, `accessibility-review`) and `validate` get the same one-phrase update rather than restating the rule. `CLAUDE.md.template` gains a new "Verification Reporting" section so consumer projects get this even without `ai-assistant-protocol` installed. `session-retro` gains an "Over-verbose verification report" finding pattern and a worked prompt-phrasing example for the case that motivated this change

### Added
- `cost-guardrail` enforcement skill — `PreToolUse` hook (matched on `Agent` and `Bash`) that compares a requested subagent model tier (or Bash) against historical cost baselines produced by `cost-audit`'s new `build_cost_baselines.py`, and warns (`warn-only`, default) or blocks (`enforce`) when the requested tier's historical median cost is disproportionate (default 3x) relative to the cheapest tracked tier; fails open on missing/stale/insufficient baseline data. `cost-audit` gains a Step 1a-baseline (refreshes `.claude/cost-audit/cost_baselines.json`) and a "Continuous Baseline Refresh" section documenting a weekly reminder-only cadence via the `schedule` skill — the reminder never runs the aggregation script itself, since that needs live Langfuse credentials and its own token cost. `apply-template` gains a Step 5.6 mirroring 5.5's install gate, and `scripts/merge-settings-hook.js` is generalized to accept `--command`/`--matcher` so both circuit-breaker and cost-guardrail share one idempotent settings-merge script (previously hardcoded to circuit-breaker's single `"*"` matcher). Note: `cost-guardrail` uses the `hookSpecificOutput.permissionDecision` protocol (matching `context-circuit-breaker` and `docs/cost-optimization.md`); `branch-protection` and `destructive-command-protection` still use an older bare `{decision, reason}` shape — worth a follow-up alignment pass, not done here
- `context-circuit-breaker` background/enforcement skill — a `PreToolUse` hook (matched on every tool) that warns, never blocks, on subagent fan-out (5+ `Agent`/`Task` spawns in a 5-minute rolling window) or expensive-call loops (4+ near-identical or oversized calls to the same tool in that window); `apply-template` gains an opt-in Step 5.5 and `scripts/merge-settings-hook.js` to idempotently wire the hook into a target's `settings.json` behind the same dry-run/backup/approval gate as its other writes
- `stack` workflow skill — splits a large branch into a resumable series of stacked PRs, one worktree per bucket, with a `stack-plan.md` manifest, remote-ref-based divergence checks, per-bucket validation against a captured baseline, and PR-base verification after creation
- `spec-loop` workflow skill — scope-locked implementation loop: baseline pre-existing failures, get an explicit file-scope contract (allowed files, forbidden actions, open questions) approved before any code changes, write failing tests, implement within scope, and self-check every commit's diff against the contract before committing
- `apply-template` CLAUDE.md template gains "Scope Discipline" (no unrequested selectors/tests/refactors/commits; no deleting exports without evidence they're dead) and "Repo & Branch Pre-Flight" (confirm target directory/worktree and re-fetch remote refs before install, rebase, or base-branch decisions) sections
- `refactor` skill requires a naming-options table, approved before any file is touched, when a rename targets shared or overloaded vocabulary
- `git-conventions` codifies a fetch-first rule: always `git fetch origin` and compute divergence/merge-base against `origin/<branch>`, never a stale local ref

### Added
- `context-disambiguation` background skill — protocol for asking targeted clarifying questions instead of broad exploration when a prompt is ambiguous and resolving it would require an unbounded search, reading many files, or a disambiguation-only subagent dispatch; includes an Auto Mode interaction rule (narrowest-interpretation-plus-stated-assumption, not silent broad-scope guessing)

### Added
- `apply-template` CLAUDE.md template gains an "AI-Generated Text Conventions" section: caps comment length at one line, caps concept explanations at one paragraph, bounds agent verbosity generally, and requires all AI-generated text (comments, docs, PR/commit prose) to describe the codebase's current state for a real reader rather than narrating the change history or reading like a changelog
- `apply-template` script `write-further-reading.sh` generates the "Further Reading" CLAUDE.md section from only the companion READMEs actually copied into a target's `docs/`, merged via the same marker mechanism

### Fixed
- `apply-template`'s "Further Reading" section moved out of the always-merged `CLAUDE.md.template` — it previously listed all three companion READMEs unconditionally, producing dead `docs/README-*.md` links on any target where the user didn't install some or all of them (or has no `docs/` at all)

### Changed
- `/commit` clarifies body wrapping ("wrap at 72 chars/line", not "72 chars total") and switches subject casing to lowercase-after-prefix, matching Angular/Kubernetes/Conventional Commits practice — `git-conventions` previously said "Capitalize first letter," contradicting both `/commit`'s own examples and `/pr`'s lowercase title examples
- `/commit` auto-derives a `Refs TICKET-123` footer from a ticket encoded in the branch name (per `git-conventions` branch naming) instead of leaving ticket references entirely manual, without asking per-commit the way `/pr` asks once per branch
- `/commit` adds an optional DCO `Signed-off-by` trailer (`git commit -s`), gated by a new `git.dco_signoff` config key, alongside the existing `git.ai_attribution`-gated AI co-author trailer
- `/cost-audit` now measures context depth, not just size. `context_depth_per_call` (mean tokens transmitted per model call) is a first-class outlier metric and offenders are ranked by `recoverable_cost` — what a trace would have cost at the window's median depth — because cost, token counts and tool-call counts are all totals that scale with how long a trace ran and therefore measure how *big* it was, not how *wasteful*
- `/cost-audit` no longer treats a high cache-read percentage as a clean bill of health. Context re-transmission (cache read + cache write) is typically ~85-90% of spend, so that number locates the cost rather than clearing it; the audit's stop condition now also requires negligible recoverable depth and an empty `underuse_profile`
- `cache_read_pct` is superseded by `token_economics`, which splits the four billed token classes, reports rate-invariant `cost_shares` in base-input-equivalents, and adds `cache_churn_ratio`. The old ratio divided cache reads by (fresh input + cache reads); because `usageDetails.input` is fresh input only, it pinned at ~99.99% on any window where caching worked at all and could not distinguish a well-run window from a badly-run one. `cache_read_pct` remains as a command alias
- `error_pct` additionally reports `error_pct_of_cost_bearing`; wrapper spans can be ~40% of all observations and cannot fail in a costly way, so including them understates the real rate (1.7x on a measured window)
- `duplicate_tool_calls` groups near-duplicates (same retrieval at a different `offset`/`limit`) and ranks by `wasted_output_bytes` rather than `repeat_count`, since one repeated 500KB read costs far more than fifty repeated `git status` calls
- `drill` now reports `input_bytes`, `output_bytes` and `payload_kind` alongside the existing 300-char preview — payload size is what drives context depth, and truncation discarded exactly that

### Fixed
- `/session-retro` deduplicates token usage on `message.id`. One assistant message spans multiple transcript lines, each repeating the same `usage` object, so the previous per-line sum counted the same tokens once per content block — a workload-dependent 1x-14x overcount that produced plausible but wrong figures (large enough to imply more output tokens than a window physically contains). The avoided factor is now reported as `usage_overcount_factor_avoided`

### Added
- `/apply-template` skill — applies a standardized CLAUDE.md template (Task Classification model-tier table, a Search & Relevance Protocol, and Context & Process Hygiene rules) to an existing installation via marker-delimited, idempotent merge scripts (dry-run diff by default, backs up the existing `CLAUDE.md` first). Also offers companion reference READMEs (`README-cost-optimization.md`, `README-search-relevance.md`, `README-security-scripts.md`) for install into the target project's `docs/`, each selected individually rather than installed wholesale. All three install scripts are dependency-free POSIX shell with no network access, documented and independently verified against a `curl|wget|eval|source` grep
- `/tooling-audit` skill — audits installed Claude Code plugins, MCP servers, skills, and permission entries against usage evidence (`~/.claude.json` `pluginUsage`/`skillUsage` counters, optionally cross-referenced with `/cost-audit`'s Langfuse tool-usage histogram), separates "dead everywhere" from "used elsewhere but irrelevant to this project" and "hard dependency of another installed skill," and gates every disable/unlink/removal on per-item approval; includes `references/dead_permission_patterns.md` (structural detection rules for permission entries that can never match a future command, e.g. embedded heredocs, hardcoded resolved paths/ports, stray shell-loop fragments)
- `/cost-audit` `payload_profile` — tool-result sizes by tool with an image/text split and the oversized payloads listed. The split decides the remedy: images cannot be grepped or paginated, so an image-dominated problem needs fewer or smaller captures, whereas oversized text yields to a bounded search or `limit`/`offset`
- `/cost-audit` `underuse_profile` — cheaper paths that were available and not taken: Bash search/dump calls against Grep/Glob usage, and delegation share of tool calls. Every other query looks for something happening too much; two of the largest depth drivers are something happening too little, which no frequency histogram can surface
- `/cost-audit` `exporter_health` — detects the double-export condition the skill already documented but never measured (both Claude Code's native OTel exporter and the langfuse-observability plugin pointed at one project), and reports how much tool activity the cost-bearing spans actually saw
- `/cost-audit` `reconcile` — asserts recorded `totalCost` against tokens × published rates per model, catching a null `model`, observations with tokens but no cost, and a stale rate table. Note Opus 4.8 / Opus 5 are $5/$25 per MTok, not $15/$75
- `/cost-audit` `all` now writes a small `summary.json` to read first, so the audit's own context cost stays low
- `/session-retro` reports `context_depth_per_call`, `tool_calls_per_message` and `cache_churn_ratio`
- `tests/skills/cost-audit-metrics.test.js` — offline tests for the metric helpers using synthetic observations, so the audit's judgements are verifiable without a live Langfuse instance
- `/session-retro` skill — analyzes the current (or a specified) session transcript for missed skill triggers, redundant/duplicate tool calls, ignored existing instructions, and mid-session user corrections; separates findings into codebase-side fixes (CLAUDE.md/skill diffs, gated on approval) and prompt-side tips (concrete before/after phrasing examples grounded in the actual request that caused friction); includes `references/session_transcript_analyzer.py` (stdlib-only Python parser for the local `.jsonl` transcript format)
- `/cost-audit` skill — pulls Langfuse trace data (cost per session, exact-duplicate tool calls, error rate, cache-read health), root-causes the worst offenders (stuck polls, re-verification reads, retry-after-error, browser-automation retries), and proposes evidence-backed CLAUDE.md/skill corrections with a per-diff approval gate and a recorded baseline for follow-up verification; includes `references/langfuse_queries.py` (stdlib-only Python client for the Langfuse public API), including a `session_sequences` query that orders each session's traces chronologically and flags cross-trace waste a trace-only view can't see — cross-trace duplicate tool calls, input-token growth without matching new tool work, and model-tier escalation immediately after an errored trace. Added deterministic `classify`/`ranked_findings` output (`classified_findings.json`, `ranked_findings.json`) that assigns each duplicate-call group a pattern label (stuck-poll, retry-after-error, re-verification-read, browser-automation-retry, skill/subagent-over-dispatch) from call timing, error adjacency, and tool-sequence signatures alone, and ranks findings by outlier metrics — replacing manual drill-and-eyeball classification for the common cases; `drill`/transcript reads are now reserved for confirming the `redundant-context-refetch` catch-all and `ignored correction` findings
- `/research` skill — ethical web research with attribution tracking, license detection, citation-based output, and compliance checklist references
- `THIRD_PARTY_NOTICES.md` — centralized third-party content attribution for CC-BY (WCAG 2.1, Conventional Commits) and CC-BY-SA (OWASP Top 10, OWASP API Top 10) derived content
- `category:` field in YAML frontmatter for all 52 skills — taxonomy: `process` (23), `meta` (7), `guideline` (16), `protocol` (4), `enforcement` (2)
- Acceptance test tables on 10 key workflow skills (implement, debug, commit, review, plan, explore, refactor, validate, tdd, finish) — positive/negative/boundary trigger tests for skill routing validation
- `branch-protection` enforcement skill — runtime PreToolUse hook that blocks force-push, hard reset, and branch deletion on protected branches; includes `references/hook.js`
- `destructive-command-protection` enforcement skill — runtime PreToolUse hook that blocks rm -rf on critical paths, DROP DATABASE, disk formatting, fork bombs, and other destructive commands; includes `references/hook.js`
- Task tier classification system in `/implement` (nano/small/medium/large) — scales workflow phases based on task complexity; nano skips planning, large suggests PR
- Change tier classification in `/commit` (nano/small/medium/large) — scales validation requirements based on change size
- Structured `config.yaml` replacing `config.md` — 15 settings across workflow, git, quality, display, enforcement, and approval sections with typed defaults
- Work queue fields in todo template — `estimated_effort` (nano/small/medium/large), `queue_position`, `blocked_by`; file naming convention: `NNN-{name}.md`
- Reference documentation for `/security-review` — modular references for quick patterns, modern threats, supply chain security, and infrastructure security; expanded OWASP API Security Top 10 in security checklists
- Reference documentation for `/implement`, `/debug`, `/commit` — plan templates, task decomposition, root-cause tracing, defense-in-depth, debugging techniques, commit conventions, pre-commit verification
- Reference documentation for `/tdd`, `/review`, `/finish`, `/plan` — TDD rationalizations and troubleshooting, review checklist and feedback patterns, finish options, plan quality checklist
- Reference documentation for `/accessibility-review`, `/e2e`, `/api-test` — screen reader testing, a11y remediation patterns, flaky test prevention, API mock and factory patterns
- Reference documentation for `/validate`, `/refactor`, `/migrate` — security scan patterns, validation troubleshooting, safe refactoring patterns, rollback cookbook
- Context-aware guideline loading tables in `/implement`, `/debug`, `/review` — auto-loads relevant guideline skills based on detected code types
- Cross-skill reference linking across 7 reference files — See Also sections connecting related content (regression testing, test isolation, security checklists, evidence-before-claims)

### Changed
- `/cost-audit` skill — `trace_outliers` now carries `generation_count` and `avg_cache_read_per_generation` per trace, and a new "Context-multiplication" pattern distinguishes cost driven by many genuinely-distinct LLM turns each re-paying cache-read on a large accumulated context from cost driven by duplicate/wasted calls; routes Context-multiplication findings to `/session-retro`'s structural fixes instead of drafting a CLAUDE.md line for them; adds `references/static_footprint.py` (stdlib-only, no Langfuse credentials needed) measuring the fixed per-turn context floor — CLAUDE.md files with `@file` imports resolved, plus every installed skill's frontmatter description — as the "what should the baseline be" counterpart to compare against the observed `avg_cache_read_per_generation`/`avg_cache_read_per_message`
- `/session-retro` skill — new "Structural / Agentification Recommendations" output category (own approval gate) for two new pattern types: oversized skill footprint (a skill's own `SKILL.md`/`references/*.md` loaded in full and carried for the rest of the session) and inline exploration that should be delegated to a subagent; `references/session_transcript_analyzer.py` now surfaces `context_multiplication_signal` (avg cache-read tokens per message) and `largest_tool_results` (the biggest tool_result payloads, with their originating tool call) as evidence for these
- Skill instructions now use target-agnostic language — "subagent" → "parallel agent", "glob/grep" → "file/content search", Claude-specific Co-Authored-By → configurable `git.ai_attribution`
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
- Updated `/finish` — added Phase 8 (Close Todos) that scans for todos completed by the session's work, creates ADRs for design decisions, and deletes closed todos
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

### Fixed
- Added legally required CC-BY attribution to `accessibility-review/references/wcag-checklist.md` (W3C WCAG 2.1, CC BY 4.0), `git-conventions/SKILL.md` and `commit/references/commit-conventions.md` (Conventional Commits, CC BY 3.0)
- Added source citations to `security-review/references/security-checklists.md` (OWASP Top 10, OWASP API Top 10) and `security-review/references/supply-chain.md` (SLSA framework)

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
