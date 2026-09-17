---
name: deps
description: Audit, update, and manage project dependencies safely. Use when checking for vulnerabilities, updating outdated packages, or performing routine dependency maintenance.
category: process
model: sonnet
effort: medium
triggers:
  - update dependencies
  - outdated packages
  - vulnerability scan
  - audit deps
---

# Dependencies

> **Purpose:** Audit, update, and manage project dependencies safely
> **Phases:** Audit -> Plan -> Update -> Validate -> Commit
> **Usage:** `/deps [action] [scope flags]`

## Constraints

- **Never update without user approval**
- **Never skip validation after updates**
- **Never commit with failing tests**
- **Never apply major updates without explicit approval**
- **Never ignore security vulnerabilities without acknowledgment**
- Security audit required before updates
- Batch updates by risk level
- Type check after each batch
- Full validation before commit
- User approval required for update plan
- Update security patches immediately when found
- Regular dependency audits recommended (weekly/monthly)
- Document breaking changes from major updates
- Create todos for deferred major updates
- Lock file always committed with package.json

> **Note:** All commands use `$PKG_MGR` which is detected in Step 1.1 (pnpm, yarn, or npm). Lock file variable `$LOCK_FILE` maps to: pnpm-lock.yaml, yarn.lock, or package-lock.json respectively.

## Actions

| Action | Description |
|--------|-------------|
| `audit` | Check for vulnerabilities and outdated packages |
| `update` | Update dependencies (default: patch/minor only) |
| `update --major` | Include major version updates |
| `update --security` | Security patches only |
| `check` | Quick outdated check without updates |

## Scope Flags

| Flag | Description |
|------|-------------|
| `--package=<name>` | Specific package(s) to update |
| `--dev` | Include devDependencies |
| `--prod` | Production dependencies only |
| `--dry-run` | Preview changes without applying |

**Examples:**
```bash
/deps audit                        # Full security audit
/deps update                       # Safe updates (patch/minor)
/deps update --major               # Include breaking updates
/deps update --security            # Security patches only
/deps update --package=lodash      # Update specific package
/deps check                        # Quick outdated check
```

## Workflow

### Phase 1: Audit

**Goal:** Understand current dependency state and risks

#### Step 1.1: Check Current State

```bash
# Get package manager
if [ -f "pnpm-lock.yaml" ]; then PKG_MGR="pnpm"
elif [ -f "yarn.lock" ]; then PKG_MGR="yarn"
else PKG_MGR="npm"; fi

$PKG_MGR outdated 2>/dev/null || true
```

#### Step 1.2: Security Audit

```bash
$PKG_MGR audit 2>/dev/null || true
```

#### Step 1.3: Supply Chain Checks

For any new dependencies being added, verify:

1. **Package legitimacy** — Check for typosquatting (e.g., `lodahs` instead of `lodash`)
2. **Maintenance status** — Is the package actively maintained? Check last publish date
3. **Download count** — Very low downloads on a common-sounding name is a red flag
4. **Install scripts** — Check for `preinstall`/`postinstall` scripts that execute arbitrary code
5. **Deprecation status** — Check if any installed packages are deprecated

```bash
# Check for install scripts in new packages
npm show [package-name] scripts 2>/dev/null
# Check publish date and maintainers
npm view [package-name] time dist-tags maintainers 2>/dev/null
# Check if any installed packages are deprecated
npm view [package-name] deprecated 2>/dev/null
```

**If suspicious patterns found:** Warn user and recommend verification before installing.

**If deprecated packages found:** Flag in audit results with replacement suggestions. Deprecated packages receive no further security patches and are a supply chain risk.

#### Step 1.4: Present Audit Results

Present vulnerability and outdated package tables, then confirm scope. Include a "Deprecated Packages" section if any are found. See [references/audit-mode.md](references/audit-mode.md) for full audit results presentation template and scope confirmation prompt.

**Scope flag behavior:**
- `--dev`: Filter outdated and audit output to devDependencies only
- `--prod`: Filter outdated and audit output to production dependencies only
- `--package=<name>`: Filter all results to the specified package(s) only

**If no vulnerabilities found and all packages up to date and no deprecated packages:** Report clean audit results and exit. No further action needed.

**GATE: User must confirm update scope.**

---

### Phase 2: Plan

**Goal:** Categorize updates by risk and create batched update plan

#### Step 2.1: Categorize Updates

Group updates by risk level and present batch plan. See [references/update-plan-template.md](references/update-plan-template.md) for full batch plan, risk assessment, and update strategy templates.

