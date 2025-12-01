---
marp: true
theme: default
paginate: true
backgroundColor: #1a1a2e
color: #eaeaea
style: |
  section {
    font-family: 'Inter', sans-serif;
  }
  h1, h2 {
    color: #00d9ff;
  }
  h3 {
    color: #ff6b6b;
  }
  code {
    background: #16213e;
    color: #00d9ff;
  }
  table {
    font-size: 0.75em;
  }
  th {
    background: #16213e;
  }
  strong {
    color: #ff6b6b;
  }
  em {
    color: #ffd93d;
  }
  a {
    color: #00d9ff;
  }
  blockquote {
    border-left: 4px solid #ff6b6b;
    padding-left: 1em;
    font-style: italic;
    color: #b8b8b8;
  }
---

# An Honest Conversation About LLMs in Software Engineering

### And a pragmatic framework for working with them

*Not AI. Large Language Models.*

---

## A Note on Language

Before we begin, a disclaimer:

**"AI" is a misnomer** for what we're discussing.

LLMs represent a small subset of machine learning — they're statistical text predictors, not artificial general intelligence. The term "AI" has been hijacked by marketing, misrepresenting decades of diverse research in robotics, computer vision, reinforcement learning, and beyond.

Let's be precise: we're talking about **Large Language Models**.

---

## My Journey (Probably Yours Too)

I gave LLMs an honest effort over the past year.

There were moments of **genuine awe** — watching it generate code in seconds that would take me hours. It felt like magic.

But those moments were rare.

More often, I found myself in what felt like an **abusive relationship** — convinced it must be my fault for not crafting the perfect prompt, not saying the right things.

---

## The Hype vs. Reality

> "Everyone is preaching how AI is turning mountains for them."

The loudest voices make you feel **inferior** for not making it work.

- Tech companies claim they've replaced half their workforce
- Exuberant investments suggest it's the only way forward
- You feel doomed for obsolescence if you don't adapt

**But everyone is suspiciously quiet about:**
- The upfront time investment
- The constant, exhausting oversight
- The minimal understanding of what actually shipped

---

## The Productivity Paradox

### The data tells a different story

| Claim | Reality |
|-------|---------|
| "Developers feel 24% faster" | Actually **19% slower** (METR study) |
| "75% of engineers use AI tools" | **No measurable performance gains** |
| "AI accelerates delivery" | PR review times **+91%**, bugs **+9%** |
| "Faster code generation" | **72% of orgs** had AI-caused production incidents |

