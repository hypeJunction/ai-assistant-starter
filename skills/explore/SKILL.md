---
name: explore
description: Understand code without making changes. Read-only exploration of codebase structure, patterns, data flow, and dependencies. Use when asked "how does X work" or to investigate code before planning.
category: process
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

### Cross-Strategy Techniques for Deep Explorations

Deep explorations should combine multiple strategies rather than relying on a single approach:

1. **Find all related files** — Start with grep/glob to discover every file related to the topic across the entire codebase
2. **Read key files fully** — Read complete implementations, not just function signatures or exports
3. **Trace imports to map dependencies** — Follow import statements to build a dependency graph between modules and packages
4. **Follow data flow end-to-end** — Trace data from entry point (e.g., user input, API request) through transformations to storage or output
5. **Check tests for behavior documentation** — Tests often document expected behavior, edge cases, and integration points that code alone does not reveal

### Monorepo Guidance

For monorepo projects (multiple packages/workspaces in one repository):

1. **Search across ALL packages/workspaces** — Do not stop after finding results in one package. A feature often spans multiple packages (e.g., frontend, backend, shared utilities)
2. **Identify cross-package dependencies via imports** — Trace imports that cross package boundaries to understand how packages communicate
3. **Map which packages own which parts of the feature** — Document which layer each package is responsible for (e.g., UI, API, shared types)
4. **Note shared types/utilities used across packages** — Shared packages are dependency hubs; identify what they export and who consumes it

## Context Management

- **Delegate deep explorations.** When exploring a large area (6+ files), delegate to a parallel agent to prevent context exhaustion. The agent reports a summary; the main session stays clean.
- **Set a scope budget.** Before exploring, estimate how many files you'll need. If >10 files, narrow the question or delegate to parallel agents.
- **Stop when answered.** Don't keep reading files after finding the answer. Report what you found.

## Workflow

### Step 1: Parse Scope and Select Strategy

```bash
git branch --show-current
```

Identify: (1) question type from strategy table, (2) depth level, (3) scope from flags or question.

### Step 2: Search for Relevant Files

Start narrow, widen only if needed. Use file search and content search to find entry points before reading full files.

### Step 3: Read and Analyze

**Trace:** Find entry point → follow code path → document transformations and decision points.

**Investigate:** Read implementation → check tests → review git blame → check for TODOs.

**Impact:** Find all imports/references → trace dependents → map blast radius (direct → transitive).

**Search:** File patterns → content keywords → check test files → review package.json.

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

**Deep explorations** use the following expanded template instead:

```markdown
## Deep Exploration: [Topic]

### Architecture Overview
[High-level description of the system/feature — how components relate, what patterns are used]

### Component Map
| File | Package/Module | Role |
|------|----------------|------|
| `path/to/file.ts` | [package] | [what it does] |

### Data Flow
[Numbered steps showing how data moves through the system — from entry point to storage/output, referencing file:line]

### Dependencies
**Internal:** [Cross-module/cross-package imports — which modules depend on which]
**External:** [Third-party libraries used and their role]

### Key Design Decisions
- [Decision — why this approach was chosen, with evidence from code/comments/history]

### Security Implications
- [Security-relevant observations — NOT fixes, just observations]

### Areas for Further Exploration
- [Related topics the developer should investigate next]
```

### Step 5: Indicate Confidence

For each finding, note what was verified vs. inferred:
- **Verified** — Read the code and confirmed
- **Inferred** — Based on naming/patterns but not traced end-to-end
- **Unknown** — Couldn't determine; needs manual verification

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| EXP-T1 | Positive | "How does the auth module work?" | Skill triggers |
| EXP-T2 | Positive | "What would change if I modify the API?" | Skill triggers |
| EXP-T3 | Positive | "Is there existing code for email validation?" | Skill triggers |
| EXP-T4 | Negative | "Fix the auth module" | Does NOT trigger (→ /debug) |
| EXP-T5 | Negative | "Add a new API endpoint" | Does NOT trigger (→ /implement) |
| EXP-T6 | Negative | "Plan the new feature" | Does NOT trigger (→ /plan) |
| EXP-T7 | Boundary | "Investigate and then fix the bug" | Triggers for investigation phase only |
