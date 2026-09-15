# Search & Relevance Protocol — Rationale

`CLAUDE.md`'s "Search & Relevance Protocol" section exists because Claude has
no dedicated relevance-scoring subsystem for code search:

- **Grep/Glob are mechanical.** They return regex/pattern matches with no
  semantic judgment. Filtering "is this actually relevant" happens only once
  results are back in context, and it happens implicitly — the model judges
  relevance the same way it does everything else, by attention over the
  prompt, not via a specialized ranking model.
- **Noisy retrieval directly taxes the model.** A broad query that returns a
  screenful of matches forces the model to do the triage inline. A narrow
  query does that filtering for free, before the tokens ever arrive.
- **Subagents are the real lever, not a smarter search tool.** Delegating a
  fuzzy/exploratory search to a read-only subagent moves the relevance
  judgment into an isolated context — the subagent reads broadly and returns
  a distilled answer, instead of raw matches landing in the caller's context
  for the caller to re-judge.
- **Tool deferral (`ToolSearch`-style mechanisms) is the closest thing to an
  actual classifier** in most Claude Code setups — a lightweight keyword/
  embedding match against tool descriptions. It's deliberately cheap and
  approximate; don't expect it to replace deliberate query scoping.

Net effect: there's no tunable "relevance" knob to turn. The lever is
reducing what reaches the context window before the model has to judge it —
scope the query, pick the right tool for the query shape, and delegate wide
fishing expeditions instead of paging through them inline.
