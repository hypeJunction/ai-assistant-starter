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

## Anti-patterns

| Anti-pattern | Why it fails |
|-------------|-------------|
| Agent reports every script-flagged duplicate/re-read as a finding without review | The script surfaces candidates, not conclusions; unreviewed output produces false-positive findings and erodes trust in the report |
| Agent turns a vague/compound user request into a CLAUDE.md rule | Misattributes a prompt-side issue to the codebase; the fix belongs in how the user phrases future requests, not in a new rule the assistant must remember |
| Agent gives generic prompting advice ("be more specific next time") | Not actionable; the value of this skill is a concrete before/after example grounded in the actual request that caused friction |
| Agent edits CLAUDE.md or a skill before presenting the report | Removes the user's ability to reject a bad diff |
| Agent conflates this skill with `/review` or `/finish` | Produces an unfocused report that duplicates other skills instead of covering the gap they don't: the assistant's own behavior during the conversation |
