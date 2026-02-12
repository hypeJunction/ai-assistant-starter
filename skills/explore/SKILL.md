---
name: explore
description: Understand code without making changes. Read-only exploration of codebase structure, patterns, data flow, and dependencies. Use when asked "how does X work" or to investigate code before planning.
---

# Explore

> **Purpose:** Understand code without making changes
> **Mode:** Read-only — do NOT modify any files
> **Usage:** `/explore [scope flags] <question>`

## Iron Laws

1. **READ-ONLY, NO EXCEPTIONS** — Never edit, create, or delete any file. This skill is purely investigative.
2. **ANSWER THE QUESTION ASKED** — Do not propose fixes, refactors, or improvements unless explicitly asked. Exploration is not a license to redesign.

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

## Constraints

- **Read-only** — Use only read, glob, grep operations
- **Never edit files** — Changes must be delegated to implementation skills
- **Never run state-changing commands**

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Focus exploration on specific files/directories |
| `--project=<path>` | Project root for monorepos |
| `--depth=<level>` | Exploration depth: `surface`, `standard`, `deep` |

**Examples:**
```bash
/explore --files=src/auth/ how does login work
/explore --depth=deep how does the state management work
/explore what patterns are used for API calls
```

## Exploration Strategies

Choose your strategy based on the question type:

| Question Type | Strategy | Approach |
|---------------|----------|----------|
| "How does X work?" | **Trace** | Find entry point → follow code path → document the flow |
| "Why does X behave this way?" | **Investigate** | Read implementation → check tests → review git blame/history |
| "What would change X affect?" | **Impact** | Find all references → trace dependents → map blast radius |
| "Is there existing code for X?" | **Search** | Glob for patterns → grep for keywords → check test files for usage |
| "What's the architecture of X?" | **Map** | Find module boundaries → trace data flow → document interfaces |

## Depth Levels

| Level | Scope | Output |
|-------|-------|--------|
| **Surface** | File list + purpose | Quick inventory — names, locations, one-line descriptions |
| **Standard** | Code flow + patterns + dependencies | Full explanation of how things connect and why |
| **Deep** | Architecture + history + alternatives + edge cases | Comprehensive analysis including git history, design decisions, trade-offs |

Default to **Standard** unless the user specifies otherwise or the question is simple enough for Surface.

## Workflow

### Step 1: Parse Scope and Select Strategy

```bash
git branch --show-current
```

Identify:
1. What question type is this? (from the strategy table above)
2. What depth level? (from flags or question complexity)
3. What scope? (from `--files` or inferred from the question)

### Step 2: Search for Relevant Files

Based on the question, search for relevant files:

```bash
# Search for keywords
grep -rn "keyword" src/

# Find files by pattern
find . -name "*.ts" -path "*/auth/*"
```

### Step 3: Read and Analyze

**For Trace strategy:**
1. Find the entry point (route handler, event listener, exported function)
2. Follow the code path step by step
3. Document each transformation and decision point
4. Note where data enters and leaves the system

**For Investigate strategy:**
1. Read the implementation
2. Check test files for intended behavior
3. Review git blame for recent changes
4. Check for related issues or TODOs

**For Impact strategy:**
1. Find all imports/references to the target
2. Trace each dependent to understand coupling
3. Check test coverage for affected areas
4. Map the blast radius (direct dependents → transitive dependents)

**For Search strategy:**
1. Glob for common patterns and naming conventions
2. Grep for keywords and related terms
3. Check test files (they often demonstrate usage patterns)
4. Review package.json for relevant dependencies

**For Map strategy:**
1. Identify module boundaries (directories, index files, barrel exports)
2. Trace data flow between modules
3. Document public interfaces and contracts
4. Note coupling patterns (tight vs loose)

### Step 4: Summarize Findings

Present findings in a structured format appropriate to the depth level.

**Surface output:**
```markdown
## Exploration: [Question]

### Key Files
| File | Purpose |
|------|---------|
| `path/to/file.ts` | [what it does] |
```

**Standard output:**
```markdown
## Exploration: [Question]

### Key Files
| File | Purpose |
|------|---------|
| `path/to/file.ts` | [what it does] |

### How It Works
[Explanation with code flow diagram or numbered steps]

1. Request enters at `path/to/handler.ts:15`
2. Validated by `path/to/validator.ts:8`
3. Processed in `path/to/service.ts:42`
4. Response returned from `path/to/handler.ts:28`

### Patterns Found
- [Pattern 1 — with example location]
- [Pattern 2 — with example location]

### Dependencies
- **Depends on:** [what this code needs]
- **Depended on by:** [what needs this code]

### Considerations
- [Things to be aware of for future changes]
```

**Deep output:** Includes all of Standard plus:
```markdown
### Git History
- [Recent significant changes with commit refs]
- [Who last modified key files and why]

### Design Decisions
- [Why it's built this way, inferred from code and comments]
- [Alternatives that were considered or could work]

### Edge Cases
- [Known edge cases from tests or comments]
- [Potential issues not covered by tests]

### Suggested Next Steps
- [If planning changes, where to start]
- [What to be careful about]
```

## Output Requirements

Every exploration must include at minimum:
- **Key files involved** — List with purpose and line references
- **How the code works** — Clear explanation with flow, not just a file list
- **Patterns to follow** — Conventions found that should be maintained
- **Considerations** — Things to be aware of for future work
