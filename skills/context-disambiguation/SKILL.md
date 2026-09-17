---
name: context-disambiguation
description: Ask targeted clarifying questions instead of broad exploration when a prompt is ambiguous and resolving it would pull large amounts of code into context.
category: protocol
user-invocable: false
---

# Context Disambiguation Protocol

Ambiguity is cheap to resolve with a question and expensive to resolve by reading. Default to asking when resolving ambiguity yourself would require pulling a large, uncertain slice of the codebase into context; default to just doing it when one targeted lookup would settle the question.

See also: `prompt-context-router` (background hook) surfaces this same guidance automatically when it can't confidently classify an incoming prompt's task class.

## Why this exists

Most agent failures trace back to bad context, not a bad model — and the biggest avoidable context tax is spent *guessing*: launching an Explore agent "to see what's there," grepping the whole repo, or reading several files speculatively before even knowing what the user meant. The same discipline shows up at the infrastructure level — loading every tool definition up front before it's known which will be used burns a large share of the context budget for near-zero benefit, versus discovering and loading on demand. Apply that logic to exploration: don't front-load a search across the codebase to disambiguate what a one-line question would settle in one turn.

## When to ask instead of explore

Ask via `AskUserQuestion` **before** any exploration when the prompt is ambiguous AND resolving it yourself would require one or more of:

- An unbounded or whole-repo search ("find where X happens", no named file/folder/module)
- Reading more than ~3-5 files, or a directory tree, just to figure out *what the user means* (not to implement the answer)
- Dispatching an Explore/general-purpose subagent whose sole purpose is disambiguation rather than implementation
- Multiple named candidates that plausibly match ("the auth module" when three exist) where picking wrong means redoing the work
- Missing scope for open-ended work ("optimize this", "clean this up") where the acceptable outcome varies wildly by interpretation

Just proceed, no question, when disambiguation costs one cheap targeted action:

- A single grep/glob for a specific, named term
- Reading one file already known to be relevant
- Every plausible reading resolves to the same outcome anyway

## How to ask

- Ground options in what's already cheaply known — file/directory names glimpsed in the request, prior conversation, `git status` — not in an enumeration built by exploring first.
- Prefer 2-4 concrete options over an open-ended "what did you mean?"
- If nothing is known yet, ask the narrower question first: scope (which file/module/directory) before intent (what outcome).

## Interaction with Auto Mode

When the session is in auto mode ("bias toward working without stopping for clarifying questions"), that means *make the reasonable call and proceed*, not *spend context finding out*. Under auto mode:

1. Prefer the narrowest-context interpretation — the one touching the fewest files or least of the codebase.
2. State the assumption made in your response so the user can redirect.
3. Still ask if the interpretations genuinely diverge in blast radius (e.g., "fix this bug" vs. "redesign this system") — auto mode covers picking between similar-cost interpretations, not gambling on scope.

## Relationship to other skills

- `/explore` remains the right tool once scope is known — this protocol only governs the moment *before* scope is known.
- `ai-assistant-protocol`'s "Ask when unclear" step is the general rule; this skill gives the concrete threshold for when unclear-and-costly beats unclear-and-cheap.
