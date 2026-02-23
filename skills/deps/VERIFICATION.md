# Deps Skill Verification

## Scenario

A developer runs `/deps audit` on a project with:

- 2 high-severity vulnerabilities: one in a direct dependency (`axios@0.21.1` -- prototype pollution), one transitive via `node-fetch@2.6.0` (header leak)
- 3 outdated packages: 1 major (`lodash@3.10.1 -> 4.17.21`), 2 minor/patch (`express@4.18.1 -> 4.18.3`, `zod@3.22.0 -> 3.22.4`)
- 1 deprecated package (`request@2.88.2` -- deprecated in favor of `got` or `node-fetch`)
- Project uses pnpm (has `pnpm-lock.yaml` in root)

### Dependency State

| Package | Current | Latest | Type | Issue |
|---------|---------|--------|------|-------|
| `axios` | 0.21.1 | 1.6.5 | direct | High vulnerability (prototype pollution) |
| `node-fetch` | 2.6.0 | 3.3.2 | transitive | High vulnerability (header leak) |
| `lodash` | 3.10.1 | 4.17.21 | direct | Major version outdated |
| `express` | 4.18.1 | 4.18.3 | direct | Patch version outdated |
| `zod` | 3.22.0 | 3.22.4 | direct | Patch version outdated |
| `request` | 2.88.2 | 2.88.2 | direct | Deprecated -- no further updates |

## Expected Outcome

The agent detects the package manager as pnpm (via `pnpm-lock.yaml`), runs a security audit using `pnpm audit`, presents an audit results table with severity levels, detects the deprecated `request` package and flags it with replacement suggestions (`got` or `node-fetch`), categorizes all updates into batches by risk level (security > patch > minor > major), presents a batch plan for user approval, applies security patches first, runs typecheck after each batch, runs full validation (typecheck, lint, tests, build) after all batches complete, and commits both `package.json` and `pnpm-lock.yaml` together.

## Key Checkpoints

### Checkpoint 1: Package manager detected as pnpm (not hardcoded npm)

**Phase:** Phase 1 -- Audit (Step 1.1)

The agent checks for lock files in the project root and finds `pnpm-lock.yaml`. All subsequent package manager commands use `pnpm` instead of `npm`. The agent does NOT default to `npm` or hardcode any package manager.

**Evidence expected:**
```bash
if [ -f "pnpm-lock.yaml" ]; then PKG_MGR="pnpm"
elif [ -f "yarn.lock" ]; then PKG_MGR="yarn"
else PKG_MGR="npm"; fi
# Result: PKG_MGR="pnpm"
```

All commands from this point forward use `pnpm` (e.g., `pnpm audit`, `pnpm outdated`, `pnpm install`).

### Checkpoint 2: Security audit run with correct command (`pnpm audit`)

**Phase:** Phase 1 -- Audit (Step 1.2)

The agent runs `pnpm audit` (not `npm audit` or `yarn audit`) and captures the output showing the 2 high-severity vulnerabilities in `axios` and `node-fetch`.

**Evidence expected:**
```bash
pnpm audit 2>/dev/null || true
# Output shows:
# axios  0.21.1  High  Prototype Pollution
# node-fetch  2.6.0  High  Header Leak (transitive)
```

### Checkpoint 3: Deprecated package `request` detected and flagged with replacement suggestion

**Phase:** Phase 1 -- Audit (Step 1.3)

The agent runs deprecation checks on installed packages and identifies that `request@2.88.2` is deprecated. The agent flags this in the audit results and suggests modern replacements (`got` or `node-fetch`).

**Evidence expected:**
```bash
npm view request deprecated 2>/dev/null
# Output: "request has been deprecated, see https://github.com/request/request/issues/3142"
```

The audit results include a deprecation section:
```markdown
### Deprecated Packages

| Package | Version | Replacement |
|---------|---------|-------------|
| `request` | 2.88.2 | `got`, `node-fetch`, or `undici` |
```

### Checkpoint 4: Audit results table presented with severity levels

**Phase:** Phase 1 -- Audit (Step 1.4)

The agent presents the full audit results in structured tables following the audit-mode reference template. The presentation includes: a security vulnerabilities table with severity and affected packages, an outdated packages table with current/wanted/latest versions and update type, a deprecated packages section, and a summary.

**Evidence expected:**
```markdown
## Dependency Audit

### Security Vulnerabilities

| Severity | Count | Packages |
|----------|-------|----------|
| High | 2 | axios@0.21.1, node-fetch@2.6.0 (transitive) |

### Outdated Packages

| Package | Current | Wanted | Latest | Type |
|---------|---------|--------|--------|------|
| express | 4.18.1 | 4.18.3 | 4.18.3 | patch |
| zod | 3.22.0 | 3.22.4 | 3.22.4 | patch |
| lodash | 3.10.1 | 3.10.1 | 4.17.21 | **major** |

### Deprecated Packages

| Package | Version | Replacement |
|---------|---------|-------------|
| request | 2.88.2 | got, node-fetch, or undici |

### Summary
- **2** packages with security issues (2 high)
- **3** packages outdated (1 major, 2 patch)
- **1** package deprecated
```

