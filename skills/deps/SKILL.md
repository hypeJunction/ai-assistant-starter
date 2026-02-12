---
name: deps
description: Audit, update, and manage project dependencies safely. Use when checking for vulnerabilities, updating outdated packages, or performing routine dependency maintenance.
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
npm audit 2>/dev/null || true
# Or: pnpm audit / yarn audit
```

#### Step 1.3: Supply Chain Checks

For any new dependencies being added, verify:

1. **Package legitimacy** — Check for typosquatting (e.g., `lodahs` instead of `lodash`)
2. **Maintenance status** — Is the package actively maintained? Check last publish date
3. **Download count** — Very low downloads on a common-sounding name is a red flag
4. **Install scripts** — Check for `preinstall`/`postinstall` scripts that execute arbitrary code

```bash
# Check for install scripts in new packages
npm show [package-name] scripts 2>/dev/null
# Check publish date and maintainers
npm view [package-name] time dist-tags maintainers 2>/dev/null
```

**If suspicious patterns found:** Warn user and recommend verification before installing.

#### Step 1.4: Present Audit Results

Present vulnerability and outdated package tables, then confirm scope. See [references/audit-mode.md](references/audit-mode.md) for full audit results presentation template and scope confirmation prompt.

**GATE: User must confirm update scope.**

---

### Phase 2: Plan

**Goal:** Categorize updates by risk and create batched update plan

#### Step 2.1: Categorize Updates

Group updates by risk level and present batch plan. See [references/update-plan-template.md](references/update-plan-template.md) for full batch plan, risk assessment, and update strategy templates.

#### Step 2.2: Approve Plan

Present the update strategy and get approval.

**GATE: User must approve update plan.**

---

### Phase 3: Update

**Goal:** Apply updates in batches with validation after each

#### Step 3.1: Apply Updates in Batches

**For each approved batch:**

```bash
# Install updates (adapt for pnpm/yarn)
npm install package1@X.Y.W package2@A.B.D
```

#### Step 3.2: Quick Validation After Each Batch

```bash
npm run typecheck
```

**If type errors occur:** Present warning with options (fix, revert batch, pin version). Wait for decision. See [references/common-issues.md](references/common-issues.md) for troubleshooting.

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

#### Step 4.1: Full Validation

```bash
npm run typecheck
npm run lint
npm run test
npm run build
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

**If failures:** Present options (fix and re-validate, revert packages, create todo). Wait for decision.

**GATE: All validations must pass before commit.**

---

### Phase 5: Commit

**Goal:** Create a clean commit for the dependency updates

#### Step 5.1: Review Changes

Present summary of files changed, packages updated, and security fixes resolved.

#### Step 5.2: Create Commit

```bash
git add package.json package-lock.json
git commit -m "chore(deps): update dependencies

Security:
- Fix X vulnerabilities

Updates:
- package1: 1.0.0 -> 1.0.1
- package2: 2.0.0 -> 2.1.0"
```

**GATE: User confirmation required before commit.**

## References

- [Audit Mode & Results Templates](references/audit-mode.md) -- Audit results presentation, scope confirmation, and audit-only report templates
- [Update Plan Template](references/update-plan-template.md) -- Batch plan, risk assessment, and update strategy templates
- [Handling Common Issues](references/common-issues.md) -- Type errors, peer dependency conflicts, and lock file troubleshooting