*Source: [Faros AI Research](https://www.faros.ai/blog/ai-software-engineering), [METR Study](https://www.cerbos.dev/blog/productivity-paradox-of-ai-coding-assistants)*

---

## The Verification Burden

> "You're not saving time with AI coding; you're just trading less typing for more time reading and untangling code."

**The hidden costs pile up:**
- 62% spend significant time **fixing AI-generated errors**
- 45% say debugging AI code takes **longer than expected**
- 66% frustrated that solutions are **"almost right, but not quite"**
- AI creates **154% larger PRs** — more code to review

*Source: [Qodo State of AI Code Quality](https://www.qodo.ai/reports/state-of-ai-code-quality/)*

---

## The Trust Problem

### 76% of developers are in the "red zone"

They use AI tools but **don't trust the results**.

**Why?**
- 25% estimate **1 in 5 suggestions** contain errors
- Up to **42% of code snippets** contain hallucinations
- AI invents **phantom functions** and **nonexistent APIs**
- It does all this **confidently**, with a straight face

> "AI doesn't just make mistakes—it makes them confidently."
> — Wilson, Exabeam

*Source: [InfoWorld](https://www.infoworld.com/article/3844363/why-ai-generated-code-isnt-good-enough-and-how-it-will-get-better.html)*

---

## Security: The Elephant in the Room

AI-generated code introduces:

- **322% more** privilege escalation paths
- **153% more** design flaws
- **40% increase** in secrets exposure
- Hard-coded credentials and API keys

Previous studies: **40% of GPT-generated code contained vulnerabilities**

The model learned from the internet — including all the bad code.

*Source: [Trend Micro](https://www.trendmicro.com/vinfo/us/security/news/vulnerabilities-and-exploits/the-mirage-of-ai-programming-hallucinations-and-code-integrity)*

---

## The Context Blindness

### Every conversation starts from zero

- Developers must **restate context repeatedly**
- 38% feel "context-blind" despite using **6+ AI tools**
- LLMs actively **discourage innovation** (push toward legacy patterns)
- Patterns break with **every model update** — no stable foundation

> "A static LLM is not cut out to be a gatekeeper for dynamic ideas and evolving context."

---

## Why Natural Language Fails for Code

We invented programming languages for a reason:

**Ambiguity is the enemy** of software engineering.

| Natural Language | Code |
|-----------------|------|
| Ambiguous | Precise |
| Interpreted | Deterministic |
| Context-dependent | Reproducible |
| Probabilistic | Binary |

*This probabilistic nonsense is not what engineering is about.*

---

## The Cognitive Dissonance

Too many of us are trapped under layers of:

- **Self-doubt** — "It must be my prompts"
- **Peer pressure** — "Everyone else seems fine"
- **Job insecurity** — "I'll be replaced if I don't adapt"
- **Impostor syndrome** — all over again

Not enough developers are taking a **principled stand** and calling out LLMs for what they really are.

---

## The Ethical Elephant

Let's ask uncomfortable questions:

- **Microsoft trained on your open-source code** — now charges you monthly
- Is that an "infrastructure fee" or a **perpetual value extraction**?
- Standard tech giant playbook: **ask for forgiveness later**
- AI has penetrated our lives — as hard to remove as social media

**Where is the warranty?**
Bad prompt → bad output. But what about:
- AI ignoring instructions?
- Going beyond scope?
- Millions of tokens wasted on things no one asked for?

---

## So What Do We Do?

I don't want to discount LLMs entirely.

**The potential is real.** I'm happy to delegate mundane tasks.

But I want to be **pragmatic and honest**.

LLMs work better with:
- Explicit, structured instructions
- Mandatory approval gates
- Role-based constraints
- Persistent context

**The tool needs guardrails. We need to provide them.**

---

## Introducing: AI Assistant Starter

### A pragmatic framework for working with LLMs

Not a silver bullet. Not hype.

A **structured approach** to:
- Reduce the verification burden
- Enforce approval gates before changes
- Maintain persistent project context
- Constrain LLM behavior by role

---

## The Core Philosophy

### Three principles

**1. Human Remains in Control**
Mandatory approval gates. No code changes without explicit consent.

**2. Structure Reduces Chaos**
Workflows, phases, constraints. Less room for hallucination.

**3. Context Must Persist**
Project memory survives sessions. No more re-explaining everything.

---

## Two-Layer Architecture

```
project-root/
├── .ai-assistant/          # 📦 Base Framework (shared)
│   ├── workflows/          #    Structured task flows
│   ├── chatmodes/          #    Role-based constraints
│   ├── domains/            #    Coding guidelines
│   └── tasks/              #    Atomic operations
│
├── .ai-project/            # 🎯 Project Layer (yours)
│   ├── .memory.md          #    Persistent context
│   ├── decisions/          #    Architecture records
│   └── todos/              #    Technical debt
│
└── CLAUDE.md               # Entry point
```

---

## Workflows: Structured Phases

### `/implement` — Not just "write code"

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ 🔍 Explore│───▶│ 📋 Plan  │───▶│ ⏸️ GATE  │
│ (read)   │    │ (design) │    │(approval)│
└──────────┘    └──────────┘    └────┬─────┘
                                     │ ✅ explicit
┌──────────┐    ┌──────────┐    ┌────▼─────┐
│ 💾 Commit│◀───│ 🧪 Test  │◀───│ 👨‍💻 Code  │
└──────────┘    └──────────┘    └──────────┘
```

**Key**: LLM proposes. Human disposes.

---

## Chatmodes: Constrained Roles

### Enforce separation of concerns

| Mode | Purpose | Cannot Do |
|------|---------|-----------|
| 🔍 **Explorer** | Understand code | Write anything |
| 📋 **Planner** | Design approach | Implement code |
| 👨‍💻 **Developer** | Write code | 6+ file changes |
| 🧪 **Tester** | Write tests | Production code |
| ♻️ **Refactorer** | Multi-file | Without tracking |

**Why**: Reduce scope creep. Prevent "creative" tangents.

---

## Mandatory Approval Gates

```typescript
// LLM presents plan, then asks:
"Ready to implement. Do you approve?"

// Valid approvals:
✅ "yes" | "approved" | "proceed" | "lgtm"

// NOT approval — LLM must wait:
❌ silence | "sounds good but..." | questions
```

**No implicit consent. No proceeding without explicit approval.**

---

## Persistent Context

### Because LLMs have no memory

```markdown
<!-- .ai-project/.memory.md -->
# Project: E-commerce Platform

## Architecture
- Next.js frontend, Nest.js backend
- PostgreSQL with Prisma ORM

## Key Decisions
- JWT for auth (see decisions/auth-strategy.md)
- Feature flags via LaunchDarkly

## Patterns
- All API routes under /api/v1
- Zod for validation at boundaries
```

Context survives sessions. Less re-explaining.

---

## Domain Guidelines

### Codify your standards (17 domains)

**Code Quality**
`typescript` • `testing` • `naming` • `error-handling`

**Security**
`security` • `data-validation` • `api`

**Operations**
`git` • `ci-cd` • `logging`

Each domain: rules + examples + extension points.

**LLMs follow documented rules better than verbal instructions.**

---

## Provider Agnostic

### Write once, use anywhere

| Provider | Entry Point |
|----------|-------------|
| Claude Code | `CLAUDE.md` |
| Cursor | `.cursorrules` |
| Windsurf | `.windsurfrules` |
| Copilot | `.github/copilot-instructions.md` |

Same constraints. Same workflows. Any tool.

---

## What This Won't Do

Let's be honest about limitations:

❌ **Won't make LLMs reliable** — they're still probabilistic
❌ **Won't eliminate oversight** — you still review everything
❌ **Won't replace experience** — gut feeling takes years
❌ **Won't fix hallucinations** — just catches them earlier
❌ **Won't work for everything** — some tasks need humans

This is **damage control**, not a cure.

---

## What This Will Do

✅ **Reduce verification burden** — structured output is easier to review
✅ **Prevent scope creep** — constrained roles, explicit gates
✅ **Maintain context** — persistent memory reduces re-explaining
✅ **Enforce standards** — documented rules > verbal prompts
✅ **Enable team consistency** — shared framework, shared patterns

Making LLMs **useful enough** without the **false promise**.

---

## When to Use LLMs

### A pragmatic guide

| Good For | Not Good For |
|----------|--------------|
| Boilerplate code | Novel architecture |
| Test scaffolding | Security-critical code |
| Documentation drafts | Performance optimization |
| Regex patterns | Complex debugging |
| Data transformations | Code you must fully understand |
| Exploration/learning | Production without review |

**Use LLMs as tools, not replacements.**

---

## The Path Forward

I respect my own voice, ideas, and thoughts.

**Thought is delicate** — requires nurture, space, experiences.

LLMs can assist, but they cannot:
- Develop your gut feeling
- Understand your context deeply
- Take responsibility for the code
- Evolve with your perception

**The craft of software engineering remains human.**

---

## Getting Started

```bash
# Add to your project
git submodule add \
  git@github.com:hypeJunction/ai-assistant-starter.git \
  .ai-assistant

# Create entry point
echo 'Read: .ai-assistant/.instructions.md' > CLAUDE.md

# Initialize project layer
/init
```

---

## Key Takeaways

1. **Be skeptical of the hype** — data shows minimal productivity gains
2. **LLMs need guardrails** — structure > verbal prompts
3. **Human oversight is non-negotiable** — approval gates are essential
4. **Context must persist** — project memory reduces chaos
5. **Know when NOT to use them** — some tasks need human craft

**Pragmatism over hype. Honesty over marketing.**

---

# Questions?

### Repository

github.com/hypeJunction/ai-assistant-starter

---

## Sources

- [Faros AI: The AI Productivity Paradox](https://www.faros.ai/blog/ai-software-engineering)
- [Qodo: State of AI Code Quality 2025](https://www.qodo.ai/reports/state-of-ai-code-quality/)
- [Cerbos: Productivity Paradox of AI Coding Assistants](https://www.cerbos.dev/blog/productivity-paradox-of-ai-coding-assistants)
- [InfoWorld: Why AI-generated code isn't good enough](https://www.infoworld.com/article/3844363/why-ai-generated-code-isnt-good-enough-and-how-it-will-get-better.html)
- [Trend Micro: AI Programming Hallucinations](https://www.trendmicro.com/vinfo/us/security/news/vulnerabilities-and-exploits/the-mirage-of-ai-programming-hallucinations-and-code-integrity)
- [LogRocket: AI coding tools and context](https://blog.logrocket.com/fixing-ai-context-problem/)
- [Pragmatic Engineer: Software engineering with LLMs in 2025](https://newsletter.pragmaticengineer.com/p/software-engineering-with-llms-in-2025)
