---
name: communication-guidelines
description: Communication templates and response formatting for AI coding assistants. Defines structured message formats with semantic indicators for status, errors, actions, and progress. Auto-loaded for all interactions.
category: protocol
user-invocable: false
---

# Communication Templates

Predictable, semantically-colored message formats following CLI UX best practices.

> **Emoji handling:** Templates below use emoji indicators by default. When `config.yaml` sets `use_emojis: false`, use plain-text prefixes instead:
>
> | Default | Plain alternative |
> |---------|-------------------|
> | ✅ STATUS | `[STATUS]` |
> | 🔴 ACTION | `[ACTION]` |
> | ⚠️ WARNING | `[WARNING]` |
> | ❌ ERROR | `[ERROR]` |
> | 💡 INFO | `[INFO]` |
> | 📝 INPUT | `[INPUT]` |
> | ⚡ CONFIRM | `[CONFIRM]` |
> | 📋 TASK | `[TASK]` |
> | 💬 NEXT | `[NEXT]` |
> | ✓ / ⠋ / ○ | `[done]` / `[..]` / `[ ]` |

## Quick Reference

```
INFORMATIONAL (no action):     ACTION REQUIRED (must respond):
  ✅ STATUS  - Results           🔴 ACTION  - Decision needed
  💡 INFO    - Context           📝 INPUT   - Info needed
  💬 NEXT    - Follow-up         ⚡ CONFIRM - Yes/no

ATTENTION (read carefully):    PROGRESS (during work):
  ⚠️ WARNING - Caution           ✓ Complete   ⠋ Working
  ❌ ERROR   - Fix suggestion    ○ Pending
```

## Response Structure

```
════════════════════════════════════════════════════════════
📋 TASK: [Brief task description]
════════════════════════════════════════════════════════════

✅ STATUS
────────────────────────────────────────────────────────────
[Results, what changed]
  ✓ Item completed
  ✓ Another item

⚠️ WARNING (if applicable)
────────────────────────────────────────────────────────────
[Risk or caution]

🔴 ACTION REQUIRED (if applicable)
────────────────────────────────────────────────────────────
[Question or decision needed]

  (A) Option one
  (B) Option two

**Select:** (A) or (B)
```

## Section Order

1. 📋 **TASK** — Header identifying current work
2. ✅ **STATUS** / 💡 **INFO** — Results, context
3. ⚠️ **WARNING** — Risks, cautions (non-blocking)
4. ❌ **ERROR** — Failures with cause + fix
5. 🔴 **ACTION** / 📝 **INPUT** / ⚡ **CONFIRM** — User response needed
6. 💬 **NEXT** — Suggested follow-up actions

## Error Pattern

Always: **What failed** → **Why** → **How to fix**

```
❌ ERROR
────────────────────────────────────────────────────────────
Build failed

  What:  Cannot read property 'name' of undefined
  Where: src/components/UserProfile.tsx:45
  Why:   user object is null when component mounts
  Fix:   Add null check: if (user?.name) { ... }
```

## Progress Indicators

```
📋 Running validation
   ✓ Type check passed
   ✓ Lint passed
   ⠋ Running tests...
   ○ Build (pending)
```

## General Style

For general communication principles (conciseness, action-focus, no-summary policy), see `ai-assistant-protocol`. For voice, tone, and human-AI interaction boundary rules, see `interaction-boundaries`.
