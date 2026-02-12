# Iterate PR Templates

## PR Status Summary

```markdown
## PR #[number]: [title]

**URL:** [url]
**State:** [open/draft]
**Review Decision:** [approved/changes_requested/review_required/none]

### CI Status
| Check | Status | Details |
|-------|--------|---------|
| [name] | ✅/❌ | [message] |

### Review Comments
- **[author]** on `[file]:[line]`: [summary]
```

## Categorized Findings

```markdown
## Findings (Iteration [N])

### CI Failures
| Type | Count | Details |
|------|-------|---------|
| Build | X | [error summary] |
| Lint | X | [rules violated] |
| Test | X | [test names] |

### Review Feedback
| # | Severity | File | Comment | Author |
|---|----------|------|---------|--------|
| 1 | P0 🔴 | `file.ts:10` | [summary] | @user |
| 2 | P1 🟠 | `file.ts:25` | [summary] | @user |
| 3 | P2 🟡 | `file.ts:40` | [summary] | @user |
| 4 | P3 🔵 | `file.ts:55` | [summary] | @user |
```

## P3 Selection Menu

```markdown
**P3 items — select which to address:**

1. Rename `getData` → `fetchUserProfile` — `api.ts:12`
2. Add JSDoc to exported function — `utils.ts:45`
3. Prefer `const` over `let` — `handler.ts:8`

Enter: "1,3" | "all" | "skip"
```

## Iteration Result

```markdown
## Iteration [N] Result

**Changes made:**
- ✅ Fixed build error: [description]
- ✅ Fixed lint: [description]
- ✅ Addressed P0: [description]
- ⏭️ Skipped P3: [description] (user chose skip)

**CI after push:** ✅ All passing / ❌ [details]
**Remaining comments:** X unresolved
```

## Final Report

```markdown
## PR Iteration Complete

**PR:** #[number] — [title]
**Iterations:** [count]
**Total fixes:** [count]

### Commits Added
| SHA | Message |
|-----|---------|
| `abc1234` | fix: address PR feedback — [summary] |
| `def5678` | style: address style feedback |

### Final Status
- **CI:** ✅ All checks passing
- **Reviews:** All comments resolved
- **Decision:** Ready for re-review

### Remaining Items (if any)
- [Item that couldn't be auto-fixed — needs manual attention]
```
