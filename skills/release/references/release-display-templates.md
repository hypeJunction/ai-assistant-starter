# Release Display Templates

## Release Status Display

```markdown
## Release Status

| Check | Status |
|-------|--------|
| Branch | `main` / Not on main |
| Uncommitted changes | None / Has changes |
| Current version | `X.Y.Z` |
| Last tag | `vX.Y.Z` |
| Commits since tag | N |
```

## Wrong Branch Warning

```markdown
> **WARNING:**
> You are on branch `[branch]`, not `main`.
> Releases should typically be made from the main branch.
>
> **Continue anyway?** (yes / switch to main / abort)
```

## Changes Categorization

```markdown
## Changes Since Last Release

### Breaking Changes
- [commit] description

### Features
- [commit] description

### Bug Fixes
- [commit] description

### Other
- [commit] description

**Suggested version bump:** `[patch/minor/major]` based on changes above
```

## Release Confirmation

```markdown
## Release Confirmation

**Current version:** `X.Y.Z`
**Requested bump:** `[patch/minor/major]`
**New version:** `X.Y.Z`

**Changes included:** N commits
- X breaking changes
- Y features
- Z bug fixes

**Proceed with release?** (yes / change version / abort)
```

## Documentation Prompt

```markdown
## Documentation (Optional)

**Release version:** vX.Y.Z

**Consider documenting:**

| Type | When Relevant | Action |
|------|---------------|--------|
| User docs | New features, API changes | Update `docs/` |
| README | Version-specific info, migration notes | Update `README.md` |

**What would you like to document?**
- `user` - Add/update user documentation
- `readme` - Update README (e.g., badge versions, migration notes)
- `skip` - No documentation needed
```

## Dry Run Complete

```markdown
## Dry Run Complete

**Would have:**
- Created commit: `chore(release): vX.Y.Z`
- Created tag: `vX.Y.Z`
- Pushed to origin

**No changes made.** Run without `--dry-run` to execute.
```

## Ready to Push

```markdown
## Ready to Push

**Branch:** `main`
**Commit:** `chore(release): vX.Y.Z`
**Tag:** `vX.Y.Z`

**Push to origin?** (yes / no)

> **WARNING:**
> This will push the release commit and tag to the remote repository.
```

## Release Summary

```markdown
## Release Summary

| Item | Value |
|------|-------|
| Version | `X.Y.Z` |
| Tag | `vX.Y.Z` |
| Commit | `[sha]` |
| GitHub Release | [URL] |

**Release complete!**
```
