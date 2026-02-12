---
name: commit
description: Review changes and create a git commit with user confirmation. Use when work is ready to commit, changes need staging, or the user says "commit".
---

# Commit

> **Purpose:** Create a clean, well-documented commit
> **Mode:** Git operations with user confirmation required
> **Usage:** `/commit [scope flags]`

## Constraints

- **Read + git only** — Do not modify source code
- **Never commit without explicit user approval** ("yes", "commit", "lgtm", "go ahead")
- **Never force push** without explicit request
- **Never amend commits you didn't create**
- **Never skip hooks** without explicit request
- **Never commit secrets** (.env, credentials, API keys)

**Invalid approval (do NOT treat as confirmation):**
- Silence, questions, "I see", "okay", "looks fine"

**Rule:** If ANY ambiguity, ask: "Please confirm with 'yes' to commit these changes."

## Scope Flags

| Flag | Description |
|------|-------------|
| `--files=<paths>` | Commit only specified files |
| `--uncommitted` | Commit all uncommitted changes (default) |
| `--staged` | Commit only already-staged files |

**Examples:**
```bash
/commit                           # All uncommitted changes
/commit --files=src/auth/         # Only auth directory
/commit --staged                  # Only staged files
```

## Workflow

### Step 0: Branch Safety + Parse Scope

```bash
CURRENT_BRANCH=$(git branch --show-current)
git status --porcelain
MAIN=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
```

**Branch check:** If `$CURRENT_BRANCH` is `main` or `master`:

```markdown
⚠️ **You are on `[branch]`.** Committing directly to the default branch is discouraged.

Options:
- **branch** — Create a feature branch first (recommended)
- **continue** — Commit directly to `[branch]` (requires explicit confirmation)
```

**STOP HERE if on main/master. Wait for user response.**

Determine scope:
- `--files=<paths>` → filter to specified paths
- `--staged` → only staged files
- `--uncommitted` or default → all uncommitted changes

### Step 1: Review Changes (Within Scope)

```bash
git status [scope-filter]
git diff $MAIN...HEAD -- [scope-paths]
git diff -- [scope-paths]
git diff --staged -- [scope-paths]
```

Show summary:
```markdown
## Changes to Commit

**Scope:** `[scope description]`
**Branch:** `[current branch]`

**Modified:**
- `path/to/file.ts` - [brief description]

**Added:**
- `path/to/new.ts` - [purpose]

**Deleted:**
- `path/to/old.ts` - [reason]

**Stats:** X files changed, +Y insertions, -Z deletions
```

### Step 2: Validate (Optional but Recommended)

```bash
npm run typecheck
npm run lint
npm run test -- [affected]
```

### Step 3: Confirm with User

```markdown
**Ready to commit these changes?**

Suggested commit message:
\`\`\`
[type](scope): [description]

[optional body]
\`\`\`

Options:
- **yes** - Commit with this message
- **edit** - Modify the message
- **review** - Show full diff again
- **cancel** - Abort commit
```

**STOP HERE. Do NOT run `git commit` until user responds with explicit approval.**

### Step 4: Commit (Within Scope)

Only after user confirms:

```bash
# Stage files within scope
git add [scope-paths]  # NOT -A unless scope is "all"

# Create commit
git commit -m "[message]"
```

Scope handling:
- `--files=<paths>` → `git add <paths>`
- `--staged` → skip add, commit staged only
- `--uncommitted` → `git add -A`

### Step 5: Report

```markdown
## Committed

**SHA:** `abc1234`
**Message:** [type](scope): [description]
**Files:** X files changed

---
**Next:** Push? Create PR? Continue working?
```

## Commit Message Format

```
[type](scope): [short description]

[optional longer description]

[optional footer: references, breaking changes]
```

Scope is optional, in kebab-case. Omit for project-wide changes.

### Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructuring (no behavior change) |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `style` | Formatting (no code change) |
| `chore` | Maintenance, dependencies |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |
| `build` | Build system or external dependency changes |

### Subject Line Rules

- Use imperative mood ("add" not "added" or "adds")
- No period at the end
- Max 50 characters (72 for body lines)
- Capitalize first letter
- Reference issues when applicable

### Anti-Generic Messages

NEVER use vague commit messages. These are all **banned**:
- "update code", "fix bug", "changes", "misc", "wip", "stuff", "updates"

Every message must answer: **what** changed and **why**.

### Issue References

| Syntax | Effect |
|--------|--------|
| `Fixes #123` | Closes the issue on merge |
| `Closes #123` | Closes the issue on merge |
| `Refs #123` | Links to the issue without closing |

Place in the commit footer (after blank line).

### AI Attribution

When AI generated the majority of committed code, add a trailer:

```
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Include when:** AI wrote most of the code or made the key decisions.
**Omit when:** User dictated the implementation and AI only transcribed, or changes are trivial (typos, formatting).
