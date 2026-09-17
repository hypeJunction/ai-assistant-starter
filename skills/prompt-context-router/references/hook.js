#!/usr/bin/env node

/**
 * Prompt Context Router Hook for Claude Code
 *
 * Classifies each incoming user prompt on two independent axes and, when
 * useful, injects `additionalContext` advising how the assistant should
 * treat it — it never blocks a prompt.
 *
 * Axis 1 — task class: the same mechanical/implementation/debugging/
 * architecture/extreme/abstain taxonomy already used for model-tier
 * routing (see CLAUDE.md's Task Classification table), reapplied here via
 * keyword/structural heuristics.
 *
 * Axis 2 — pivot: does this prompt look like a standalone aside rather than
 * a continuation of the immediately preceding turn? Heuristic only (short
 * length, no shared file/symbol references, no continuation pronouns tied
 * to prior context, explicit aside markers like "quick question" or
 * "unrelated"). False negatives are fine — it only needs to catch clear
 * cases.
 *
 * When a prompt is both a pivot and cheap/self-contained (mechanical or
 * lookup-shaped implementation work), the hook suggests delegating it to a
 * subagent so its exploration/tool calls happen off the main thread. When
 * it's a pivot but debugging/architecture/extreme, the hook flags the pivot
 * but recommends staying in the main thread, since that class of work
 * usually still depends on accumulated context. Continuations get no
 * output at all — stays silent like `cost-guardrail`'s fail-open behavior.
 *
 * A third, independent concern layered on top of task class: whether the
 * prompt warrants Plan Mode. Hooks cannot set `permission_mode` themselves
 * (it's a read-only input field — see code.claude.com/docs/en/hooks), so
 * this can only ever be advisory (`additionalContext` suggesting the
 * assistant call `EnterPlanMode`) except for the single highest-risk class
 * (`extreme`), where the first such prompt in a session is denied outright
 * to force engagement. `abstain`-classified prompts are pointed at the
 * `context-disambiguation` skill instead (ask a clarifying question first);
 * `architecture` and `extreme` are pointed at the `plan` skill's phased
 * workflow, which is what real Plan Mode is meant to run inside. Already
 * being in Plan Mode (`permission_mode === 'plan'`) suppresses all of this.
 *
 * The `extreme` deny is a **one-time-per-session** check, not a per-prompt
 * rule — classification is stateless per prompt, so without a session flag
 * every later continuation of an already-planned, already-approved
 * extreme-scope task would re-match the same keywords and get denied again.
 * A small state file in `os.tmpdir()` keyed by `session_id` (same pattern as
 * `context-circuit-breaker`'s `statePath`) records whether this session has
 * already been nudged once; every prompt after that only gets the advisory
 * `additionalContext`, never another deny.
 *
 * Hook protocol: reads the UserPromptSubmit event from stdin as JSON
 * (`input.prompt`, `input.permission_mode`, `input.session_id`), outputs
 * `hookSpecificOutput` JSON to stdout when there's something worth
 * surfacing, nothing otherwise.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const MECHANICAL_KEYWORDS = [
  'rename', 'bump version', 'look up', 'lookup', 'format', 'typo',
  'git status', 'git log', 'file move', 'move the file', 'what version',
  'quick lookup', 'list the', 'find the file',
];

const DEBUGGING_KEYWORDS = [
  'bug', 'fix', 'race', 'flaky', 'crash', 'broken', 'error', 'exception',
  'stack trace', 'regression', 'failing test', 'traceback', "doesn't work",
  'not working',
];

const ARCHITECTURE_KEYWORDS = [
  'redesign', 'tradeoff', 'trade-off', 'architecture', 'rearchitect',
  'design decision', 'approach should we', 'refactor the whole',
];

const EXTREME_KEYWORDS = [
  'migrate the whole', 'codebase-wide', 'rewrite the entire', 'rfc',
  'platform-scale', 'multi-system migration',
];

const IMPLEMENTATION_KEYWORDS = [
  'implement', 'add a feature', 'add feature', 'write a test', 'add tests',
  'build a component', 'create an api', 'add an endpoint',
];

const ASIDE_MARKERS = [
  'quick question', 'btw', 'by the way', 'unrelated', 'off topic',
  'off-topic', 'separately', 'on another note', 'random question',
  'side question',
];

const CONTINUATION_PRONOUNS = [
  ' it ', ' it.', ' it,', ' it?', ' that ', ' this ', ' these ', ' those ',
  ' the above', ' the same', ' also ', ' additionally', ' as well',
];

const PIVOT_LENGTH_THRESHOLD = 160;

function getInput() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(data));
      } catch {
        resolve(null);
      }
    });
  });
}

function countHits(text, keywords) {
  return keywords.reduce((n, kw) => (text.includes(kw) ? n + 1 : n), 0);
}

function classifyTaskClass(promptLower) {
  const scores = {
    extreme: countHits(promptLower, EXTREME_KEYWORDS) * 3,
    architecture: countHits(promptLower, ARCHITECTURE_KEYWORDS) * 2,
    debugging: countHits(promptLower, DEBUGGING_KEYWORDS) * 2,
    implementation: countHits(promptLower, IMPLEMENTATION_KEYWORDS),
    mechanical: countHits(promptLower, MECHANICAL_KEYWORDS),
  };
  let best = 'abstain';
  let bestScore = 0;
  for (const [cls, score] of Object.entries(scores)) {
    if (score > bestScore) {
      best = cls;
      bestScore = score;
    }
  }
  return bestScore > 0 ? best : 'abstain';
}

function looksLikePivot(prompt, promptLower) {
  if (countHits(promptLower, ASIDE_MARKERS) > 0) return true;
  const hasContinuationPronoun = CONTINUATION_PRONOUNS.some((p) => promptLower.includes(p));
  if (hasContinuationPronoun) return false;
  const hasFileOrSymbolRef = /[.\/][a-zA-Z0-9_-]+\.(ts|tsx|js|jsx|py|go|rs|md|json|yml|yaml)|[a-zA-Z_][a-zA-Z0-9_]*\(\)/.test(prompt);
  if (hasFileOrSymbolRef) return false;
  if (prompt.trim().length <= PIVOT_LENGTH_THRESHOLD) return true;
  return false;
}

function classify(prompt) {
  const promptLower = prompt.toLowerCase();
  return {
    taskClass: classifyTaskClass(promptLower),
    isPivot: looksLikePivot(prompt, promptLower),
  };
}

const CHEAP_CLASSES = new Set(['mechanical', 'implementation']);
const CONTEXT_HEAVY_CLASSES = new Set(['debugging', 'architecture', 'extreme']);

function buildAdditionalContext({ taskClass, isPivot }) {
  if (!isPivot) return null;

  if (CHEAP_CLASSES.has(taskClass)) {
    return (
      `This prompt looks like an unrelated aside (task class: ${taskClass}). ` +
      `Treat it as standalone rather than re-deriving it from the full prior thread, ` +
      `and consider delegating it to the dispatch subagent so its exploration/tool ` +
      `calls happen off the main thread instead of accumulating here.`
    );
  }

  if (CONTEXT_HEAVY_CLASSES.has(taskClass)) {
    return (
      `This prompt looks like a topic pivot, but its task class (${taskClass}) usually ` +
      `still depends on accumulated context. Verify whether it actually depends on the ` +
      `current plan/branch/discussion before treating it as fully standalone.`
    );
  }

  return (
    `This prompt looks like an unrelated aside. Treat it as standalone rather than ` +
    `re-deriving it from the full prior thread.`
  );
}

const PLAN_WORKFLOW_NOTE =
  `this matches the plan skill's phased workflow (explore, design, review, approval).`;

function statePath(sessionId) {
  const safeId = (sessionId || 'unknown').replace(/[^a-zA-Z0-9_-]/g, '_');
  return path.join(os.tmpdir(), `claude-prompt-context-router-${safeId}.json`);
}

function loadState(filePath) {
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    const parsed = JSON.parse(raw);
    return { extremeNudged: !!parsed.extremeNudged };
  } catch {
    return { extremeNudged: false };
  }
}

function saveState(filePath, state) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(state));
  } catch {
    // Best-effort only — a failed write just means the next call re-denies once more.
  }
}

function buildPlanModeGuidance({ taskClass, permissionMode, sessionId, extremeMode }) {
  if (permissionMode === 'plan') return null;

  if (taskClass === 'abstain') {
    return {
      additionalContext:
        `This prompt doesn't clearly match a task class. Before pulling in broad context, ` +
        `consider asking a clarifying question (see the context-disambiguation skill) rather ` +
        `than exploring broadly — only consider Plan Mode if the clarified scope turns out to ` +
        `be architecture-sized.`,
    };
  }

  if (taskClass === 'architecture') {
    return {
      additionalContext:
        `This prompt looks architecture-level (redesign/tradeoff-shaped). Consider calling ` +
        `EnterPlanMode before making changes — ${PLAN_WORKFLOW_NOTE}`,
    };
  }

  if (taskClass === 'extreme') {
    const advisory =
      `This prompt looks like an extreme-scope task (codebase-wide rewrite, multi-system ` +
      `migration). Consider calling EnterPlanMode before making changes — ${PLAN_WORKFLOW_NOTE}`;

    if (extremeMode !== 'enforce') {
      return { additionalContext: advisory };
    }

    const filePath = statePath(sessionId);
    const state = loadState(filePath);
    if (state.extremeNudged) {
      return { additionalContext: advisory };
    }
    saveState(filePath, { extremeNudged: true });
    return {
      permissionDecision: 'deny',
      permissionDecisionReason:
        `This prompt looks like an extreme-scope task (codebase-wide rewrite, multi-system ` +
        `migration). Enter Plan Mode (EnterPlanMode) before proceeding, or resend this prompt ` +
        `to proceed anyway — this is a one-time check per session.`,
    };
  }

  return null;
}

async function main() {
  const input = await getInput();
  const prompt = (input && typeof input.prompt === 'string' && input.prompt) || '';
  if (!prompt.trim()) {
    process.exit(0);
  }

  const result = classify(prompt);
  const pivotContext = buildAdditionalContext(result);

  const permissionMode = (input && typeof input.permission_mode === 'string' && input.permission_mode) || null;
  const sessionId = (input && typeof input.session_id === 'string' && input.session_id) || null;
  const extremeMode = process.env.PROMPT_CONTEXT_ROUTER_EXTREME_MODE || 'enforce';
  const planGuidance = buildPlanModeGuidance({
    taskClass: result.taskClass,
    permissionMode,
    sessionId,
    extremeMode,
  });

  if (planGuidance && planGuidance.permissionDecision === 'deny') {
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        permissionDecision: 'deny',
        permissionDecisionReason: planGuidance.permissionDecisionReason,
      },
    }));
    process.exit(0);
  }

  const contexts = [pivotContext, planGuidance && planGuidance.additionalContext].filter(Boolean);
  if (contexts.length) {
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext: contexts.join('\n\n'),
      },
    }));
  }
  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = {
  classify,
  classifyTaskClass,
  looksLikePivot,
  buildAdditionalContext,
  buildPlanModeGuidance,
  statePath,
  loadState,
  saveState,
};
