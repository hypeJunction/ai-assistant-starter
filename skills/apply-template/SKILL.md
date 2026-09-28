---
name: apply-template
description: Apply the AI Assistant Starter CLAUDE.md template (delegation, search-relevance, process hygiene, scope discipline, repo pre-flight, AI-generated text conventions) to an existing installation, retiring superseded marker blocks from a prior template version, and optionally install companion reference READMEs, the `guard`/`context-circuit-breaker`/`cost-guardrail`/`prompt-context-router` hooks, and verified cost-saving settings.json env vars. Use when a project already has skills installed but lacks the standardized CLAUDE.md sections, or to refresh them after a template update.
category: meta
model: sonnet
effort: medium
triggers:
  - apply template
  - adopt claude.md template
  - install claude.md sections
  - refresh claude.md template
  - rewire docs
---

# Apply Template

> **Purpose:** Merge the standardized CLAUDE.md sections into an existing
> installation without disturbing project-specific content, retire any
> marker blocks the template no longer ships, and offer companion reference
> READMEs, enforcement hooks, and cost-saving `settings.json` env vars.
> **Usage:** `/apply-template [--target <path>]`
> **Output:** Updated `CLAUDE.md` (backed up first), any selected
> `docs/README-*.md` files, and — only if opted in — hook entries and/or
> selected `env` vars in `settings.json` (also backed up first).

## Template sections

`assets/templates/CLAUDE.md.template` ships six marker-delimited sections,
each merged independently: `delegation`, `search-relevance`,
`process-hygiene`, `scope-discipline`, `repo-preflight`, `ai-generated-text`.

## Constraints

- **Never write without a diff.** Always run `apply-template.sh` in dry-run
  mode first, show the user the diff, and only re-run with `--apply` after
  they confirm.
- **Never skip the backup.** `backup-claude-md.sh` runs before any write to
  an existing `CLAUDE.md` or `settings.json`.
- **Don't touch content outside the managed marker blocks.** The merge is
  section-scoped; a project's own conventions outside those markers are
  never modified.
- **Ask before installing companion READMEs or hooks** — nothing is
  installed by default; each is its own approval gate.

## Workflow

1. **Refuse to run on this repo itself.** If the target's `package.json` is
   named `ai-assistant-starter`, or it has both a top-level `skills/` and a
   `CLAUDE.md` mentioning the Agent Skills specification, stop and ask the
   user to confirm the actual target (`--target ../my-project`).
2. **Locate the target** — default `./CLAUDE.md`, or `--target <path>`.
3. **Back up** with `scripts/backup-claude-md.sh <target>/CLAUDE.md`.
4. **Dry-run the merge**: `scripts/apply-template.sh
   assets/templates/CLAUDE.md.template <target>/CLAUDE.md`. This prints a
   unified diff and writes nothing. **GATE:** confirm with the user
   (Apply as-is / Trim first / Decline) before proceeding.
5. **Apply**: re-run with `--apply`. Confirm the reported section count
   matches the dry run.
6. **Offer companion READMEs** (`README-cost-optimization.md`,
   `README-search-relevance.md`, `README-security-scripts.md` under
   `assets/readmes/`) — copy only the ones selected via
   `scripts/copy-readmes.sh`, then add a "Further Reading" section listing
   only those files via `scripts/write-further-reading.sh` (dry-run first).
7. **Offer each enforcement hook individually** — `context-circuit-breaker`,
   `cost-guardrail`, and `prompt-context-router` — each behind its own
   **Install/Skip** gate. If installed, copy the hook's `hook.js` (and, for
   `prompt-context-router`, its companion `post-tool-hook.js`) into
   `<target>/.claude/hooks/<name>/`, back up `<target>/.claude/settings.json`,
   then dry-run and apply the merge via
   `scripts/merge-settings-hook.js`. This installs a version-pinned,
   project-local copy independent of whatever the plugin's own
   `hooks/guard/` and `hooks/hooks.json` already wire in globally — offer it
   only when the user wants a copy that won't shift when the plugin updates.
8. **Offer cost-saving env vars** (`DISABLE_TELEMETRY`,
   `DISABLE_ERROR_REPORTING`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`,
   `CLAUDE_CODE_FORK_SUBAGENT`, `BASH_DEFAULT_TIMEOUT_MS`,
   `BASH_MAX_TIMEOUT_MS`, `BASH_MAX_OUTPUT_LENGTH`) via a multi-select
   `AskUserQuestion` — flag that the first three are behavior-neutral and
   the rest change runtime behavior, then dry-run/apply via the same
   `merge-settings-hook.js`.
9. **Report**: what was backed up, which sections were applied/refreshed,
   which marker blocks were retired, which companion READMEs and hooks were
   installed, and which env vars were added. Do not commit.

## Retired marker blocks

`apply-template.sh` also removes four marker blocks the template no longer
ships, so a refresh never leaves superseded guidance installed alongside the
section that replaced it: `task-classification`, `delegation-default`,
`verification-reporting`, `response-formatting`. This runs automatically on
every apply — content outside these specific markers is never touched, and a
target missing a given block is left as-is.

## Security Notes

The five scripts in `scripts/` (four dependency-free POSIX shell, one
dependency-free Node script for JSON-aware merging) make no network calls
and are short enough to read end-to-end before running:
`apply-template.sh`, `backup-claude-md.sh`, `copy-readmes.sh`,
`write-further-reading.sh`, `merge-settings-hook.js`. See
`assets/readmes/README-security-scripts.md` for the specific properties of
each.

## Re-running / Updates

Re-running this skill after the template changes upstream is safe: the
merge is idempotent per marker block (replaces the block's own content,
never duplicates it), always re-backs-up first, and retires any
now-superseded blocks in the same pass.