### Checkpoint 5: Updates categorized into batches by risk (security > patch > minor > major)

**Phase:** Phase 2 -- Plan (Step 2.1)

The agent categorizes all updates into batches ordered by risk level. Security patches come first, then patch updates, then minor updates, then major updates. The `axios` vulnerability fix requires a major version bump (`0.21.1 -> 1.6.5`), which is flagged separately with breaking change analysis. The deprecated `request` package is noted but NOT auto-updated (requires manual migration).

**Evidence expected:**
```markdown
## Update Plan

### Batch 1: Security Patches (Critical)
| Package | From | To | Risk | Notes |
|---------|------|----|----- |-------|
| node-fetch | 2.6.0 | 2.6.13 | Low | Transitive -- patch fix available |

### Batch 2: Patch Updates (Low Risk)
| Package | From | To | Risk |
|---------|------|----|------|
| express | 4.18.1 | 4.18.3 | Low |
| zod | 3.22.0 | 3.22.4 | Low |

### Batch 3: Security Fix Requiring Major Version (High Risk)
| Package | From | To | Risk | Breaking Changes |
|---------|------|----|----- |------------------|
| axios | 0.21.1 | 1.6.5 | High | Yes -- API changes |

**Note:** axios vulnerability fix requires major version bump. Breaking change analysis required.

### Deferred: Deprecated Package (Manual Migration)
| Package | Status | Action |
|---------|--------|--------|
| request | Deprecated | Replace with `got` or `node-fetch` (separate task) |

### Not Included: Major Updates (Requires Explicit Approval)
| Package | From | To | Risk |
|---------|------|----|------|
| lodash | 3.10.1 | 4.17.21 | High -- major version bump |
```

### Checkpoint 6: User approval gate before applying updates

**Phase:** Phase 2 -- Plan (Step 2.2)

The agent presents the full update strategy and waits for explicit user approval. The agent does NOT begin applying any updates until the user responds. The approval prompt includes options to approve, modify, or skip batches.

**Evidence expected:**
```markdown
**Proposed approach:**
1. Apply Batch 1 (security patches) -> validate
2. Apply Batch 2 (patch updates) -> validate
3. [If approved] Apply Batch 3 (axios major upgrade) -> validate thoroughly
4. Deferred: request migration (separate task/todo)

**Approve this plan?** (yes / modify / skip batch N)
```

The agent waits. No `pnpm install` command is executed until the user explicitly approves.

### Checkpoint 7: Typecheck run after each batch

**Phase:** Phase 3 -- Update (Step 3.2)

After applying each batch, the agent runs `pnpm run typecheck` (using the detected package manager, not hardcoded `npm run typecheck`). If type errors occur after a batch, the agent presents the errors and options (fix, revert batch, pin version) before proceeding to the next batch.

**Evidence expected:**

After Batch 1:
```bash
pnpm install node-fetch@2.6.13
pnpm run typecheck
# Result: PASS
```

After Batch 2:
```bash
pnpm install express@4.18.3 zod@3.22.4
pnpm run typecheck
# Result: PASS
```

After Batch 3 (if approved):
```bash
pnpm install axios@1.6.5
pnpm run typecheck
# Result: Type errors in src/services/api.ts (axios API changed)
# Agent presents options: fix / revert batch / pin version
```

### Checkpoint 8: Full validation (typecheck, lint, test, build) after all batches

**Phase:** Phase 4 -- Validate (Step 4.1)

After all approved batches are applied, the agent runs full validation using the detected package manager. All four checks must pass before proceeding to commit.

**Evidence expected:**
```bash
pnpm run typecheck
pnpm run lint
pnpm run test
pnpm run build
```

```markdown
## Validation Results

| Check | Status | Details |
|-------|--------|---------|
| Type check | Pass | No errors |
| Lint | Pass | No warnings |
| Tests | Pass | 142 passed, 0 failed |
| Build | Pass | Build successful |
```

All four checks must pass. If any fail, the agent presents options (fix and re-validate, revert packages, create todo) and waits for the user's decision.

### Checkpoint 9: Commit includes both `package.json` AND `pnpm-lock.yaml`

**Phase:** Phase 5 -- Commit (Step 5.2)

The agent stages both `package.json` and the pnpm lock file (`pnpm-lock.yaml`) for the commit. The agent does NOT commit `package.json` without the corresponding lock file, and does NOT hardcode `package-lock.json` when the project uses pnpm.

