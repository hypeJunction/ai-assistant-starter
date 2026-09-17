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
 * a single ordered rule table (`RULES`) of { class, keyword, weight }
 * entries. Keywords match on word boundaries (not plain substring, so
 * "fix" doesn't match inside "prefix") and a short negation lookback
 * discounts hits preceded by "don't"/"not"/"no need to"/etc. within the
 * last few words.
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
 * A fourth, fully independent concern: context ballast. This is the live
 * counterpart to `/cost-audit`'s `prompt_context_mismatch` and
 * `/session-retro`'s `prompt_context_outliers` — same idea (a short new
 * prompt riding on a disproportionately large paid context), just checked at
 * submit time instead of after the fact. It reads `input.transcript_path`
 * (the session's own local `.jsonl`), tails it for the last main-loop
 * (non-sidechain) assistant message's `usage.cache_read_input_tokens` +
 * `usage.cache_creation_input_tokens` + `usage.input_tokens`, and compares
 * that to this prompt's estimated size (chars/4, no tokenizer available).
 * Same default thresholds as the two audit-side checks (>=20k context
 * tokens, >=5x ratio, prompt itself <=300 est. tokens) so a session flagged
 * live here and one flagged retrospectively there apply the same bar. This
 * can only ever advise (`additionalContext`) — a hook cannot remove tokens
 * already in the context window, only suggest delegating the next step or
 * checkpointing with `/clear`.
 *
 * Hook protocol: reads the UserPromptSubmit event from stdin as JSON
 * (`input.prompt`, `input.permission_mode`, `input.session_id`,
 * `input.transcript_path`), outputs `hookSpecificOutput` JSON to stdout when
 * there's something worth surfacing, nothing otherwise.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const NEGATION_MARKERS = [
  "don't", 'do not', "doesn't need to", 'no need to', 'not', 'without',
  'never mind', 'nevermind', 'skip',
];
const NEGATION_LOOKBACK_WORDS = 4;

