---
name: explore
description: Understand code without making changes. Read-only exploration of codebase structure, patterns, data flow, and dependencies. Use when asked "how does X work" or to investigate code before planning.
triggers:
  - how does X work
  - what would change affect
  - understand code
  - investigate
  - find existing code
  - code architecture
---

# Explore

> **Purpose:** Understand code without making changes
> **Mode:** Read-only — do NOT modify any files
> **Usage:** `/explore [scope flags] <question>`

## Iron Laws

1. **READ-ONLY, NO EXCEPTIONS** — Never edit, create, or delete any file. This skill is purely investigative.
2. **ANSWER THE QUESTION ASKED** — Do not propose fixes, refactors, or improvements unless explicitly asked. Exploration is not a license to redesign.
3. **SCOPE BEFORE SEARCHING** — Define what you're looking for before reading files. Unbounded exploration fills context and degrades performance.

## When to Use

- "How does X work?" — Understand a feature's implementation
- "Why does X behave this way?" — Investigate behavior with history
- "What would be affected if I change X?" — Impact analysis
- "Is there existing code for X?" — Find reusable patterns
- Before `/plan` or `/implement` when the codebase is unfamiliar

## When NOT to Use

- You already know the answer from files in context → just answer
- You need to fix a bug → `/debug`
- You need to make changes → `/implement`
- You need to review code quality → `/review`

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Focus exploration on specific files/directories |
| `--project=<path>` | Project root for monorepos |
| `--depth=<level>` | Exploration depth: `surface`, `standard`, `deep` |

## Exploration Strategies

| Question Type | Strategy | Approach |
|---------------|----------|----------|
| "How does X work?" | **Trace** | Find entry point → follow code path → document the flow |
| "Why does X behave this way?" | **Investigate** | Read implementation → check tests → review git blame/history |
| "What would change X affect?" | **Impact** | Find all references → trace dependents → map blast radius |
| "Is there existing code for X?" | **Search** | Glob for patterns → grep for keywords → check test files for usage |
| "What's the architecture of X?" | **Map** | Find module boundaries → trace data flow → document interfaces |

## Depth Levels

| Level | Scope |
|-------|-------|
| **Surface** | File list + purpose — quick inventory |
| **Standard** | Code flow + patterns + dependencies — full explanation (default) |
| **Deep** | Architecture + history + alternatives + edge cases — comprehensive |

## Context Management

- **Use subagents for deep explorations.** When exploring a large area (6+ files), delegate to a subagent to prevent context exhaustion. The subagent reports a summary; the main session stays clean.
- **Set a scope budget.** Before exploring, estimate how many files you'll need. If >10 files, narrow the question or use subagents.
- **Stop when answered.** Don't keep reading files after finding the answer. Report what you found.

## Workflow

### Step 1: Parse Scope and Select Strategy

```bash
git branch --show-current
```

Identify: (1) question type from strategy table, (2) depth level, (3) scope from flags or question.

### Step 2: Search for Relevant Files

Start narrow, widen only if needed. Use glob/grep to find entry points before reading full files.

### Step 3: Read and Analyze

**Trace:** Find entry point → follow code path → document transformations and decision points.

**Investigate:** Read implementation → check tests → review git blame → check for TODOs.

**Impact:** Find all imports/references → trace dependents → map blast radius (direct → transitive).

**Search:** Glob patterns → grep keywords → check test files → review package.json.

**Map:** Identify module boundaries → trace data flow → document public interfaces → note coupling.

### Step 4: Summarize Findings

Every exploration must include:

```markdown
## Exploration: [Question]

### Key Files
| File | Purpose |
|------|---------|
| `path/to/file.ts` | [what it does] |

### How It Works
[Explanation with numbered steps referencing file:line]

### Patterns Found
- [Pattern — with example location]

### Considerations
- [Things to be aware of for future changes]
```

**Deep explorations** additionally include: Git History, Design Decisions, Edge Cases, and Suggested Next Steps.

### Step 5: Indicate Confidence

For each finding, note what was verified vs. inferred:
- **Verified** — Read the code and confirmed
- **Inferred** — Based on naming/patterns but not traced end-to-end
- **Unknown** — Couldn't determine; needs manual verification
