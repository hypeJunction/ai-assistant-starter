---
marp: true
theme: uncover
paginate: true
class: invert
backgroundColor: #050007
color: #ffffff
style: |
  section {
    font-family: 'Inter', -apple-system, sans-serif;
    padding: 60px 80px;
  }
  h1 {
    color: #4D74FF;
    font-size: 2.8em;
    font-weight: 700;
  }
  h2 {
    color: #4D74FF;
    font-size: 2.2em;
    font-weight: 600;
  }
  h3 {
    color: #FF5128;
    font-size: 1.4em;
    font-weight: 500;
  }
  p, li {
    font-size: 1.3em;
    line-height: 1.8;
  }
  strong {
    color: #FF5128;
  }
  em {
    color: #4D74FF;
  }
  ul {
    list-style: none;
    padding-left: 0;
  }
  ul li {
    margin: 0.5em 0;
  }
  ul li::before {
    content: "→ ";
    color: #4D74FF;
  }
  code {
    background: #1a1a2e;
    padding: 0.2em 0.4em;
    border-radius: 4px;
    font-size: 0.9em;
  }
  pre {
    background: #1a1a2e;
    padding: 1em;
    border-radius: 8px;
    border-left: 4px solid #4D74FF;
  }
  pre code {
    background: transparent;
    padding: 0;
  }
  blockquote {
    border-left: 4px solid #FF5128;
    padding-left: 1em;
    font-style: italic;
    color: #e0e0e0;
  }
---

# AI Assistant Starter

### Agentic primitives for controlled AI-assisted development

```
github.com/hypeJunction/ai-assistant-starter
```

---

## The Reality

### METR Study, 2024

```
Measured productivity    Perceived productivity

      ████████████             ████████████████████
      -19%                     +20%
```

*Developers felt faster but were actually slower*

---

## Hidden Costs

```
Where the time actually goes:

██████████████████████████████████  62%  Fixing AI errors
████████████████████                43%  Longer code reviews
████████████████                    38%  Larger PR sizes
```

---

## The Trust Problem

```
┌──────────────────────────────────────────┐
│  78% of developers use AI tools          │
│  but only 32% trust the output           │
└──────────────────────────────────────────┘

        42% of AI code contains
        hallucinated APIs or functions
```

*Productivity tool or liability?*

---

## The Language Problem

### Natural language is ambiguous. Code is not.

```
You say:          AI hears:

"Make it faster"  → Which part? By how much?
"Clean this up"   → Refactor? Delete? Rename?
"Add tests"       → Unit? Integration? E2E?
```

*Probability cannot produce precision*

---

## What This Does

```
Reusable agentic primitives for the software lifecycle

├── Workflows with approval gates
├── Role constraints for unambiguous scope
├── Persistent context across sessions
└── Course correction at every phase
```

---

## Three Core Principles

```
1. Human remains in control
   └── Explicit approval gates

2. Unambiguous scope
   └── Defined phases and roles

3. Context must persist
   └── Memory survives sessions
```

---

## Two Layers

```
.ai-assistant/          .ai-project/
├── workflows/          ├── context.md
├── chatmodes/          ├── domains/
├── domains/            └── decisions/
└── guidelines/
    ↓                       ↓
  Agentic               Your context
  primitives            (gitignored)
```

---

## Atomic Composition

### Small units. Clear scope. Composable.

```
┌─────────────────────────────────────────────┐
│  Task: smallest unit of work                │
│  └── Disambiguated intent                   │
│  └── Project-aware context                  │
│  └── Constrained tool access                │
│                                             │
│  Workflow: composed of tasks                │
│  └── /implement = explore + plan + code     │
└─────────────────────────────────────────────┘
```

*"find" is vague. `grep -r` is precise.*

---

## Software Lifecycle Phases

### Course correction at every gate

```
┌─────────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌────────┐
│ Explore │ → │ Plan │ → │ GATE │ → │ Code │ → │ Commit │
└─────────┘   └──────┘   └──────┘   └──────┘   └────────┘
  read-only    no code    approval   limited    verified
```

*No skipping ahead*

---

## Unambiguous Scope

### Constrained roles prevent overreach

```yaml
Explorer:
  can_read: true
  can_write: false

Planner:
  can_design: true
  can_code: false

Developer:
  files: [src/feature/*.ts]
```

*One chatmode per task. No role confusion.*

---

## Scoped Access

### Limited blast radius per task

