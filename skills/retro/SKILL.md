---
name: retro
description: Mine session transcripts, Langfuse cost traces, and installed-tooling usage evidence for waste and drift, then propose evidence-backed CLAUDE.md/skill/config corrections gated by approval. Flags pick the source(s) and window up front — the skill never stops mid-run to ask which mode. Use after a cost spike, when a session felt inefficient, or periodically to catch tooling clutter.
category: process
triggers:
  - retro this session
  - audit token cost
  - what plugins are unused
  - clean up claude settings
  - why is this expensive
  - session retro
  - audit our tooling
  - find wasted tokens
---

# Retro

> **Purpose:** Turn one evidence source (or all three) into ranked, evidence-cited config corrections.
> **Usage:** `/retro [--session|--cost|--tooling|--all] [--since=7d] [--apply]`

## Flags

| Flag | Effect |
|---|---|
| `--session` | Mine the current (or a specified) session transcript for behavioral friction. Default when no source flag is given. |
| `--cost` | Mine Langfuse trace data for token-cost waste. |
| `--tooling` | Mine installed plugin/MCP/skill/permission usage evidence. |
| `--all` | Run all three sources in one pass; merge findings into one report and one approval gate. |
| `--since=<duration>` | Evidence window, e.g. `24h`, `7d`, `30d`. Default `7d`. |
| `--apply` | Apply approved diffs immediately after the gate, instead of only reporting them. |

All options resolve from flags (or their defaults) at invocation. Never pause mid-run to ask which source or window to use.

## Workflow

1. **Gather evidence** — for each selected source, delegate the mining step to a subagent (prefer the `auditor` agent; fall back to `general-purpose`). Give it the source, the `--since` window, and the exact script/path below to run. It returns parsed JSON/counter output, not raw logs.
2. **Rank findings** — apply the per-source rules below; keep only genuine, high-impact findings, and state explicitly which checks came back clean.
3. **Propose diff** — one concrete, testable change per finding: exact line(s) for CLAUDE.md / a skill / `settings.json`, with cited evidence (timestamp, trace ID, or `usageCount`/`lastUsedAt`).
4. **Approval gate** — present the full report; get per-item approval via `AskUserQuestion` (Apply / Skip / Edit first) before touching any file. This gate always runs, with or without `--apply`.
5. **Apply if `--apply`** — write only approved diffs. Back up `settings.json` before editing it; validate JSON after.
6. **Verify** — record the finding and its count/ratio so a later `/retro` run on the same source can confirm the targeted pattern's rate actually dropped.

## Source: `--session`

Data: the transcript JSONL at `~/.claude/projects/<project-slug>/<sessionId>.jsonl` (current session = newest-mtime file in the project dir, or the session UUID from the scratchpad path in this environment's system prompt). Parse with `skills/retro/references/session_transcript_analyzer.py` (stdlib-only, Python 3.8+): tool-call histogram, exact-duplicate calls, `Read`-after-`Edit` re-verification, candidate user-correction turns, `context_multiplication_signal` (`message_count`/`avg_cache_read_per_message`), `largest_tool_results`, and `prompt_context_outliers`. Compare its `skills_invoked` output against every installed skill's triggers/description (project-scoped, user-global, and plugin-supplied — check all three locations) to catch a missed trigger. Waste patterns: missed skill trigger, ignored existing instruction, redundant re-fetch, oversized skill footprint, inline exploration that should have been delegated.

## Source: `--cost`

Data: Langfuse traces via `skills/retro/references/langfuse_queries.py` (stdlib-only). Needs `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`/`LANGFUSE_BASE_URL`/`LANGFUSE_USER_ID` — the first three and the user ID live in `~/.claude/settings.json` under `pluginConfigs["langfuse-observability@langfuse-observability"].options`, the secret in `~/.claude/.credentials.json` under `pluginSecrets[...]` (or decode it from a base64 `Authorization: Basic` header in `OTEL_EXPORTER_OTLP_HEADERS` on older installs). Run `langfuse_queries.py all --out-dir <dir>` for `summary`, `trace_outliers`, `duplicate_tool_calls`, `token_economics`, `session_sequences`, `classified_findings`, `ranked_findings`, `prompt_context_mismatch`; rank by `recoverable_cost` (spend above the window's median `context_depth_per_call`), not raw totals. Also run `skills/retro/references/static_footprint.py` (CLAUDE.md + skill-index token floor) and `skills/retro/references/boot_cache_health.py --days <since>` (cross-session cache-miss rate vs. recent CLAUDE.md/SKILL.md edits) for the two fixed-baseline checks. Waste patterns: context-multiplication, stuck poll/runaway loop, retry-after-error, cross-trace redundant fetch, escalation-after-failure, boot cache miss.

## Source: `--tooling`

Data: `~/.claude.json`'s `pluginUsage`/`skillUsage` counters (`usageCount`/`lastUsedAt` per plugin/skill, across every project) plus `~/.claude/settings.json` (`permissions.allow`/`deny`, `enabledPlugins`, `mcpServers`, `pluginConfigs`) and `~/.claude/plugins/installed_plugins.json` (`scope`: `user` loads everywhere, `local` is already project-scoped). Classify permission entries structurally, not by counter — see `skills/retro/references/dead_permission_patterns.md` for dead-pattern shapes (embedded heredocs, hardcoded resolved paths/ports, stray loop fragments). Cross-reference the `--cost` source's `tool_usage.json` when available for per-MCP-tool granularity. Run `skills/retro/references/warmup_footprint.py --days <since>` for the CLAUDE.md/settings.json startup-footprint axis across active projects and worktree clusters. Waste patterns: dead plugin/skill (`usageCount: 0`, no hard dependency), used-but-irrelevant-here (rescope, don't remove), structurally-dead permission entry, hard dependency (never remove — check every other installed skill's Prerequisites for a reference to it first).

## Rules

- Evidence before edits — every proposed change cites a transcript excerpt, trace ID, or `usageCount`/`lastUsedAt`. No unsupported "be more careful" advice.
- Never write to CLAUDE.md, a skill file, or `settings.json` before the approval gate — `--apply` changes *when* it writes, not whether the gate runs.
- `--all` merges findings into one report and one approval pass, not three separate gates.
- Distinguish "dead everywhere" from "unused in this project" (tooling), and "real friction" from "normal work" (session) — drop false positives rather than reporting them.
- Record a baseline after every applied change so a later `/retro --since=...` run on the same source can confirm the fix worked.
