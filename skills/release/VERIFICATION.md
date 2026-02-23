# Release Skill Verification

## Scenario

A developer is ready to release v2.1.0 of their library. There are 8 commits since the last tag (v2.0.0): 3 features, 2 fixes, 2 chores, and 1 that added a dependency with a moderate vulnerability. The project uses npm and has a `package-lock.json` that needs regeneration after the version bump. They invoke `/release --type=minor`.

### Commits Since v2.0.0

| Hash | Type | Description |
|------|------|-------------|
| `a1b2c3d` | feat | Add batch export endpoint |
| `e4f5g6h` | feat | Support CSV format in reports |
| `i7j8k9l` | feat | Add webhook retry configuration |
| `m0n1o2p` | fix | Correct timezone handling in scheduler |
| `q3r4s5t` | fix | Fix memory leak in connection pool |
| `u6v7w8x` | chore | Update CI matrix to Node 20 |
| `y9z0a1b` | chore | Add `xml-parser@3.2.1` dependency (has moderate prototype pollution vuln) |
| `c2d3e4f` | chore | Clean up unused type exports |

### Project State

- **Package manager:** npm (detected from `package-lock.json`)
- **Current version in package.json:** `2.0.0`
- **Latest git tag:** `v2.0.0`
- **Branch:** `main`
- **Working tree:** clean (no uncommitted changes)
- **CHANGELOG.md:** exists with previous entries

## Expected Outcome

Version bumped to 2.1.0 in package.json, package-lock.json regenerated via `npm install`, CHANGELOG.md updated with categorized entries (3 features under Added, 2 fixes under Fixed, 3 chores under Changed), moderate vulnerability in `xml-parser@3.2.1` flagged with handling guidance, validation suite passes, git tag `v2.1.0` created, everything committed with user approval at each gate.

## Key Checkpoints

### Checkpoint 1: Agent detects current version (2.0.0 from package.json)

**Phase:** Phase 1 — Prepare (Step 1.1: Check Release Readiness)

The agent reads `package.json` to find the current version and runs `git describe --tags --abbrev=0` to find the last tag. Both confirm v2.0.0.

**Evidence expected:**
```
## Release Status

| Check | Status |
|-------|--------|
| Branch | `main` |
| Uncommitted changes | None |
| Current version | `2.0.0` |
| Last tag | `v2.0.0` |
| Commits since tag | 8 |
```

### Checkpoint 2: Agent determines release type (minor -> 2.1.0)

**Phase:** Phase 1 — Prepare (Step 1.2-1.3: Gather Changes / Confirm Scope)

The agent uses the `--type=minor` flag to determine the bump type. It does not need to infer from commit analysis since the flag is explicit. The new version is calculated as 2.1.0 (minor bump from 2.0.0).

**Evidence expected:**
```
## Release Confirmation

**Current version:** `2.0.0`
**Requested bump:** `minor` (from --type flag)
**New version:** `2.1.0`
```

### Checkpoint 3: Agent categorizes commits since last tag (3 feat, 2 fix, 2 chore)

**Phase:** Phase 1 — Prepare (Step 1.2: Gather Changes)

The agent runs `git log v2.0.0..HEAD --oneline --no-merges` and categorizes each commit by its conventional commit prefix.

**Evidence expected:**
```
## Changes Since Last Release

### Features
- a1b2c3d Add batch export endpoint
- e4f5g6h Support CSV format in reports
- i7j8k9l Add webhook retry configuration

### Bug Fixes
- m0n1o2p Correct timezone handling in scheduler
- q3r4s5t Fix memory leak in connection pool

### Other
- u6v7w8x Update CI matrix to Node 20
- y9z0a1b Add xml-parser@3.2.1 dependency
- c2d3e4f Clean up unused type exports

**Suggested version bump:** `minor` (features present, no breaking changes)
```

### Checkpoint 4: Agent detects package manager (npm from package-lock.json)

**Phase:** Phase 2 — Version (Step 2.1: Bump Version)

Before running version bump commands, the agent detects the package manager by checking for lockfile presence: `package-lock.json` indicates npm, `pnpm-lock.yaml` indicates pnpm, `yarn.lock` indicates yarn.

