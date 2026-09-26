# Update Plan Template

## Batch Plan

```markdown
## Update Plan

### Batch 1: Security Patches (Low Risk)
| Package | From | To | Risk |
|---------|------|----|----- |
| package1 | 1.0.0 | 1.0.1 | Low - security fix |

### Batch 2: Patch Updates (Low Risk)
| Package | From | To | Risk |
|---------|------|----|----- |
| package2 | 2.1.0 | 2.1.5 | Low - bug fixes |

### Batch 3: Minor Updates (Medium Risk)
| Package | From | To | Risk |
|---------|------|----|------|
| package3 | 3.0.0 | 3.2.0 | Medium - new features |

### Batch 4: Major Updates (High Risk)
| Package | From | To | Risk | Breaking Changes |
|---------|------|----|----- |------------------|
| typescript | 4.9.5 | 5.3.0 | High | Yes - see notes |

**Breaking Change Notes:**
- **typescript 5.x**: New strict checks, decorator changes
```

## Risk Assessment

```markdown
## Risk Assessment

| Risk Level | Packages | Recommendation |
|------------|----------|----------------|
| Low | X | Update together |
| Medium | Y | Update and test carefully |
| High | Z | Update one at a time |

**Estimated impact:**
- Type changes: [likely/unlikely]
- API changes: [likely/unlikely]
- Test failures: [likely/unlikely]
```

## Update Strategy

```markdown
## Update Strategy

**Proposed approach:**
1. Apply Batch 1 (security) -> validate
2. Apply Batch 2 (patches) -> validate
3. Apply Batch 3 (minor) -> validate
4. [If approved] Apply Batch 4 (major) -> validate thoroughly

**Approve this plan?** (yes / modify / skip batch N)
```
