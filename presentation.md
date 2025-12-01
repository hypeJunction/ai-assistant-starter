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
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
  }
  th {
    background: #4D74FF;
    color: #ffffff;
    padding: 0.5em 1em;
    text-align: left;
  }
  td {
    background: #1a1a2e;
    color: #ffffff;
    padding: 0.5em 1em;
    border-bottom: 1px solid #333;
  }
  .diagram {
    font-family: monospace;
    font-size: 1.1em;
    line-height: 1.4;
  }
  blockquote {
    border-left: 4px solid #FF5128;
    padding-left: 1em;
    font-style: italic;
    color: #e0e0e0;
  }
---

# LLMs in Software Engineering

### An honest conversation

---

## Let's Be Precise

```
"AI" ≠ Artificial General Intelligence

LLMs = Statistical Text Predictors
       └── Subset of Machine Learning
```

*Marketing hijacked the term*

---

## The Year I Tried

- Moments of genuine awe
- Code materialising in seconds
- Felt like magic

---

## But Those Moments Were Rare

```
  My Reality              The Internet
  ───────────            ─────────────
  Bad prompts?      vs   "Built entire app
  What am I doing        in 5 minutes!"
  wrong?
```

---

## The Productivity Paradox

### Feeling faster ≠ Being faster

```
┌─────────────────────────────────┐
│  Perceived:  +24% faster        │
│  Actual:     -19% slower        │
│                      — METR     │
└─────────────────────────────────┘
```

---

## **19% Slower**

When measured objectively

*METR Study*

---

## The Hidden Costs

| Metric | Impact |
|--------|--------|
| Time fixing AI errors | **62%** |
| Pull request size | **+154%** |
| PR review time | **+91%** |

---

## The Trust Problem

```
┌──────────────────────────────┐
│                              │
│   76% use AI tools           │
│                              │
│   But don't trust results    │
│                              │
└──────────────────────────────┘
```

---

## **42%** Hallucinations

```javascript
// AI-generated code
import { validateUser } from 'auth-utils';
//       ^^^^^^^^^^^^
//       This function doesn't exist
```

*Presented confidently*

---

## Security Nightmare

```
Privilege escalation:  +322%  ██████████████████
Secrets exposure:      +40%   ██████
```

*Learned from all the bad code*

---

## Natural Language vs Code

| Natural Language | Code |
|-----------------|------|
| Ambiguous | Precise |
| Probabilistic | Deterministic |

```
"Make it faster" → Which part? How much?
```

---

## The Real Problem

- We blame ourselves
- Assume others figured it out
- Nobody's calling it out

---

## But I Don't Want to Discount LLMs

- The potential is real
- Good for mundane tasks
- **With guardrails**

---

## AI Assistant Starter

### A pragmatic framework

```
github.com/hypeJunction/ai-assistant-starter
```

---

## Three Principles

```
1. Human remains in control
   └── Explicit gatekeeping

2. Structure reduces chaos
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
  Shared                Your context
  primitives            (gitignored)
```

---

## Structured Workflows

```
┌─────────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌────────┐
│ Explore │ → │ Plan │ → │ GATE │ → │ Code │ → │ Commit │
└─────────┘   └──────┘   └──────┘   └──────┘   └────────┘
  read-only    no code    approval   limited    verified
```

*No skipping ahead*

---

## Constrained Roles

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

---

## Explicit Approval

```
AI: "Do you approve this plan?"

✓ "yes"
✓ "approved"
✓ "proceed"

✗ "sounds good"
✗ "maybe"
✗ [silence]
```

*Silence is not consent*

---

## Persistent Memory

```markdown
<!-- .ai-project/context.md -->

## Architecture
- API routes: /api/v1/*
- Auth: JWT with refresh tokens
- DB: PostgreSQL with Prisma

## Decisions
- Using React Query for caching
- Tailwind for styling
```

---

## What This Won't Fix

- LLMs are still probabilistic
- You still review everything
- Experience can't be replaced

---

## What This Will Do

- Reduce verification burden
- Prevent scope creep
- Maintain context

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

## The Craft Remains Human

- Gut feeling
- Deep context
- Accountability

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

## Key Takeaways

- **Be skeptical** of the hype
- **Guardrails** are essential
- **Human oversight** is non-negotiable

---

# Questions?

```
github.com/hypeJunction/ai-assistant-starter
```