**Evidence expected:**
The agent runs `npm version minor --no-git-tag-version` (not hardcoded -- selected based on detection of `package-lock.json`).

### Checkpoint 5: Agent bumps version in package.json

**Phase:** Phase 2 — Version (Step 2.1: Bump Version)

The agent bumps the version from 2.0.0 to 2.1.0 using the detected package manager's version command.

**Evidence expected:**
```bash
npm version minor --no-git-tag-version
# package.json now shows "version": "2.1.0"
```

### Checkpoint 6: Agent regenerates package-lock.json after version bump

**Phase:** Phase 2 — Version (Step 2.2: Regenerate Lockfile)

After the version bump changes package.json, the agent runs `npm install` to regenerate the lockfile so it reflects the new version. This is critical because the lockfile records the package version and will be stale after the bump.

**Evidence expected:**
```bash
npm install
# package-lock.json now reflects version 2.1.0
```

The agent stages both `package.json` and `package-lock.json` for the release commit.

### Checkpoint 7: Agent updates CHANGELOG.md with categorized entries

**Phase:** Phase 2 — Version (Step 2.3: Update Changelog)

The agent updates CHANGELOG.md following the changelog format reference, with sections for Added (3 features), Fixed (2 fixes), and Changed (3 chores).

**Evidence expected:**
```markdown
## [2.1.0] - 2026-02-23

### Added
- Add batch export endpoint (a1b2c3d)
- Support CSV format in reports (e4f5g6h)
- Add webhook retry configuration (i7j8k9l)

### Fixed
- Correct timezone handling in scheduler (m0n1o2p)
- Fix memory leak in connection pool (q3r4s5t)

### Changed
- Update CI matrix to Node 20 (u6v7w8x)
- Add xml-parser@3.2.1 dependency (y9z0a1b)
- Clean up unused type exports (c2d3e4f)
```

### Checkpoint 8: Agent runs validation (typecheck, lint, tests, build)

**Phase:** Phase 3 — Validate (Step 3.1: Run Full Validation)

The agent runs the full validation suite using the detected package manager's run command.

**Evidence expected:**
```
## Validation Results

| Check | Status | Details |
|-------|--------|---------|
| Type check | Pass | No errors |
| Lint | Pass | No warnings |
| Tests | Pass | 147 passed, 0 failed |
| Build | Pass | Built in 4.2s |
```

### Checkpoint 9: Agent detects moderate vulnerability and flags it with guidance

**Phase:** Phase 3 — Validate (Step 3.2: Security Audit)

The agent runs `npm audit` and detects the moderate prototype pollution vulnerability in `xml-parser@3.2.1`. Because it is a moderate (not just high/critical) vulnerability, the agent does not silently ignore it -- it flags it with specific information and options.

**Evidence expected:**
```
## Security Audit

Moderate vulnerability found:

| Package | Severity | Description | Dependency Type |
|---------|----------|-------------|-----------------|
| xml-parser@3.2.1 | Moderate | Prototype pollution via crafted XML input | production |
```

### Checkpoint 10: Agent explicitly handles the moderate vulnerability

**Phase:** Phase 3 — Validate (Step 3.2: Security Audit — moderate handling)

The agent presents the moderate vulnerability with three explicit options and waits for user decision. It does not proceed automatically.

**Evidence expected:**
```
**Moderate vulnerability in production dependency: xml-parser@3.2.1**
- Prototype pollution via crafted XML input

**Options:**
1. **Fix now** — update xml-parser to a patched version (if available)
2. **Document** — add as known issue in release notes and proceed
3. **Abort** — stop the release to investigate and fix first

**How would you like to proceed?** (fix / document / abort)
```

### Checkpoint 11: Agent creates git tag (v2.1.0)

**Phase:** Phase 5 — Tag (Step 5.2: Create Git Tag)

After getting user approval for the release commit, the agent creates an annotated git tag.

**Evidence expected:**
```bash
git tag -a v2.1.0 -m "Release v2.1.0"
```

### Checkpoint 12: Agent presents everything for user approval before committing/tagging

**Phase:** Phase 5 — Tag (Step 5.1: Create Release Commit)

The agent presents all files to be committed, the proposed commit message, and waits for explicit user approval. It does NOT run `git commit` or `git tag` until the user confirms.

