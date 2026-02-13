# Refactor Templates

All markdown output templates for the refactor workflow phases.

---

## Pattern Analysis: Findings (Step 2.2)

```markdown
## Pattern Analysis

**Total Occurrences:** {N} across {M} files

**Pattern Variations:**
| Variation | Count | Example | Notes |
|-----------|-------|---------|-------|
| Standard usage | 15 | `pattern()` | Normal refactor |
| With options | 5 | `pattern({ opt: true })` | Special handling |
| Edge case | 2 | `pattern?.()` | Optional chaining |
```

## Pattern Analysis: Edge Cases (Step 2.3)

```markdown
## Edge Cases to Discuss

| Case | Files Affected | Question |
|------|----------------|----------|
| Conditional usage | `file1.ts` | Transform too? |
| Dynamic reference | `utils.ts` | Handle dynamic lookup? |
| Exported API | `index.ts` | Breaking change? |
| Test mocks | `*.spec.ts` | Update mocks? |
```

---

## Plan Summary (Step 3.1)

```markdown
## Refactor Plan Summary

**What:** {brief description}
**Scope:** {N} files across {directories}
**Risk:** {level}

**Key Changes:**
1. Change A
2. Change B

**Before/After:**
\`\`\`typescript
// Before
oldPattern()

// After
newPattern()
\`\`\`

**Edge Cases:** {N} handled per discussion

---
**Proceed with this refactor?** (yes / modify / cancel)
```

---

## Batch Progress (Step 4.2)

```markdown
## Progress Update

**Batch 1 of {N}:** Files 1-5
- ✓ `file1.ts` - transformed
- ✓ `file2.ts` - transformed

**Validation:** Type check passed

**Next:** Batch 2 (files 6-10)

**Continue with next batch?** (yes / pause / review changes)
```

## Discrepancy Report (Step 4.3)

```markdown
## Found Something Unexpected

**File:** `src/components/Special.ts`
**Expected:** `oldPattern()`
**Found:** `oldPattern.withConfig()`

**Options:**
1. **Skip** - Leave unchanged
2. **Transform** - Apply similar transformation
3. **Manual** - Flag for manual review

**Select approach:** (1 / 2 / 3)
```

---

## Verification Report (Phase 5)

```markdown
## Refactor Complete

**Files Modified:** {N}
**Files Skipped:** {N} (with reasons)

| Check | Status |
|-------|--------|
| Type check | ✓ Pass |
| Lint | ✓ Pass |
| Tests | ✓ Pass ({N} tests) |

**Verify refactor externally:** (confirmed working / issues found / need more testing)
```

---

## Commit Message (Phase 7)

```markdown
## Ready to Commit

**Message:**
\`\`\`
refactor: {title}

{Brief description}
\`\`\`

**Commit?** (yes / edit / cancel)
```
