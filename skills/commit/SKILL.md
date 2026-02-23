---
name: commit
description: Review changes and create a git commit with user confirmation. Use when work is ready to commit, changes need staging, or the user says "commit".
category: process
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

### Step 1: Review Changes

```bash
git diff $MAIN...HEAD -- [scope-paths]
git diff -- [scope-paths]
git diff --staged -- [scope-paths]
```

**Unstaged changes:** If `git status` shows unstaged changes not related to the current commit, leave them alone. Note them in the review output as "out of scope" so the user is aware, but do NOT stage them. Do NOT run `git add .` or `git add -A`. Only stage files that are part of the intended commit. If the user asks to include additional files, stage them explicitly by name.

```markdown
## Changes to Commit

**Branch:** `[current branch]`

**Modified:** `path/to/file.ts` — [brief description]
**Added:** `path/to/new.ts` — [purpose]
**Deleted:** `path/to/old.ts` — [reason]

**Stats:** X files changed, +Y insertions, -Z deletions

**Out of scope (unstaged):** `path/to/other.ts`, `path/to/another.ts` — not included in this commit
```

### Step 2: Mixed-Concern Check

If changes include different concern types (feature + refactor, or feature + config), flag it:

```markdown
These changes appear to mix concerns:
- **Feature:** [files related to new behavior]
- **Refactor:** [files with structural changes only]

Split into separate commits? (yes / no)
```

### Step 3: Security Scan (Always Runs)

Scan changed files for security issues before committing:

```bash
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

**If secrets detected:** **STOP.** Warn the user with the specific file, line number, and secret type. Do NOT proceed to commit.
**If insecure patterns detected:** Flag for review — ask user to confirm these are intentional before proceeding.

Exclude test files and example/documentation files from blocking — flag them as informational only.

#### Re-Scan After Secret Fix

If a secret is detected and fixed (moved to environment variable, removed, etc.):

1. Re-run the full security scan on staged changes
2. If new issues are found, fix and re-scan
3. Continue until the scan is clean
4. **Maximum 3 iterations** — if secrets persist after 3 fix-and-rescan cycles, stop and escalate to the user with a summary of remaining issues
5. Do NOT proceed to Step 4 until the security scan passes with zero findings

### Step 4: Validate (Optional)

Validation scales by change tier. See `references/pre-commit-verification.md` for tier-specific requirements and evidence freshness rules.

```bash
npm run typecheck
npm run lint
npm run test -- [affected]
```

### Step 5: Confirm

```markdown
**Suggested commit message:**
```
[type](scope): [description]

[optional body]
```

Options: **yes** / **edit** / **review** / **cancel**
```

**GATE: Do NOT run `git commit` until user responds with explicit approval.**

### Step 6: Commit

```bash
git add [scope-paths]  # Stage files explicitly by name — NEVER use -A or .
git commit -m "[message]"
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
- Max 50 characters subject, 72 body
- No period at end
- Every message answers: **what** changed and **why**

### Banned Messages

"update code", "fix bug", "changes", "misc", "wip", "stuff", "updates"

### Issue References

`Fixes #123` / `Closes #123` (closes on merge) — `Refs #123` (links without closing)

### AI Attribution

If configured, add an AI co-author trailer to commits where AI wrote most of the code. Follow the project's `config.yaml` setting for `git.ai_attribution`.

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