```
Task: "Add user validation"

Allowed:
  ✓ src/features/user/*.ts
  ✓ src/utils/validation.ts

Blocked:
  ✗ src/core/*
  ✗ src/config/*
  ✗ Everything else
```

*AI can't refactor what it can't touch*

---

## Course Correction

### Explicit approval enables intervention

```
AI: "Do you approve this plan?"

✓ "yes"
✓ "approved"
✓ "proceed"

✗ "sounds good"
✗ "maybe"
✗ [silence]
```

---

## Persistent Memory

### Context survives across sessions

```markdown
<!-- .ai-project/context.md -->

## Architecture
- API routes: /api/v1/*
- Auth: JWT with refresh tokens
- DB: PostgreSQL with Prisma

## Decisions
- Using React Query for caching
```

---

## Captured Knowledge

### No more tribal knowledge

```
Before:                     After:
┌──────────────────┐        ┌──────────────────┐
│ Alice knows auth │        │                  │
│ Bob knows billing│   →    │  Single source   │
│ Carol left...    │        │  of truth        │
│ "Ask Dave"       │        │                  │
└──────────────────┘        └──────────────────┘
```

*Domain evolution lives in the repo, not in heads*

---

## Fresh Documentation

### Docs always drift. AI keeps them aligned.

```
/sync command:

1. AI scans codebase for changes
2. Compares against context.md
3. Flags stale documentation
4. Proposes updates for approval
```

*Documentation that stays current*

---

## Evolving Instructions

### Regression testing for AI behaviour

```
┌─────────────────────────────────────────────────┐
│  1. AI produces undesired output                │
│  2. Tell AI what went wrong                     │
│  3. AI updates its own instructions             │
│  4. Same mistake won't happen again             │
└─────────────────────────────────────────────────┘
```

*Instructions improve like a test suite*

---

## Positive Prompting

### Tell AI what TO do, not what NOT to do

```
✗ "Don't write verbose code"
✓ "Write concise functions under 20 lines"

✗ "Avoid complex logic"
✓ "Use early returns and guard clauses"

✗ "Don't forget error handling"
✓ "Wrap external calls in try-catch"
```

---

## Template from Your Code

### Point AI to YOUR patterns, not generic ones

```
✗ "Write a React component"
  → Generic patterns from training data

✓ "Follow src/components/Button.tsx"
  → YOUR conventions, YOUR patterns
```

*Don't let AI invent. Let it replicate.*

---

## Enforced SDLC

### No more cutting corners

```
Steps we skip under pressure:

✗ Exploration    → "I know this codebase"
✗ Planning       → "Let's just start coding"
✗ Testing        → "Ship it, we'll fix later"
✗ Documentation  → "The code is self-documenting"
```

*AI in the loop ensures every step happens*

---

## Natural Language Test Plans

### Documentation that becomes implementation

```typescript
/**
 * Test Plan: UserAuth
 *
 * Scenario: Happy path
 *   Given valid credentials
 *   When user submits login
 *   Then JWT token returned
 *
 * Scenario: Account lockout
 *   Given 5 failed attempts
 *   Then account is locked
 */
```

*Readable specs → AI generates actual tests*

---

## Commands as Entry Points

### Clear intent. No missed steps.

```
Freeform:              Structured:
"help me with this"    /implement feature-x
"can you review"       /review
"let's commit"         /commit

     ↓                      ↓
  Ambiguous            Predefined workflow
  Incomplete           All steps included
```

---

## Human-First Workflow

### You write. AI follows up.

```
┌─────────────────────────────────────────┐
│  Human writes mission-critical code     │
│              ↓                          │
│  AI generates tests for it              │
│  AI writes documentation                │
│  AI replicates pattern to similar files │
└─────────────────────────────────────────┘
```

*Focus your expertise. Delegate the rest.*

---

## When to Use LLMs

```
✓ Boilerplate       → Well-defined, verifiable
✓ Test scaffolding  → Patterns are known
✓ Documentation     → Draft, not final
✓ Regex patterns    → Easy to test
```

---

## When NOT to Use

```
✗ Novel architecture  → Needs deep thinking
✗ Security-critical   → Stakes too high
✗ Complex debugging   → Requires intuition
✗ Core business logic → Must fully understand
```

---

## Get Started

```bash
# Add as submodule
git submodule add \
  github.com/hypeJunction/ai-assistant-starter \
  .ai-assistant

# Initialize project layer
/init
```

---

# Questions?

```
github.com/hypeJunction/ai-assistant-starter
```

