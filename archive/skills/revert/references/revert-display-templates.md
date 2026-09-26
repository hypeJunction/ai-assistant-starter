Full markdown display templates for user-facing output in the revert workflow phases.

## Phase 1: Identify

### Commits to Revert (Step 1.2)

```markdown
## Commits to Revert

| # | SHA | Author | Date | Message |
|---|-----|--------|------|---------|
| 1 | abc123 | @user | 2024-01-15 | feat: add feature |
| 2 | def456 | @user | 2024-01-15 | fix: related fix |

**Total:** 2 commits
```

### Changes That Will Be Reverted (Step 1.3)

```markdown
## Changes That Will Be Reverted

**Files affected:** N files

| File | Changes |
|------|---------|
| `src/feature.ts` | +50 / -10 (will be removed) |
| `src/utils.ts` | +5 / -2 (will be removed) |
| `tests/feature.spec.ts` | +30 / -0 (will be removed) |

**Summary:**
- Lines added that will be removed: X
- Lines removed that will be restored: Y
```

### Confirm Revert Target (Step 1.4)

```markdown
## Confirm Revert Target

**You are about to revert:**
- Commit(s): `[sha(s)]`
- Message(s): "[commit message(s)]"
- Files: N files affected

**This will:**
- Remove changes introduced by these commit(s)
- Create new revert commit(s)
- NOT delete history (commits remain in log)

**Proceed with revert?** (yes / show diff / change target / abort)
```

## Phase 2: Assess

### Dependent Changes Warning (Step 2.1)

```markdown
> **WARNING:**
> Found commits that may depend on the target:
>
> | SHA | Message | Risk |
> |-----|---------|------|
> | xyz789 | feat: uses reverted code | High |
>
> **Reverting may cause:**
> - Type errors in dependent code
> - Runtime errors
> - Test failures
>
> **Options:**
> 1. Revert all dependent commits too
> 2. Proceed anyway (will need manual fixes)
> 3. Abort and investigate
>
> **How to proceed?**
```

### Conflict Risk Table (Step 2.2)

```markdown
> **INFO:**
> Files modified since target commit:
>
> | File | Status | Conflict Risk |
> |------|--------|---------------|
> | `src/feature.ts` | Modified | High |
> | `src/utils.ts` | Unchanged | Low |
>
> **Conflicts may require manual resolution.**
```

## Phase 3: Revert

### Conflict Resolution Display (Step 3.2)

```markdown
> **ACTION REQUIRED:**
> Merge conflicts detected in:
>
> | File | Conflict Type |
> |------|---------------|
> | `src/feature.ts` | Content conflict |
>
> **Options:**
> 1. Let me resolve the conflicts
> 2. Show conflict details
> 3. Abort revert
>
> **How to proceed?**
```

### Per-File Conflict Display (Step 3.2)

```markdown
## Conflict in `src/feature.ts`

**Conflict:**
```diff
<<<<<<< HEAD
// Current code (will be kept if we choose "ours")
const newFeature = true;
=======
// Original code (will be restored if we choose "theirs")
>>>>>>> parent of abc123
```

**Resolution options:**
1. Keep current (abort this file's revert)
2. Restore original (apply revert)
3. Manual merge (edit file)

**Choose resolution:**
```
