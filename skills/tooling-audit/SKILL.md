---
name: tooling-audit
description: Audit installed Claude Code plugins, MCP servers, skills, and permission entries against real usage evidence and propose removing what's actually dead weight, gated by approval.
category: process
triggers:
  - audit installed skills
  - what plugins are unused
  - clean up claude settings
  - trim installed tools
  - audit mcp servers
  - what should we uninstall
  - claude code feels cluttered
  - unused skills or plugins
---

# Tooling Audit

> **Purpose:** Turn `~/.claude.json` usage counters (and, optionally, Langfuse tool-call histograms) into evidence-backed removals of unused plugins, MCP servers, skills, and permission entries — then gate every change behind approval.
> **Usage:** `/tooling-audit`

## Constraints

- **Evidence before removal** — never propose disabling a plugin, unlinking a skill, or deleting a permission entry without citing its actual `usageCount`/`lastUsedAt`, or (for permission entries) the structural reason it can never match again. "Looks unused" is not evidence; the counter is.
- **Dead-everywhere vs. irrelevant-here are different findings** — a plugin or skill with real usage elsewhere is not a removal candidate just because it's unrelated to the current project's stack. Global config loads for every project on the machine; conflating "not for this repo" with "not for anything" produces a bad recommendation that breaks someone else's session.
- **Check for hard dependencies before touching a plugin** — one skill's Prerequisites can silently depend on another plugin's config (e.g. an observability skill reading Langfuse credentials out of a tracing plugin's `pluginConfigs` block). A plugin firing 200+ times is not "stale" just because its purpose isn't obvious from its name.
- **Gate before writing** — present the full inventory and every proposed removal; apply nothing until the user approves it, item by item.
- **Reversible over destructive** — unlink, don't delete. Flip a flag, don't hand-edit a lock file. Back up before editing global config.

## Prerequisites

- Read access to `~/.claude/settings.json`, `~/.claude.json`, `~/.claude/plugins/installed_plugins.json`, and `~/.claude/skills/` (and the project's `.claude/settings.json` / `.claude/settings.local.json` / `.claude/skills/` if present).
- Optional: a reachable Langfuse instance for Step 2b's supplementary MCP-tool-level cross-reference. Not required — Step 2a's local counters are sufficient to run the audit end to end.

## Workflow

Four steps: **inventory** everything installed, **pull usage evidence** for each item, **classify** each into keep/remove/rescope, then **gate and apply**.

### Step 1: Inventory the Installed Surface

**1a. Global config** — read `~/.claude/settings.json`:
- `permissions.allow`/`permissions.deny` — every entry
- `enabledPlugins` — note which are `true`/`false`, and each plugin's `scope` from `~/.claude/plugins/installed_plugins.json` (`"user"` = loads in every project on the machine; `"local"` = tied to one `projectPath`, already scoped correctly, out of scope for this audit unless that specific project is the one being audited)
- `mcpServers` — global MCP server definitions
- `pluginConfigs` — note which plugins have stored credentials/config; anything depending on one of these is a hard dependency (see Step 3)

**1b. Project config** — same shape, read from the current project's `.claude/settings.json`, `.claude/settings.local.json`, and `.mcp.json` if present. Project-scoped permission entries and MCP servers were deliberately added for this repo — they need the same evidence-before-removal treatment, not a pass.

**1c. Skills** — enumerate `~/.claude/skills/` (resolve each symlink target — most point into a package-manager-controlled skill store like `~/.agents/skills/`, some point directly into a plugin's cache dir) and the project's own `.claude/skills/` (skills the project vendored on purpose — different bar for removal than global clutter). Note which global skills are plain directories (bundled with a specific plugin) vs. symlinks (independently installed).

**1d. Cross-check scope** — a `scope: "local"` plugin or a project-vendored skill that only activates inside its own `projectPath` isn't cluttering *other* sessions even if it looks irrelevant to the one you're auditing from. Only user-scoped (global) items are candidates for "this loads everywhere and shouldn't."

### Step 2: Pull Usage Evidence

**2a. Local counters (always available, no setup)** — Claude Code tracks its own invocation counts in `~/.claude.json`:

```bash
python3 -c "
import json
d = json.load(open('$HOME/.claude.json'))
print(json.dumps(d.get('pluginUsage', {}), indent=2))
print(json.dumps(d.get('skillUsage', {}), indent=2))
"
```

Each entry carries `usageCount` and `lastUsedAt` (unix ms). This is the primary evidence source — it needs no credentials and covers every plugin and every skill name Claude Code has ever dispatched, across all projects. A name with **no entry at all** is not automatically "unused" — it may predate usage tracking, or be tracked under a different name after a rename; treat "no data" as weaker evidence than an explicit `usageCount: 0` and say so in the report.

**2b. Langfuse cross-reference (optional, supplementary)** — if this project also has the `cost-audit` skill installed (check for a sibling `skills/cost-audit/references/langfuse_queries.py`) and Langfuse credentials are resolvable (same lookup cost-audit's Prerequisites describe: `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_BASE_URL` from `pluginConfigs["langfuse-observability@langfuse-observability"]`, secret key decoded from `OTEL_EXPORTER_OTLP_HEADERS`), run:

```bash
python3 <path-to-cost-audit>/references/langfuse_queries.py tool_usage --out-dir ./cost_audit_out
```

This gives a per-**tool** invocation histogram (including individual MCP tool names like `mcp__playwright__browser_navigate`), which is finer-grained than plugin/skill counters — useful for telling apart "is the playwright MCP server actually being called" from "is it just configured." If a recent `cost_audit_out/tool_usage.json` already exists, reuse it instead of re-querying. **If Langfuse isn't reachable or `cost-audit` isn't installed, skip this step and say so explicitly in the report** — don't silently omit it, and don't block the rest of the audit on it.

**2c. Permission entries have no usage counter — classify structurally instead.** A literal (non-wildcarded) `Bash(...)`/`Read(...)`/`WebFetch(...)` pattern is dead the moment it can never match a *different* future command, independent of whether it was ever used. See `references/dead_permission_patterns.md` for the concrete shapes (embedded heredocs, hardcoded resolved absolute paths, hardcoded ports, stray shell-loop fragments like a bare `for x in a b c` or `do`/`done` split out of a multi-line command).

### Step 3: Classify Each Item

For every plugin, MCP server, skill, and permission entry from Step 1, assign one label:

| Label | Criteria | Action |
|---|---|---|
| **Dead** | `usageCount: 0` (or a structurally-dead permission pattern) with no hard dependency | Propose removal |
| **Used, irrelevant here** | Nonzero usage, but the item belongs to a stack/domain the current project's CLAUDE.md never touches | Do NOT propose global removal — recommend project-scoping instead (move to the *other* project's `.claude/skills/`, or leave it — a global item being irrelevant to *this* session doesn't make it clutter for the sessions that use it) |
| **Hard dependency** | Another installed skill's Prerequisites/body references this plugin's `pluginConfigs` entry, or another config depends on this MCP server/permission | Never propose disabling — state the dependency explicitly in the report even if usage looks low |
| **Active** | Nonzero usage, relevant, no conflict | Leave alone; list only if the user specifically asked about it |

**Before finalizing any "Dead" plugin classification**, grep every other installed skill's `SKILL.md` for a reference to that plugin's name or its `pluginConfigs` key. A plugin can have a high usage count purely because it fires a hook on every tool call (e.g. an observability exporter) — that's still real usage, not noise, and disabling it can silently break whatever reads its output.

### Step 4: Gate and Apply

**4a. Present the full report** (Output Format below) before writing anything.

**GATE: user approves each proposed removal individually.** Some may be approved, others rejected or deferred.

**4b. Apply only approved items, following the reversibility rule for each surface:**

| Surface | How to remove | Never do this |
|---|---|---|
| Global/project `settings.json` permission entry | `cp settings.json settings.json.bak-<date>` then edit the array; validate with `python3 -c "import json; json.load(open(...))"` after | Regex/sed on the JSON file |
| Plugin | Flip `enabledPlugins["<id>"]` to `false` (or remove the key if already `false`) | Hand-edit `installed_plugins.json`'s version/cache bookkeeping |
| Global skill | Remove the symlink in `~/.claude/skills/` (`rm <name>`, or restore with `ln -s <target> <name>`) | Delete the underlying skill source directory, or edit the package manager's lock file (e.g. `.skill-lock.json`) |
| MCP server | Remove the entry from `mcpServers` in the relevant `settings.json`/`.claude.json`/`.mcp.json` scope | — |

**4c. Record what was checked and what survived**, so a future audit run doesn't re-litigate approved-to-keep items without new evidence.

## Output Format

```markdown
# Tooling Audit Report — [date]

## Inventory
- Plugins: [N] user-scoped, [M] project-local-scoped (out of scope here)
- MCP servers: [N] global, [M] project
- Skills: [N] global (symlinked), [M] global (plugin-bundled), [K] project-vendored
- Permission entries: [N] allow, [M] deny

## Evidence Sources
- Local counters (`~/.claude.json`): available
- Langfuse tool-usage cross-reference: [available, used | skipped — reason]

## Findings

### Dead — propose removal
| Item | Type | Evidence | Hard dependency? |
|---|---|---|---|
| [name] | plugin/skill/mcp/permission | usageCount 0 (last used [date] or never) / [structural reason] | none found |

### Used, Irrelevant Here — recommend rescoping, not removal
| Item | Type | Usage | Why it's irrelevant to this project | Recommendation |
|---|---|---|---|---|

### Hard Dependencies Found — do not disable
| Item | Depended on by | How |
|---|---|---|

## Proposed Removals
1. [item] — [exact change: settings.json diff / enabledPlugins flip / symlink to remove]
   **Justification**: [usageCount]/[lastUsedAt] or structural reason

[repeat per proposal]

## Follow-Up
- Kept-and-verified this round: [list, so a future audit doesn't re-ask]
- Re-check when: [e.g. "next time a new plugin/skill is installed, or usage counters show 0 for 60+ days on a currently-active item"]
```

## Rules

### Required
- Every proposed removal cites `usageCount`/`lastUsedAt`, or the specific structural reason a permission entry can never match again — no removal on suspicion alone
- Check every candidate plugin against other installed skills' Prerequisites/body for a hard dependency before proposing to disable it
- Distinguish "dead everywhere" from "used elsewhere, irrelevant to this project" — only the former is a removal candidate
- Present the full report and get per-item approval before writing any file
- Back up `~/.claude/settings.json` (or the project equivalent) before editing it, and validate JSON after
- Never hand-edit a plugin/skill package manager's lock or cache files — only flip `enabledPlugins`/settings entries, or (un)symlink inside `~/.claude/skills/`

### Recommended
- Run periodically, after installing several new plugins/skills/MCP servers in a burst, or when the skill-discovery listing feels cluttered
- Treat "no usage data at all" as weaker evidence than an explicit `usageCount: 0` and say so
- Reuse a recent `cost-audit` run's `tool_usage.json` instead of re-querying Langfuse when one exists
- When in doubt between "remove" and "rescope," rescope — it's reversible and doesn't risk another project's session

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| TA-T1 | Positive | "What plugins can we uninstall?" | Skill triggers |
| TA-T2 | Positive | "This settings.json is a mess, can you clean it up?" | Skill triggers |
| TA-T3 | Positive | "Are we actually using the playwright MCP server?" | Skill triggers |
| TA-T4 | Negative | "Install the Figma MCP server" | Does NOT trigger — that's setup, not audit |
| TA-T5 | Negative | "Why is this session expensive?" | Does NOT trigger (-> `/cost-audit`, which is about token cost, not installed-surface clutter) |
| TA-T6 | Boundary | A plugin has `usageCount: 0` but another skill's Prerequisites reads its `pluginConfigs` credentials | Reported as "Hard Dependency Found," not proposed for removal |
| TA-T7 | Boundary | A skill has real usage but for a different project's stack (e.g. a PHP-CMS skill in a TypeScript-frontend session) | Classified "Used, Irrelevant Here" with a rescoping recommendation, not a removal proposal |
| TA-T8 | Positive | "Why does every session list 60 skills I never use?" | Skill triggers; agent runs `skillUsage` cross-reference and separates dead-everywhere from used-elsewhere-irrelevant-here |
