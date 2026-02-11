Special cases for the revert workflow including merge commits, PR reverts, partial reverts, and recovery procedures.

## Special Cases

### Revert a Merge Commit

```bash
# Revert merge commit (specify parent)
git revert -m 1 [merge-sha]  # Keep main branch changes
git revert -m 2 [merge-sha]  # Keep feature branch changes
```

```markdown
> **ACTION REQUIRED:**
> This is a merge commit. Which parent should be the mainline?
>
> - `1` - Keep changes from main branch (revert feature)
> - `2` - Keep changes from feature branch (revert main)
>
> **Usually you want option 1 to revert a merged feature.**
```

### Revert PR Commits

```bash
# Get PR commits
gh pr view [number] --json commits -q '.commits[].oid'

# Revert in reverse chronological order
git revert [newest-sha] [older-sha] [oldest-sha] --no-commit
```

### Partial Revert (Specific Files)

```bash
# Revert specific files from a commit
git checkout [sha]^ -- path/to/file.ts
git add path/to/file.ts
```

## Recovery Options

### Undo a Revert

```bash
# Revert the revert (restores original changes)
git revert [revert-commit-sha]
```

### Abort In-Progress Revert

```bash
# If revert not committed yet
git reset --hard HEAD
```

### View Reverted Content

```bash
# The original commit is still in history
git show [original-sha]

# Cherry-pick to restore specific commits
git cherry-pick [original-sha]
```