**Evidence expected:**
```bash
git add package.json pnpm-lock.yaml
git commit -m "chore(deps): update dependencies

Security:
- Fix high vulnerability in node-fetch (header leak)
- Upgrade axios 0.21.1 -> 1.6.5 (prototype pollution fix)

Updates:
- express: 4.18.1 -> 4.18.3
- zod: 3.22.0 -> 3.22.4"
```

The commit message references the correct lock file name and the `git add` command includes `pnpm-lock.yaml` (not `package-lock.json` or `yarn.lock`).

### Checkpoint 10: Nothing-to-do early exit if audit finds no issues

**Phase:** Phase 1 -- Audit (after Step 1.4)

If the audit had found no vulnerabilities, no outdated packages, and no deprecated packages, the agent would report a clean audit and exit without proceeding to Phase 2-5.

**Evidence expected:**
```markdown
## Dependency Audit -- Clean

No vulnerabilities found. All packages up to date. No deprecated packages detected.

No further action needed.
```

The agent stops. No update plan is generated, no packages are installed, no commit is created.

## Anti-Patterns

### 1. Hardcoding `npm` when project uses pnpm

**Wrong:** Agent runs `npm audit`, `npm install`, `npm outdated` even though a `pnpm-lock.yaml` is present in the project root.

This can produce incorrect audit results (npm and pnpm resolve dependencies differently), create a spurious `package-lock.json` alongside the existing `pnpm-lock.yaml`, and install packages using a different resolution strategy than what the project expects. The agent must detect the package manager in Step 1.1 and use it consistently throughout all phases.

### 2. Applying major updates without explicit user approval

**Wrong:** Agent detects that `lodash@3.10.1` is outdated to `4.17.21` and includes it in a batch update without asking. Or agent upgrades `axios@0.21.1 -> 1.6.5` (major version) as a security fix without flagging the breaking changes.

Major version updates can introduce breaking API changes, remove deprecated methods, or change default behaviors. Even when a major update is needed for a security fix (like `axios`), the agent must present the breaking change analysis and get explicit approval before applying.

### 3. Skipping validation between batches

**Wrong:** Agent applies all batches (security patches, patch updates, minor updates) in a single `pnpm install` command, then runs validation once at the end.

If validation fails after applying everything at once, it is impossible to determine which batch caused the failure. Applying batches sequentially with typecheck after each one isolates failures to specific packages and makes rollback straightforward.

### 4. Committing package.json without the lock file

**Wrong:** Agent runs `git add package.json && git commit` without also staging `pnpm-lock.yaml`.

This creates a state where `package.json` specifies version ranges but the lock file still pins old versions, leading to inconsistent installs across environments. Other developers running `pnpm install` would get the old locked versions, defeating the purpose of the update. The lock file must always be committed alongside `package.json`.

### 5. Not detecting deprecated packages

**Wrong:** Agent runs `pnpm audit` and `pnpm outdated` but does not check for deprecated packages. The `request@2.88.2` package appears up-to-date (no newer version exists) and has no security vulnerability, so it passes all checks silently.

Deprecated packages are a supply chain risk -- they receive no further security patches, bug fixes, or maintenance. The agent must proactively check for deprecation status and flag deprecated packages with replacement suggestions, even when there are no version updates available.

## Known Gaps Addressed

| Gap | Description | Resolution |
|-----|-------------|------------|
| No early exit for clean audit | If no vulnerabilities found and all packages up to date, the skill proceeded to Phase 2 (Plan) anyway, asking the user to approve an empty plan | Added early exit after Phase 1: if nothing outdated, no vulnerabilities, and no deprecated packages, report clean audit and exit immediately |
| No deprecated package detection | The supply chain checks (Step 1.3) only verified new packages being added but did not scan existing packages for deprecation status | Added deprecated package detection using `npm view [package-name] deprecated` and a "Deprecated Packages" section in the audit results table |
| No guidance for security fix requiring major version | When a vulnerability fix is only available in a major version (e.g., `axios@0.21.1 -> 1.x`), the skill had no special handling; it could be silently grouped with low-risk security patches | Added security + major version conflict guidance: present separately with breaking change analysis, require explicit user approval even for security-motivated major bumps |
| Scope flags not operationalized | `--dev`, `--prod`, `--dry-run`, and `--package=<name>` were documented as flags in the Actions table but were not referenced in the Phase 1-5 workflow steps | Wired scope flags into Phase 1 (filter outdated/audit output) and Phase 3 (--dry-run skips update/validate/commit); --package filters all phases to specific packages |
| Package manager inconsistency | Step 1.1 detected the package manager as `$PKG_MGR` but Steps 1.2, 3.1, 3.2, 4.1, and 5.2 hardcoded `npm` commands | Replaced hardcoded `npm` with `$PKG_MGR` throughout all steps and added lock file name mapping (pnpm-lock.yaml, yarn.lock, package-lock.json) |
| No acceptance tests | The skill had no acceptance tests to verify trigger matching and boundary conditions | Added acceptance tests table with positive, negative, and boundary test cases |
