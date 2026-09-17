# Session Retro — Verification Scenario

## Scenario

A developer just finished a long session where they asked "fix the bug" early on, watched the assistant investigate two unrelated files before they clarified which component and symptom they meant, and later noticed the assistant re-read a file it had just edited. They want to know what to change — in the project's CLAUDE.md/skills, and in how they phrase requests — so it doesn't happen again.

**Invocation:** `/session-retro`

## Expected Outcome

1. The agent runs `references/session_transcript_analyzer.py` against the current session's transcript and gets back: a tool-call histogram, one re-edit-read candidate, and a correction point where the user's message contains "no, I meant the checkout component."
2. The agent manually reviews the re-edit-read candidate and determines whether it was necessary (content had changed between the edit and the read) or genuinely redundant — it does not report it as a finding without this check.
3. The agent classifies the correction point as **scope drift / compound ask** (fix side: prompt) because the originating request ("fix the bug") named neither a file nor a symptom.
4. In "Proposed Codebase Changes," the agent only includes items that map to an actual codebase gap (e.g., if a skill like `/debug` should have triggered on "fix the bug" and didn't, that's a codebase-side trigger fix) — it does not turn the vague-request finding into a CLAUDE.md rule, since that's a prompt-side issue.
5. In "Prompt Phrasing Tips," the agent shows the actual quoted request, explains what was missing (no file or symptom named), and gives a concrete rephrased example naming the component and symptom.
6. The agent presents the full report and asks for approval before writing anything to CLAUDE.md or a skill file.
7. The agent explicitly lists any script-flagged candidate it reviewed and dismissed (e.g., a duplicate `Bash` call that was actually a legitimate re-check after a real state change).

## Key Checkpoints

| # | Checkpoint | What to verify |
|---|-----------|----------------|
| 1 | Agent runs the actual parser, doesn't guess from memory | `references/session_transcript_analyzer.py` is invoked against a real transcript path, not fabricated from the conversation summary |
| 2 | Agent manually reviews script-flagged candidates | Each duplicate/re-read/correction candidate is judged as genuine or a false positive before appearing in "Findings" — the script's output is not reported verbatim as conclusions |
| 3 | Findings correctly separate "codebase" from "prompt" fix side | A vague-request finding produces a prompt-phrasing tip, not a CLAUDE.md rule; a missed-skill-trigger finding produces a codebase diff, not a prompting tip |
| 4 | Prompt tips are concrete, not generic | Each tip in "Prompt Phrasing Tips" quotes the actual original request and gives a specific rephrased example — never "try to be more specific" alone |
| 5 | Approval gate before writing | CLAUDE.md/skill files are not modified until the user approves each proposed diff |
| 6 | Dismissed candidates are shown, not silently dropped | The report's "No Action Needed" section lists what was reviewed and ruled out, so the user can sanity-check the agent's judgment calls |
| 7 | Skill scope stays distinct from `/review` and `/finish` | The agent does not pull in code-quality review or test/commit steps — this skill only covers the assistant's own behavior in the conversation |
| 8 | Correction points are real user text, not synthetic events | None of the reported `correction_points` are `<task-notification>`, `<local-command-stdout>`/`<local-command-caveat>`, `<system-reminder>`, or hook-feedback blocks — the analyzer filters these before they reach `user_turns` |
| 9 | Missed-skill-trigger check covers all skill locations | The agent checked project (`.claude/skills`), user-global (`~/.claude/skills`), and plugin-supplied skills before concluding a trigger was or wasn't missed — not project skills alone |

## Scenario 2: Prompt/context mismatch

A developer asks a two-word follow-up ("fix it") mid-session. The assistant's response to that exact turn re-pays a large accumulated context — a previously-loaded skill's reference body plus several prior tool results still sitting in the cache-read total — even though the prompt itself carried almost no information. The developer wants to know whether that specific turn was disproportionately expensive and, if so, why.

**Invocation:** `/session-retro`

**Expected Outcome:**

1. The agent runs `references/session_transcript_analyzer.py` and the report's `prompt_context_outliers` list contains one entry for the "fix it" turn: `prompt_est_tokens` at or below 300, `turn_context_tokens` at or above 20000, and `ratio` at or above 5.0 (e.g. `prompt_est_tokens: 1`, `turn_context_tokens: 25000`, `ratio: 25000.0`).
2. Per Step 1d, the agent dispatches exactly one subagent for this flagged turn (capped at 3 flagged turns total, so one subagent here), on a cheap/mid-tier model, with the turn's `ts`/`turn_index`/`prompt_excerpt` and the preceding main-loop tool calls in its prompt — not a fresh re-read of the whole transcript.
3. The subagent's diagnosis names a specific contributor (e.g. a `Skill` invocation's `SKILL.md`/`references/*.md` body still counted in cache-read, or a long unrelegated exploration run) and recommends one concrete decoupling action (delegate to a subagent, insert a `/clear` boundary, narrow a search, or split a reference doc).
4. The agent folds this finding and its diagnosis into whichever of the two existing structural categories the diagnosis actually points to ("Oversized skill footprint" or "Inline exploration that should be delegated") in the Structural / Agentification Recommendations section — it does not invent a third category unless the diagnosis genuinely doesn't fit either, in which case it says so explicitly.
5. The report's Structural / Agentification Recommendations entry cites the `prompt_context_outliers` entry (ts, ratio) alongside `largest_tool_results`/`context_multiplication_signal` as justification.

## Key Checkpoints (Scenario 2)

| # | Checkpoint | What to verify |
|---|-----------|----------------|
| 10 | Mismatch is flagged only when all three static thresholds hold | The flagged entry has `prompt_est_tokens <= 300`, `turn_context_tokens >= 20000`, and `ratio >= 5.0` — not just a large context total alone |
| 11 | Exactly one subagent per flagged turn, capped at 3 | The agent does not dispatch more than 3 inference subagents even if more turns are flagged, and dispatches one (not zero, not a bulk combined call) per turn under the cap |
| 12 | Inference subagent runs on a cheap/mid-tier model | The dispatch does not default to the most capable model for this bounded read-and-diagnose task |
| 13 | Diagnosis is folded into an existing structural category, not a new one | The Structural / Agentification Recommendations section labels the finding as "Oversized skill footprint" or "Inline exploration that should be delegated" unless the diagnosis genuinely doesn't fit, which is stated explicitly |

## Anti-patterns

| Anti-pattern | Why it fails |
|-------------|-------------|
| Agent reports every script-flagged duplicate/re-read as a finding without review | The script surfaces candidates, not conclusions; unreviewed output produces false-positive findings and erodes trust in the report |
| Agent turns a vague/compound user request into a CLAUDE.md rule | Misattributes a prompt-side issue to the codebase; the fix belongs in how the user phrases future requests, not in a new rule the assistant must remember |
| Agent gives generic prompting advice ("be more specific next time") | Not actionable; the value of this skill is a concrete before/after example grounded in the actual request that caused friction |
| Agent edits CLAUDE.md or a skill before presenting the report | Removes the user's ability to reject a bad diff |
| Agent conflates this skill with `/review` or `/finish` | Produces an unfocused report that duplicates other skills instead of covering the gap they don't: the assistant's own behavior during the conversation |
