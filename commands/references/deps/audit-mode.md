# Audit Mode & Results Templates

## Audit Results Presentation

Present after running outdated and security audit checks:

```markdown
## Dependency Audit

### Security Vulnerabilities

| Severity | Count | Packages |
|----------|-------|----------|
| Critical | N | package1, package2 |
| High | N | package3 |
| Moderate | N | package4, package5 |
| Low | N | package6 |

### Outdated Packages

| Package | Current | Wanted | Latest | Type |
|---------|---------|--------|--------|------|
| lodash | 4.17.20 | 4.17.21 | 4.17.21 | patch |
| react | 18.2.0 | 18.2.0 | 18.3.0 | minor |
| typescript | 4.9.5 | 4.9.5 | 5.3.0 | **major** |

### Summary
- **X** packages with security issues
- **Y** packages outdated (Z major, W minor, V patch)
```

## Scope Confirmation Prompt

```markdown
> **ACTION REQUIRED:**
> What would you like to update?
>
> - `security` - Security patches only (X packages)
> - `safe` - Patch + minor updates (Y packages)
> - `all` - Include major updates (Z packages)
> - `select` - Choose specific packages
> - `skip` - No updates, just audit
```

## Audit-Only Report

When using `/deps audit` (no updates), present this summary:

```markdown
## Dependency Audit Report

### Security Summary
| Severity | Count | Action Needed |
|----------|-------|---------------|
| Critical | 0 | None |
| High | 2 | Update recommended |
| Moderate | 5 | Review when convenient |
| Low | 3 | Optional |

### Outdated Summary
| Type | Count |
|------|-------|
| Major | 3 |
| Minor | 8 |
| Patch | 12 |

### Recommendations
1. **Immediate:** Update packages with high/critical vulnerabilities
2. **Soon:** Apply patch and minor updates
3. **Plan:** Review major updates for breaking changes

**Run `/deps update` to apply updates.**
```
