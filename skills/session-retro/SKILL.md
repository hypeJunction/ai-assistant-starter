---
name: session-retro
description: Analyze the current (or a specified) Claude Code session transcript for behavioral issues — missed skill triggers, duplicate/redundant tool calls, ignored existing instructions, mid-session user corrections — and propose concrete CLAUDE.md/skill edits plus prompt-phrasing tips to prevent recurrence. Use at the end of a session, when something felt inefficient or went sideways, or as a periodic retrospective.
category: process
triggers:
  - review this session
  - session retro
  - what went wrong this session
  - why did this take so long
  - audit this conversation
  - retro on this session
---

# Session Retro

> **Purpose:** Turn one session's transcript into evidence-backed corrections — to the codebase's CLAUDE.md/skills, and to how the user phrases requests — so the same friction doesn't recur
> **Usage:** `/session-retro`

## Constraints

- **Evidence before edits** — every proposed correction cites an actual transcript excerpt (timestamp, tool name, quoted user text). No unsupported "the agent should generally..." advice.
- **Two audiences, two kinds of fix** — a friction point can be caused by a codebase-side gap (missing/unclear CLAUDE.md rule, a skill that should have triggered but didn't) or a prompt-side gap (the request was ambiguous, compound, or under-specified). Diagnose which one it is; don't default to "add a rule" when the real fix is "ask it differently next time."
- **Distinguish real friction from normal work** — not every duplicate tool call or re-read is a mistake (e.g., re-reading a file before a second edit because content genuinely changed is normal). Only flag patterns that wasted turns/tokens without adding information, or that a user explicitly corrected.
- **Gate before writing** — present findings and proposed diffs; do not edit CLAUDE.md, any skill file, or suggest committing anything until the user approves.
- **This is not `/review` or `/finish`** — this skill audits the assistant's own behavior and the conversation that shaped it, not the code changes produced. Route actual code-quality review to `/review`, end-of-session testing/commit to `/finish`.
- **This is the drill-down stage of one pipeline with `/cost-audit`, not a second overlapping skill** — `/cost-audit` works across many sessions via Langfuse and finds *which* sessions/traces cost what (triage); this skill works on one local transcript with full-fidelity tool inputs, per-turn tokens, and the user's actual wording, and explains *why* a specific one went sideways (root cause). Run `/cost-audit` first when the question is "which session," and this skill when the question is "what happened in this one" — including when `/cost-audit`'s `drill` output hit `input: null` on a generic OTel wrapper span and couldn't show the real arguments.

## Prerequisites

- The session's transcript file, JSONL, written to `~/.claude/projects/<project-slug>/<sessionId>.jsonl`. `$CLAUDE_TRANSCRIPT_PATH` is **not** a main-loop environment variable — it's a field in a hook's payload, so it's only available inside a hook script, not to the assistant directly. To locate the transcript instead:
  - **Current session**: the session UUID is a path segment of the scratchpad directory path shown in this environment's system prompt (e.g. `.../claude-1000/<project-slug>/<sessionId>/scratchpad`) — extract it from there. If that's not available, the current session's transcript is whichever `.jsonl` in the project dir has the newest mtime. Note that the current session's transcript is still being appended to as you work, so a retro on "the current session" necessarily includes its own turns up to the point you ran the analysis.
  - **A past session**: ask the user for the session ID, or let them point at the `.jsonl` file directly.
  - A Langfuse `sessionId` from a `/cost-audit` run **is** the Claude Code session UUID — if you arrived here from a cost-audit finding, that ID is the filename to open.
- Python 3.8+ — `references/session_transcript_analyzer.py` is stdlib-only, no dependency install required.
- Read access to the project's CLAUDE.md and every installed skill, so a friction point can be checked against an existing rule that wasn't followed vs. a genuine gap. Skills live in more than one place — check all of them, not just the project:
  - Project-scoped: `.claude/skills/*/SKILL.md`
  - User-global: `~/.claude/skills/*/SKILL.md`
  - Plugin-supplied: `~/.claude/plugins/**/skills/*/SKILL.md` (path varies by plugin manager version — locate via the plugin's installed directory if this doesn't match)

## Workflow

Three steps: **classify** the session's events, **identify** which classified issues actually caused friction, then **propose** fixes for both sides — the codebase and the prompt.

### Step 1: Classify Session Events

**1a. Parse the transcript:**

```bash
python3 references/session_transcript_analyzer.py <path-to-session.jsonl> --out ./session_retro_out.json
```

This surfaces: tool-call histogram, exact-duplicate tool calls, `Read` calls that follow an `Edit`/`Write` on the same file (within a bounded call/time window — not just "ever read after ever edited"), skills invoked, token/cache usage, and candidate "user correction" turns (user messages containing correction language like "no,", "that's wrong", "instead of", "I asked for"; synthetic events like task notifications, hook output, and local-command results are filtered out before this check runs, not treated as user turns). It also surfaces two fields specifically for the structural findings in Step 1c/3a below:

- `context_multiplication_signal` — `message_count` (main-loop turns) and `avg_cache_read_per_message` (mean `cache_read_input_tokens` per assistant message). This is the transcript-side view of `/cost-audit`'s `generation_count`/`avg_cache_read_per_generation` fields — a high `message_count` with a large, roughly flat `avg_cache_read_per_message` means every turn in this session re-paid cache-read on the same large accumulated context.
- `largest_tool_results` — the 8 largest tool_result payloads in the session (size in characters, which tool produced them, and a one-line input summary), e.g. a `Skill` invocation's own `SKILL.md`/`references/*.md` body, a verbose command dump (a full `gh pr view` across several PRs, an unfiltered test run), or a large file read. These are candidate contributors to the baseline `context_multiplication_signal` measures — evidence for *what* is inflating the per-turn cost, which Langfuse alone can't show.

The script only reports which skills **were** invoked (`skills_invoked`) — it has no notion of what skills exist to compare against. To check for a missed trigger, separately enumerate the available skills yourself (see Prerequisites — all three locations) and compare their descriptions/triggers against each user request in the transcript.

**If the report shows no duplicates, no re-edit-reads, and no correction points:** report "No significant friction found in this session" and stop.

**1b. Review each candidate finding manually** — the script flags candidates, it doesn't judge them. For each:
- A duplicate call: was the second call genuinely redundant, or did state change between them (a poll that's supposed to wait, a re-check after a real edit)?
- A re-edit-read: was the re-read needed for accurate context before a second edit to the *same* content, or was it pure re-verification of something already known?
- A correction point: read the surrounding turns — is this a real correction of a wrong action, or just the user adding detail / asking a follow-up?

Drop false positives. Keep only genuine friction.

**1c. Classify each genuine finding:**

| Pattern | Signature | Likely fix side |
|---|---|---|
| Missed skill trigger | User's request matches an installed skill's description/triggers (checked against **all** skill locations from Prerequisites — project, user-global, and plugin-supplied — not just the project's), but no `Skill` tool_use appears before the related work began | Codebase (skill triggers/description) |
| Ignored existing instruction | Assistant action contradicts a rule already present in CLAUDE.md or a loaded skill | Codebase (rule needs to be more prominent/explicit) or one-off slip |
| Redundant re-fetch / re-read | Same lookup repeated with no new information gained | Codebase (reinforce existing "don't re-verify" guidance) |
| Scope drift / compound ask | The user had to correct direction mid-session; the originating request bundled multiple asks or left key constraints unstated | Prompt-side (see Step 3b) |
| Ambiguous or underspecified request | The assistant's first attempt addressed a plausible-but-wrong interpretation, corrected only after the user clarified | Prompt-side |
| Oversized skill footprint | `largest_tool_results` shows a `Skill` invocation's own `SKILL.md`/`references/*.md` body among the biggest payloads in the session, loaded in full regardless of which part of the skill's workflow actually applied to this request | Structural (see Step 3a-structural) — split the skill's reference docs for progressive disclosure |
| Inline exploration that should be delegated | `context_multiplication_signal.message_count` is high (dozens+) with a large, flat `avg_cache_read_per_message`, and the tool histogram shows a long run of `Read`/`Bash`/`Grep`-type calls doing a broad investigative sweep with no `Agent`/`Task`/`Workflow` delegation in between | Structural (see Step 3a-structural) — delegate the sweep to a subagent instead of running it inline in the main thread |

### Step 2: Identify What Actually Caused Friction

For each classified finding, judge impact:

- **Turn/token cost**: did it burn extra tool calls or re-ingest a large output for no new information?
- **User intervention required**: a correction point is the highest-signal finding — the user had to notice and fix it themselves.
- **Recurrence risk**: is this the kind of thing that will happen again on a similar future request, or was it a one-off?

Keep only findings with real impact (a correction, or a pattern with real turn/token cost). A single harmless duplicate isn't worth a policy change or a prompting tip.

### Step 3: Propose Concrete Improvements

**3a. Codebase-side fixes.** For each confirmed finding whose fix side is "codebase," draft ONE specific, testable change:
- A missing skill trigger → propose adding the specific phrase(s) the user actually used to that skill's `triggers` list, or clarifying its `description`
- An ignored instruction → propose making the existing rule more prominent (move it earlier, restate more explicitly) rather than adding a duplicate rule
- Cite the transcript evidence (timestamp, quoted text or tool call) for each proposed change

**3a-structural. Structural / agentification fixes.** For a confirmed "Oversized skill footprint" or "Inline exploration that should be delegated" finding, the fix is a restructuring of the skill or the base repo, not a CLAUDE.md line — draft ONE specific, concrete change:

- **Oversized skill footprint** → propose splitting the skill's `references/` doc(s) so the always-loaded body is an index (which procedure/section applies to which situation) and the full procedure text is only pulled in — via a targeted `Read` with `offset`/`limit`, or a second-tier `references/<procedure>.md` — once the relevant one is identified. Name the exact file(s) and current size (from `largest_tool_results`), and what the split would look like.
- **Inline exploration that should be delegated** → propose the specific phase of the skill's workflow that should spawn a subagent (`Agent`/`Explore`/`dispatch`) instead of running inline, and what that subagent should return (a compact digest, not raw tool output) so the main thread's context doesn't carry the full exploration. Name the skill, the workflow step, and the evidence (`message_count`, `avg_cache_read_per_message`, the run of tool calls in question).

Cite `largest_tool_results`/`context_multiplication_signal` evidence for each. These changes touch a skill's structure (splitting files, rewriting a workflow step to delegate), not a single line — describe the restructuring precisely enough that the user can approve or reject the shape of it, not just wording.

**If a `/cost-audit` run flagged this session or trace as "Context-multiplication"**, that finding is a pointer to root-cause here — this step is where it gets an actual structural fix, since `/cost-audit`'s own Langfuse data can tell you *that* a trace multiplied cost by turn count but not *what* specifically to restructure.

**3b. Prompt-side tips.** For each confirmed finding whose fix side is "prompt," draft a concrete before/after phrasing example — not generic advice like "be more specific." Show:
- The actual request that led to the friction (quoted)
- What was ambiguous, compound, or missing about it
- A rephrased version that would have avoided the detour, and why it works (states the constraint up front, splits a compound ask into steps, names the specific scope)

Example shape:
> **What happened**: "fix the bug" (session at 14:02) led to two wrong-file attempts before the user pointed at the actual file.
> **Why**: no file/component/symptom named — the request was resolvable only by guessing.
> **Try instead**: "fix the null-pointer crash in `PaymentForm.tsx` when the discount code is empty" — names the file and the symptom, so the first search lands in the right place.

**3c. Present the report and gate.** Present the full report (Output Format below) before writing any changes.

**GATE: user must approve each proposed codebase diff individually before it is applied** — this includes structural/agentification changes from 3a-structural, which get the same per-item approval as a CLAUDE.md line edit. Prompt-side tips are informational — no approval gate needed to *state* them, but do not silently rewrite the user's future prompts for them.

**3d. Apply and note follow-up.** Apply only approved codebase diffs. If a pattern seems likely to recur, tell the user it's worth checking on a future `/session-retro` run rather than promising a fixed re-check date.

## Output Format

```markdown
# Session Retro — [session ID or date]

## Summary
- **Active duration**: [X] (wall-clock span: [Y] — only report the wall-clock figure if it differs meaningfully from active time, e.g. a resumed session spanning days; label it explicitly as wall-clock, not "duration")
- **Tool calls**: [N] (main loop) + [N] (subagent, excluded from friction findings below) / **Messages**: [N]
- **Context baseline**: avg [X] cache-read tokens/message across [N] messages (context only — flag as a finding in Step 1c only if it's unusually large/flat *and* paired with a specific `largest_tool_results` or delegable-exploration cause; a high number alone isn't evidence)
- **Genuine friction found**: [N] findings ([N] correction points, [N] redundant patterns, [N] structural)

## Findings

### [pattern name] — [timestamp]
- **Evidence**: [quoted transcript excerpt or tool-call sequence]
- **Fix side**: codebase | prompt
- **Impact**: [turns/tokens wasted, or "required user correction"]

[repeat per finding]

## Proposed Codebase Changes

### 1. [target file: CLAUDE.md / skill name]
> [exact line(s) to add or change]

**Justification**: [timestamp/quote from Findings]

[repeat per proposed diff]

## Structural / Agentification Recommendations

### 1. [target skill] — [oversized skill footprint | inline exploration that should be delegated]
- **Current structure**: [file(s)/size, or the workflow step and its inline call sequence]
- **Proposed change**: [the specific split, or the specific delegation — which step, what the subagent should return]
- **Justification**: [`largest_tool_results` / `context_multiplication_signal` evidence, or the cross-referenced `/cost-audit` trace]

[repeat per recommendation; omit this section entirely if no structural finding survived Step 2]

## Prompt Phrasing Tips

### [finding it addresses]
- **What happened**: [quoted original request + what went wrong]
- **Why**: [what was ambiguous/compound/missing]
- **Try instead**: [rephrased example]

[repeat per tip]

## No Action Needed
- [finding] — reviewed, determined to be normal work, not friction
```

## Rules

### Required
- Every proposed change cites a specific transcript excerpt — no unsupported generalizations
- Manually review every script-flagged candidate (Step 1b) before treating it as a genuine finding — the script surfaces candidates, it does not judge them
- Present the full report and get approval before writing any codebase file
- Give a concrete before/after phrasing example for every prompt-side tip — never generic "be clearer" advice
- State explicitly which script-flagged candidates were reviewed and dismissed as normal work

### Recommended
- Run at the end of a session that felt inefficient, not on a fixed schedule
- Prefer strengthening an existing CLAUDE.md rule over adding a new one when the finding shows a rule was ignored rather than missing
- Cross-reference `/cost-audit` findings when both are available — a session flagged as a cost outlier there is a good candidate for a `/session-retro` deep dive here, and a trace flagged "Context-multiplication" there should land here for the actual structural fix
- Don't propose a structural/agentification change on `context_multiplication_signal` alone — pair it with a concrete `largest_tool_results` entry or an identifiable inline-exploration run before drafting a fix; a high baseline with no clear single contributor is architecture-inherent, not a defect in this skill or session

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| SR-T1 | Positive | "Can we do a retro on this session? It felt like it took forever." | Skill triggers |
| SR-T2 | Positive | "Why did you keep re-reading that file?" | Skill triggers |
| SR-T3 | Positive | "Review this conversation and tell me what went wrong" | Skill triggers |
| SR-T4 | Negative | "Review this PR before I merge it" | Does NOT trigger (-> /review, code review not session behavior) |
| SR-T5 | Negative | "Run the finish workflow" | Does NOT trigger (-> /finish, end-of-session test/validate/commit) |
| SR-T6 | Boundary | "Audit our Langfuse traces for wasted tokens across all sessions" | Does NOT trigger — cross-session/cost-focused, route to `/cost-audit` instead |
| SR-T7 | Positive | "This audit skill cost $16 to run — should it be structured differently?" | Skill triggers; agent checks `largest_tool_results` and `context_multiplication_signal`, and if a genuine cause is found, proposes a Structural / Agentification Recommendation rather than a CLAUDE.md line |
