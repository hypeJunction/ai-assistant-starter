---
name: commit
description: Review changes and create a git commit with user confirmation. Use when work is ready to commit, changes need staging, or the user says "commit".
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

## Workflow

### Step 0: Branch Safety

```bash
CURRENT_BRANCH=$(git branch --show-current)
git status --porcelain
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
```

**If on main/master:** Warn and suggest creating a feature branch. **Wait for response.**

### Step 1: Review Changes

```bash
git diff $MAIN...HEAD -- [scope-paths]
git diff -- [scope-paths]
git diff --staged -- [scope-paths]
```

```markdown
## Changes to Commit

**Branch:** `[current branch]`

**Modified:** `path/to/file.ts` — [brief description]
**Added:** `path/to/new.ts` — [purpose]
**Deleted:** `path/to/old.ts` — [reason]

**Stats:** X files changed, +Y insertions, -Z deletions
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
# Secrets detection in changed files
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" [scope-paths]

# Insecure patterns
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|\.exec\(|rejectUnauthorized:\s*false)" [scope-paths]
```

**If secrets detected:** **STOP.** Warn the user. Do NOT proceed to commit.
**If insecure patterns detected:** Flag for review — ask user to confirm these are intentional before proceeding.

Exclude test files and example/documentation files from blocking — flag them as informational only.

### Step 4: Validate (Optional)

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
git add [scope-paths]  # NOT -A unless scope is "all"
git commit -m "[message]"
```

### Step 7: Report

```markdown
**Committed:** `abc1234` — [type](scope): [description]
**Files:** X changed

**Next:** Push? Create PR? Continue working?
```

## Commit Message Format

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

When AI wrote most of the code: `Co-Authored-By: Claude <noreply@anthropic.com>`
