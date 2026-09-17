---
name: commit
description: Review changes and create a git commit with user confirmation. Use when work is ready to commit, changes need staging, or the user says "commit".
category: process
model: sonnet
effort: medium
triggers:
  - commit changes
  - save work
  - stage and commit
  - git commit
---

# Commit

> **Purpose:** Create a clean, well-documented commit
> **Mode:** Git operations with user confirmation required
> **Usage:** `/commit [scope flags]`

## Iron Laws

1. **NEVER COMMIT WITHOUT EXPLICIT APPROVAL** — Valid approval per `ai-assistant-protocol`, plus `commit` as a domain-specific term. Silence, questions, "okay" are NOT approval.
2. **NEVER COMMIT SECRETS** — .env, credentials, API keys. Scan before staging.
3. **ONE CONCERN PER COMMIT** — If changes include both a feature and a refactor, suggest splitting into separate commits.

## Constraints

- **Read + git only** — Do not modify source code
- **Never force push** without explicit request
- **Never amend commits you didn't create**
- **Never skip hooks** without explicit request

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Commit only specified files |
| `--uncommitted` | Commit all uncommitted changes (default) |
| `--staged` | Commit only already-staged files |

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Change Tiers

The commit workflow scales based on the size of changes:

| Tier | Scope | Validation | Suggestion |
|------|-------|------------|------------|
| **nano** | 1-2 files, <20 lines | Security scan only | Direct commit |
| **small** | 2-4 files, <100 lines | Security scan + typecheck | Direct commit |
| **medium** | 5-10 files, 100-500 lines | Full validation (Step 4) | Commit, suggest push |
| **large** | 10+ files, 500+ lines | Full validation | Suggest feature branch + PR |

Auto-classify from `git diff --stat`. The user can override ("just commit it").

## Workflow

### Step 0: Branch Safety

```bash
CURRENT_BRANCH=$(git branch --show-current)
git status --porcelain
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
```

**If clean working tree (no staged, unstaged, or untracked changes):** Report "Nothing to commit — working tree is clean" and exit.

**If on main/master:** Warn and suggest creating a feature branch. **Wait for response.**

### Step 1: Delegate Analysis

The diff, mixed-concern classification, and security scan are all read-only and don't require the main session's context — dispatch a single subagent (via the `Agent` tool) to gather all three and return a structured digest, rather than pulling the raw diff into the main agent.

Give the subagent: the scope paths, the commands below, and instructions to return only the digest format — not raw diff text (except for any grep matches from the security scan, which must be quoted in full).

```bash
git diff $MAIN...HEAD -- [scope-paths]
git diff -- [scope-paths]
git diff --staged -- [scope-paths]

# Secrets detection — generic assignment patterns
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" [scope-paths]

# Secrets detection — specific high-confidence patterns
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.env*" \
  -E "(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----|ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{48}|Bearer [a-zA-Z0-9_.\\-]{20,})" [scope-paths]

# Secrets detection — passwords and tokens in strings
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(password|passwd|pwd|token|secret)\s*[:=]\s*[\"'][^\"']{8,}" [scope-paths]

# Insecure patterns
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|\.exec\(|rejectUnauthorized:\s*false)" [scope-paths]
```

**Common secret patterns detected by the scan above:**

| Pattern | Example | Risk |
|---------|---------|------|
| AWS access key | `AKIA...` (20 chars) | Full AWS account access |
| Private key header | `-----BEGIN RSA PRIVATE KEY-----` | TLS/SSH compromise |
| GitHub PAT | `ghp_...` (36 chars) | Repository access |
| OpenAI API key | `sk-...` (48 chars) | API billing abuse |
| Bearer token in code | `Bearer eyJ...` | Auth bypass |
| Password in string | `password = "hunter2"` | Credential leak |

Exclude test files and example/documentation files from blocking — the subagent should flag them as informational only, not as findings.

**Required digest format returned by the subagent:**

```markdown
## Changes to Commit

**Branch:** `[current branch]`

**Modified:** `path/to/file.ts` — [brief description]
**Added:** `path/to/new.ts` — [purpose]
**Deleted:** `path/to/old.ts` — [reason]

**Stats:** X files changed, +Y insertions, -Z deletions

**Out of scope (unstaged):** `path/to/other.ts`, `path/to/another.ts` — not included in this commit

## Mixed-Concern Check
[None detected, or:]
- **Feature:** [files related to new behavior]
- **Refactor:** [files with structural changes only]

## Security Scan
[Clean, or the specific file/line/pattern for each finding, quoted in full]
```

**Unstaged changes:** the subagent must leave unstaged changes alone and never run `git add .` / `git add -A` — it only reads, it does not stage.

### Step 2: Act on the Digest

Read the subagent's digest before proceeding.

**Mixed concerns:** If the digest flags mixed concerns, ask the user via `AskUserQuestion`:

```markdown
These changes appear to mix concerns:
- **Feature:** [files related to new behavior]
- **Refactor:** [files with structural changes only]

Split into separate commits? (yes / no)
```

**Security findings:** **If secrets detected:** **STOP.** Warn the user with the specific file, line number, and secret type. Do NOT proceed to commit.
**If insecure patterns detected:** Flag for review — ask user to confirm these are intentional before proceeding.

**Re-scan after a secret fix:** If a secret is found and fixed (moved to environment variable, removed, etc.), dispatch a fresh Step 1 analysis subagent to re-scan. Continue until the scan is clean. **Maximum 3 iterations** — if secrets persist after 3 fix-and-rescan cycles, stop and escalate to the user with a summary of remaining issues. Do NOT proceed to Step 4 until the security scan passes with zero findings.

### Step 4: Validate (Optional)

Validation scales by change tier. See `references/pre-commit-verification.md` for tier-specific requirements and evidence freshness rules.

**Delegate each check to its own subagent** — typecheck, lint, and scoped test each run via a separate `Agent` call, never directly in the main agent's shell and never bundled into one call. Send independent checks in a single message with multiple tool uses so they run concurrently. Read each subagent's raw output yourself before reporting results. See `ai-assistant-protocol` § Validation Execution.

```bash
npm run typecheck        # subagent 1
npm run lint              # subagent 2
npm run test -- [affected] # subagent 3
```

### Step 5: Confirm

Show the suggested commit message, then use `AskUserQuestion` with options **Yes** (commit as-is), **Edit** (revise the message first), **Review** (show the diff again), **Cancel**.

**GATE: Do NOT run `git commit` until user responds with explicit approval.**

### Step 6: Commit

```bash
git add [scope-paths]  # Stage files explicitly by name — NEVER use -A or .
git commit -m "[message]"       # or: git commit -s -m "[message]" if git.dco_signoff is configured
```

**Staging rule:** Only stage files that are part of the intended commit scope. If there are unstaged changes in other files, they must remain unstaged. Verify with `git status` after staging that no unintended files were included.

### Step 7: Report

```markdown
**Committed:** `abc1234` — [type](scope): [description]
**Files:** X changed

**Next:** Push? Create PR? Continue working?
```

## Commit Message Format

See `references/commit-conventions.md` for extended formats (breaking changes, reverts, multi-issue references, scope conventions, good/bad examples).

```
[type](scope): [short description]

[optional body]

[optional footer: references, breaking changes]
```

### Types

| Type | Use |
|------|-----|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Structure change (no behavior change) |
| `test` | Adding/updating tests |
| `docs` | Documentation |
| `chore` | Maintenance, dependencies |
| `perf` | Performance |

### Rules

- Imperative mood ("add" not "added")
- Lowercase after the type/scope prefix (`feat(auth): add login`, not `feat(auth): Add login`) — matches the lowercase convention used by Angular, Kubernetes, and most Conventional Commits adopters
- Subject line ≤50 characters; wrap body text at 72 characters per line (not "72 characters total")
- No period at end of subject
- Blank line between subject and body
- Every message answers: **what** changed and **why**

### Banned Messages

"update code", "fix bug", "changes", "misc", "wip", "stuff", "updates"

### Issue References

`Fixes #123` / `Closes #123` (closes on merge) — `Refs #123` (links without closing)

If the current branch name encodes a ticket (per `git-conventions` branch naming, e.g. `feature/TICKET-123-payment-integration`), add `Refs TICKET-123` to the footer automatically — don't ask the user each commit. This mirrors `/pr`'s ticket handling but stays lightweight since a branch spans many commits; `/pr` still asks once per branch in case the ticket wasn't encoded in the branch name.

### Commit Trailers

- **AI Attribution:** If configured, add an AI co-author trailer to commits where AI wrote most of the code. Follow the project's `config.yaml` setting for `git.ai_attribution`. Default: do not add one.
- **DCO Sign-off:** If the project requires a Developer Certificate of Origin (the convention used by the Linux kernel, Kubernetes, and many other OSS projects), commit with `git commit -s` to add a `Signed-off-by` trailer. Follow the project's `config.yaml` setting for `git.dco_signoff`; do not add unless configured.

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| CMT-T1 | Positive | "Commit my changes" | Skill triggers |
| CMT-T2 | Positive | "Save my work" | Skill triggers |
| CMT-T3 | Positive | "Stage and commit" | Skill triggers |
| CMT-T4 | Negative | "Push to remote" | Does NOT trigger (git push, not commit) |
| CMT-T5 | Negative | "Create a PR" | Does NOT trigger (→ /pr) |
| CMT-T6 | Negative | "Review my changes" | Does NOT trigger (→ /review) |
| CMT-T7 | Boundary | "Commit and push" | Triggers (commit portion) |