**Evidence expected:**
```
## Release Commit

**Files to commit:**
- `package.json` — version bumped to 2.1.0
- `package-lock.json` — regenerated with new version
- `CHANGELOG.md` — added v2.1.0 release entry

**Commit message:** `chore(release): v2.1.0`

**Approve release commit?** (yes / edit / abort)
```

The agent stops here. No `git commit` command is executed until the user responds.

### Checkpoint 13: Scope flags are operationalized

**Phase:** Phase 1 — Prepare (Step 1.3: Confirm Release Scope)

The `--type=minor` flag directly drives the version calculation. If the flag were `--type=patch`, the agent would bump to 2.0.1 instead. If `--type=major`, it would bump to 3.0.0. If no `--type` flag is provided, the agent analyzes commits using conventional commit prefixes to suggest an appropriate type.

**Evidence expected:**
- With `--type=minor`: version becomes 2.1.0
- The flag overrides any commit-based suggestion
- If no flag were provided, the agent would suggest `minor` based on the presence of `feat` commits and absence of `BREAKING CHANGE`

## Anti-Patterns

### 1. Skip package-lock.json regeneration after version bump

**Wrong:** Agent bumps version in package.json but does not run `npm install` to regenerate the lockfile.

The lockfile records the package version. After a version bump, the lockfile is stale and contains the old version. Publishing or installing from this state will produce inconsistencies. The agent must regenerate the lockfile after every version bump.

### 2. Silently ignore the moderate vulnerability

**Wrong:** Agent runs `npm audit --audit-level=high`, sees no high/critical vulnerabilities, and proceeds without mentioning the moderate vulnerability at all.

Moderate vulnerabilities in production dependencies deserve explicit acknowledgment. The agent must flag moderate vulnerabilities, identify whether they affect production or devDependencies, and present options (fix, document, or abort). Only informational/low severity can be passed without flagging.

### 3. Create tag before getting user approval

**Wrong:** Agent runs `git commit` and `git tag` immediately after validation passes, without presenting the release commit for user review.

The release commit is a gate that requires explicit user approval. The agent must present the files, commit message, and tag name, then wait for confirmation before executing any git commands.

### 4. Hardcode npm when project might use a different package manager

**Wrong:** Agent runs `npm version`, `npm install`, `npm run test`, `npm audit` without checking which package manager the project uses.

The agent must detect the package manager from lockfile presence (package-lock.json = npm, pnpm-lock.yaml = pnpm, yarn.lock = yarn) and use the corresponding commands. Hardcoding npm will fail for pnpm/yarn projects.

### 5. Number phases inconsistently

**Wrong:** Phases skip numbers (e.g., Phase 1, Phase 2, Phase 3, Phase 5) or use duplicate numbers, making the workflow confusing to follow.

All phases must be numbered sequentially without gaps or duplicates. If a phase is optional (like Docs), it still gets its own number in the sequence.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No lockfile regeneration | After version bump, package-lock.json (or equivalent) was not regenerated, leaving it stale with the old version | Added Step 2.2 (Regenerate Lockfile): after version bump, run the package manager's install command to update the lockfile, then stage it with the version bump commit |
| Scope flags not operationalized | `--type` flag was documented as a version argument but not explicitly wired into the workflow's decision logic | Added explicit flag handling: `--type` flag drives version calculation directly; if absent, conventional commit analysis suggests the type; flag always overrides suggestion |
| No moderate vulnerability handling | Security audit only checked for high/critical; moderate vulnerabilities were silently ignored | Added moderate vulnerability handling: flag each with package name, severity, and dependency type; present fix/document/abort options; only informational/low severity can pass without flagging |
| Phase numbering inconsistency | Phase numbers had a gap (Phase 4 Docs jumped to Phase 5 Tag, but internally references were inconsistent) | Renumbered all phases sequentially: 1 (Prepare), 2 (Version), 3 (Validate), 4 (Docs), 5 (Tag), 6 (Notes) |
| Package manager hardcoding | Commands used `npm` directly instead of detecting the project's package manager | Added package manager detection from lockfile presence and replaced all hardcoded npm references with detection-based commands |