**Security fix requiring major version:** If a vulnerability fix is only available in a major version (e.g., `lodash@3 -> lodash@4`), present this separately with breaking change analysis. User must explicitly approve major version bumps even for security fixes.

#### Step 2.2: Approve Plan

Present the update strategy and get approval.

**GATE: User must approve update plan.**

---

### Phase 3: Update

**Goal:** Apply updates in batches with validation after each

**Scope flag behavior:**
- `--dry-run`: Skip Phase 3-5 entirely. Run through Phase 1-2 (audit + plan) only, then exit.
- `--package=<name>`: Apply updates only to the specified package(s).

#### Step 3.1: Apply Updates in Batches

Before the first batch, confirm `package.json` and `$LOCK_FILE` have no uncommitted changes (`git status --porcelain package.json $LOCK_FILE`) — if they're dirty, stop and get them committed or stashed first, so each batch has a clean revert point.

**For each approved batch:**

```bash
# Install updates using detected package manager
$PKG_MGR install package1@X.Y.W package2@A.B.D
```

#### Step 3.2: Quick Validation After Each Batch

```bash
$PKG_MGR run typecheck
```

**If type errors occur:** Present warning with options (fix, revert batch, pin version). To revert the batch: `git checkout -- package.json $LOCK_FILE && $PKG_MGR install`, which restores the last committed manifest/lockfile and reinstalls. Wait for decision. See [references/common-issues.md](references/common-issues.md) for troubleshooting.

#### Step 3.3: Progress Report

```markdown
## Update Progress

| Batch | Status | Notes |
|-------|--------|-------|
| 1. Security | Complete | |
| 2. Patches | Complete | |
| 3. Minor | Complete | |
| 4. Major | In progress | Type fixes needed |
```

---

### Phase 4: Validate

**Goal:** Full validation after all updates applied

**Delegate each check to its own subagent** — run every distinct command via a separate `Agent` call, never directly in the main agent's shell and never bundled into one call. Send independent checks in a single message with multiple tool uses so they run concurrently. Give each subagent its exact command and require full raw output back; read every subagent's output yourself before reporting results. See `ai-assistant-protocol` § Validation Execution.

#### Step 4.1: Full Validation

```bash
$PKG_MGR run typecheck
$PKG_MGR run lint
$PKG_MGR run test
$PKG_MGR run build
```

#### Step 4.2: Validation Report

```markdown
## Validation Results

| Check | Status | Details |
|-------|--------|---------|
| Type check | Pass / Fail | [details] |
| Lint | Pass / Fail | [details] |
| Tests | Pass / Fail | X passed, Y failed |
| Build | Pass / Fail | [details] |
```

**If failures:** Present options (fix and re-validate, revert packages, create todo). To revert all package updates: `git checkout -- package.json $LOCK_FILE && $PKG_MGR install`. Wait for decision.

**GATE: All validations must pass before commit.**

---

### Phase 5: Commit

**Goal:** Create a clean commit for the dependency updates

#### Step 5.1: Review Changes

Present summary of files changed, packages updated, and security fixes resolved.

#### Step 5.2: Create Commit

Determine the correct lock file name based on the detected package manager:
- pnpm: `pnpm-lock.yaml`
- yarn: `yarn.lock`
- npm: `package-lock.json`

```bash
# Stage both package.json and the correct lock file
git add package.json $LOCK_FILE
git commit -m "chore(deps): update dependencies

Security:
- Fix X vulnerabilities

Updates:
- package1: 1.0.0 -> 1.0.1
- package2: 2.0.0 -> 2.1.0"
```

**GATE: User confirmation required before commit.**

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| DEP-T1 | Positive | "Check for vulnerabilities" | Skill triggers |
| DEP-T2 | Positive | "Update outdated packages" | Skill triggers |
| DEP-T3 | Positive | "Audit dependencies" | Skill triggers |
| DEP-T4 | Negative | "Install a new package" | Does NOT trigger (manual task) |
| DEP-T5 | Negative | "What version of React are we using?" | Does NOT trigger (-> /explore) |
| DEP-T6 | Boundary | "Update lodash" | Triggers with --package=lodash scope |

## References

- [Audit Mode & Results Templates](references/audit-mode.md) -- Audit results presentation, scope confirmation, and audit-only report templates
- [Update Plan Template](references/update-plan-template.md) -- Batch plan, risk assessment, and update strategy templates
- [Handling Common Issues](references/common-issues.md) -- Type errors, peer dependency conflicts, and lock file troubleshooting
