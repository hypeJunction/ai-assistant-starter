---
name: release
description: Prepare and publish a release with version bump, changelog, and tagging. Use when shipping a new version, creating a release candidate, or tagging a production build.
triggers:
  - ship version
  - release
  - version bump
  - publish
  - tag release
---

# Release

> **Purpose:** Prepare and publish a release with version bump, changelog, and tagging
> **Phases:** Prepare -> Version -> Validate -> Tag -> Notes
> **Usage:** `/release [scope flags] [version]`

## Constraints

- **Never release from non-main branches** without explicit approval
- **Never skip validation phase**
- **Never force push tags**
- **Never release with uncommitted changes**
- **Never push without user confirmation**
- **Semantic versioning (semver) required**
- Full validation (typecheck, lint, test, build) required before release
- User confirmation required at each major gate
- Annotated git tags with version message required
- Update CHANGELOG.md with categorized changes when present
- Create GitHub release with notes when appropriate
- Use conventional commit format for release commit
- Include breaking change migration notes for major releases

> **Note:** Command examples use `npm` as default. Adapt to the project's package manager per `ai-assistant-protocol` — Project Commands.

## Scope Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview changes without committing or tagging |
| `--no-tag` | Skip git tag creation |
| `--no-push` | Create tag locally but don't push |
| `--prerelease=<id>` | Create prerelease (alpha, beta, rc) |

**Version argument:**
- `major` - Breaking changes (1.0.0 -> 2.0.0)
- `minor` - New features (1.0.0 -> 1.1.0)
- `patch` - Bug fixes (1.0.0 -> 1.0.1)
- `X.Y.Z` - Explicit version number

**Examples:**
```bash
/release patch                    # Bug fix release
/release minor                    # Feature release
/release major                    # Breaking change release
/release 2.0.0-beta.1            # Explicit prerelease
/release --dry-run minor         # Preview minor release
/release --prerelease=rc minor   # Release candidate
```

## Workflow

### Phase 1: Prepare

**Goal:** Check release readiness and gather changes

#### Step 1.1: Check Release Readiness

```bash
CURRENT_BRANCH=$(git branch --show-current)
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git status --porcelain
cat package.json | grep '"version"'
git describe --tags --abbrev=0 2>/dev/null || echo "No tags found"
```

Display release status table and warn if not on main branch. See [references/release-display-templates.md](references/release-display-templates.md) for status and warning templates. Wait if on wrong branch.

#### Step 1.2: Gather Changes Since Last Release

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -n "$LAST_TAG" ]; then
  git log ${LAST_TAG}..HEAD --oneline --no-merges
else
  git log --oneline --no-merges -20
fi
```

Categorize changes into Breaking Changes, Features, Bug Fixes, Other. Suggest version bump. See [references/release-display-templates.md](references/release-display-templates.md) for categorization template.

#### Step 1.3: Confirm Release Scope

Present release confirmation with current version, requested bump, new version, and change counts. See [references/release-display-templates.md](references/release-display-templates.md) for confirmation template.

**GATE: Do NOT proceed without explicit approval.**

---

### Phase 2: Version

**Goal:** Bump version and update changelog

#### Step 2.1: Bump Version

```bash
npm version [major|minor|patch] --no-git-tag-version
```

Or manually edit if npm version not appropriate.

#### Step 2.2: Update Changelog

If `CHANGELOG.md` exists, update it. See [references/changelog-format.md](references/changelog-format.md) for the changelog entry format.

If no `CHANGELOG.md` exists, release notes will be generated from commits.

#### Step 2.3: Review Version Changes

```markdown
## Version Changes

**Files modified:**
- `package.json` - version bumped to `X.Y.Z`
- `CHANGELOG.md` - added release entry (if exists)

**Approve version changes?** (yes / edit / abort)
```

**GATE: Do NOT proceed without approval.**

---

### Phase 3: Validate

**Goal:** Full validation before release

#### Step 3.1: Run Full Validation

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

#### Step 3.2: Security Audit

```bash
# Dependency vulnerabilities
npm audit --audit-level=high

# Secrets scan across entire source
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" \
  -E "(api[_-]?key|secret|password|token|credential|private[_-]?key)\s*[:=]" src/

# Insecure patterns
grep -rn --include="*.ts" --include="*.tsx" --include="*.js" \
  -E "(eval\(|new Function\(|innerHTML\s*=|dangerouslySetInnerHTML|rejectUnauthorized:\s*false)" src/
```

**If high/critical vulnerabilities found:** Do NOT release. Fix or document exemption with user approval.
**If secrets or insecure patterns found:** Flag for user review before proceeding.

#### Step 3.3: Report Validation Results

```markdown
## Validation Results

| Check | Status | Details |
|-------|--------|---------|
| Type check | Pass / Fail | [errors if any] |
| Lint | Pass / Fail | [errors if any] |
| Tests | Pass / Fail | X passed, Y failed |
| Build | Pass / Fail | [errors if any] |
| Security audit | Pass / Fail | [vulnerabilities if any] |
| Secrets scan | Pass / Fail | [findings if any] |
```

**If any failures:** Present options (fix and re-run, or abort). Wait for decision.

**GATE: All validations must pass.**

---

### Phase 4: Docs (Optional)

Before creating the release commit, prompt for documentation. See [references/release-display-templates.md](references/release-display-templates.md) for documentation prompt template.

Wait for user response. If `skip`, proceed to tag.

---

### Phase 5: Tag

**Goal:** Create release commit and tag

#### Step 5.1: Create Release Commit

Present files to commit and proposed message. Wait for confirmation.

**STOP HERE. Wait for confirmation.**

```bash
git add package.json package-lock.json CHANGELOG.md
git commit -m "chore(release): vX.Y.Z"
```

#### Step 5.2: Create Git Tag

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

#### Step 5.3: Push Release

**If `--dry-run` flag:** Show what would have happened. See [references/release-display-templates.md](references/release-display-templates.md) for dry run template.

**Otherwise:** Present push confirmation. See [references/release-display-templates.md](references/release-display-templates.md) for push template.

**GATE: Never push without explicit "yes".**

```bash
git push origin main
git push origin vX.Y.Z
```

---

### Phase 6: Notes

**Goal:** Generate release notes and optionally create GitHub release

#### Step 6.1: Generate Release Notes

See [references/release-notes-template.md](references/release-notes-template.md) for the full release notes format.

#### Step 6.2: Create GitHub Release (Optional)

Prompt user: `yes` (create now), `draft` (create as draft), or `skip`. Wait for response.

**If yes or draft:**

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes-file release-notes.md \
  [--draft]
```

---

## Release Complete

Present release summary. See [references/release-display-templates.md](references/release-display-templates.md) for summary template.

## References

- [Release Notes Template](references/release-notes-template.md) -- Full release notes format with highlights, changes, and contributors
- [Changelog Format](references/changelog-format.md) -- CHANGELOG.md entry format for version releases
- [Display Templates](references/release-display-templates.md) -- Status, confirmation, documentation, push, and summary templates