// Ordered rule table: one row per keyword, grouped by class. Add or retune a
// rule here — the class weight lives next to the keywords it applies to
// instead of being hardcoded separately in classifyTaskClass.
const RULES = [
  ...[
    'rename', 'bump version', 'look up', 'lookup', 'format', 'typo',
    'git status', 'git log', 'file move', 'move the file', 'what version',
    'quick lookup', 'list the', 'find the file', 'version bump',
    'clean up whitespace', 'reformat',
  ].map((keyword) => ({ class: 'mechanical', keyword, weight: 1 })),

  ...[
    'implement', 'add a feature', 'add feature', 'write a test', 'add tests',
    'build a component', 'create an api', 'add an endpoint', 'add an index',
    'consolidate', 'clean up',
  ].map((keyword) => ({ class: 'implementation', weight: 1, keyword })),

  ...[
    'bug', 'fix', 'race', 'flaky', 'crash', 'broken', 'error', 'exception',
    'stack trace', 'regression', 'failing test', 'traceback', "doesn't work",
    'not working', 'flaky test', 'optimize', 'performance', 'slow query',
    'memory leak',
  ].map((keyword) => ({ class: 'debugging', keyword, weight: 2 })),

  ...[
    'redesign', 'tradeoff', 'trade-off', 'architecture', 'rearchitect',
    'design decision', 'approach should we', 'refactor the whole',
  ].map((keyword) => ({ class: 'architecture', keyword, weight: 2 })),

  ...[
    'migrate the whole', 'codebase-wide', 'rewrite the entire', 'rfc',
    'platform-scale', 'multi-system migration',
  ].map((keyword) => ({ class: 'extreme', keyword, weight: 3 })),
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

// Same defaults as /cost-audit's prompt_context_mismatch and /session-retro's
// prompt_context_outliers, so a session flagged live here and one flagged
// retrospectively there use the same bar.
const CONTEXT_BALLAST_FACTOR = Number(process.env.PROMPT_CONTEXT_ROUTER_BALLAST_FACTOR) || 5.0;
const CONTEXT_BALLAST_MIN_CONTEXT_TOKENS = Number(process.env.PROMPT_CONTEXT_ROUTER_BALLAST_MIN_TOKENS) || 20000;
const CONTEXT_BALLAST_MIN_PROMPT_TOKENS = 300;
// A tail read is enough to find the most recent assistant usage line without
// paying to parse a multi-MB transcript on every single prompt submit.
const TRANSCRIPT_TAIL_BYTES = 262144;

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

function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Single-word keywords get \b word-boundary matching so short entries like
// "fix" don't match inside "prefix"/"suffix". Multi-word phrases keep plain
// substring matching — they're specific enough to not need it.
function findMatches(text, keyword) {
  const isSingleWord = !keyword.includes(' ') && !keyword.includes('-');
  const pattern = isSingleWord
    ? new RegExp(`\\b${escapeRegExp(keyword)}\\b`, 'g')
    : new RegExp(escapeRegExp(keyword), 'g');
  return [...text.matchAll(pattern)].map((m) => m.index);
}

function isNegated(text, matchIndex) {
  const before = text.slice(0, matchIndex);
  const words = before.trim().split(/\s+/).filter(Boolean);
  const window = words.slice(-NEGATION_LOOKBACK_WORDS).join(' ');
  return NEGATION_MARKERS.some((marker) => window.includes(marker));
}

function countHits(text, keyword) {
  return findMatches(text, keyword).filter((idx) => !isNegated(text, idx)).length;
}

function classifyTaskClass(promptLower) {
  const scores = { extreme: 0, architecture: 0, debugging: 0, implementation: 0, mechanical: 0 };
  for (const rule of RULES) {
    scores[rule.class] += countHits(promptLower, rule.keyword) * rule.weight;
  }
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
  if (ASIDE_MARKERS.some((marker) => promptLower.includes(marker))) return true;
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

// Reads only the last `maxBytes` of the transcript file — cheap even on a
// multi-MB session history. The first line of the slice may be a partial
// fragment cut mid-JSON; callers must tolerate/skip a parse failure on it.
function readTranscriptTail(transcriptPath, maxBytes = TRANSCRIPT_TAIL_BYTES) {
  let fd;
  try {
    const size = fs.statSync(transcriptPath).size;
    const start = Math.max(0, size - maxBytes);
    const length = size - start;
    const buffer = Buffer.alloc(length);
    fd = fs.openSync(transcriptPath, 'r');
    fs.readSync(fd, buffer, 0, length, start);
    return buffer.toString('utf8');
  } catch {
    return null;
  } finally {
    if (fd !== undefined) {
      try { fs.closeSync(fd); } catch { /* best-effort close */ }
    }
  }
}

// Walks the tail backward for the most recent main-loop (non-sidechain)
// assistant message's usage, mirroring `_context_tokens()` in
// `cost-audit/references/langfuse_queries.py` and `per_message_context` in
// `session-retro/references/session_transcript_analyzer.py`: fresh input +
// cache read + cache creation, the actual paid-context total for that call.
function lastMainLoopContextTokens(transcriptPath) {
  const tail = readTranscriptTail(transcriptPath);
  if (!tail) return null;
  const lines = tail.split('\n').filter(Boolean);
  for (let i = lines.length - 1; i >= 1; i--) {
    let event;
    try {
      event = JSON.parse(lines[i]);
    } catch {
      continue;
    }
    if (event.type !== 'assistant' || event.isSidechain) continue;
    const usage = event.message && event.message.usage;
    if (!usage) continue;
    const contextTokens =
      (usage.cache_read_input_tokens || 0) +
      (usage.cache_creation_input_tokens || 0) +
      (usage.input_tokens || 0);
    if (contextTokens > 0) return contextTokens;
  }
  return null;
}

function buildContextBallastAdvisory(prompt, transcriptPath) {
  if (!transcriptPath) return null;
  const promptEstTokens = Math.ceil(prompt.trim().length / 4);
  if (promptEstTokens > CONTEXT_BALLAST_MIN_PROMPT_TOKENS) return null;

  const contextTokens = lastMainLoopContextTokens(transcriptPath);
  if (contextTokens === null || contextTokens < CONTEXT_BALLAST_MIN_CONTEXT_TOKENS) return null;

  const ratio = contextTokens / Math.max(promptEstTokens, 1);
  if (ratio < CONTEXT_BALLAST_FACTOR) return null;

  const contextK = Math.round(contextTokens / 1000);
  return (
    `This prompt is short (~${promptEstTokens} est. tokens) but the session is currently ` +
    `carrying ~${contextK}k tokens of accumulated context (cache read/write) — a ~${Math.round(ratio)}x ` +
    `ratio. Before continuing in the main thread, consider whether this step could run in a ` +
    `subagent instead, or whether a /clear checkpoint is due.`
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
  const transcriptPath = (input && typeof input.transcript_path === 'string' && input.transcript_path) || null;
  const extremeMode = process.env.PROMPT_CONTEXT_ROUTER_EXTREME_MODE || 'enforce';
  const planGuidance = buildPlanModeGuidance({
    taskClass: result.taskClass,
    permissionMode,
    sessionId,
    extremeMode,
  });
  const ballastContext = buildContextBallastAdvisory(prompt, transcriptPath);

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

  const contexts = [pivotContext, planGuidance && planGuidance.additionalContext, ballastContext].filter(Boolean);
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
  readTranscriptTail,
  lastMainLoopContextTokens,
  buildContextBallastAdvisory,
};
