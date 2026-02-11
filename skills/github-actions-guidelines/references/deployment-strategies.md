Deployment strategies and release management patterns for GitHub Actions CI/CD pipelines.

## Deployment Strategies

### Environment Promotion

```yaml
# Deploy to staging on {{DEFAULT_BRANCH}} push
name: Deploy

on:
  push:
    branches: [{{DEFAULT_BRANCH}}]

jobs:
  deploy-staging:
    runs-on: {{CI_RUNNER}}
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh staging

  # Manual approval for production
  deploy-production:
    needs: [deploy-staging]
    runs-on: {{CI_RUNNER}}
    environment: production  # Requires approval
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production
```

### Blue-Green Deployment

```yaml
deploy:
  steps:
    # Deploy to inactive environment
    - name: Deploy to blue
      run: |
        ./deploy.sh blue
        ./health-check.sh blue

    # Switch traffic
    - name: Switch traffic
      run: |
        ./switch-traffic.sh blue
        ./verify-switch.sh

    # Rollback on failure
    - name: Rollback on failure
      if: failure()
      run: ./switch-traffic.sh green
```

### Canary Deployment

```yaml
deploy:
  steps:
    - name: Deploy canary (10%)
      run: |
        ./deploy-canary.sh 10
        sleep 300  # Monitor for 5 minutes

    - name: Check canary metrics
      run: |
        ERROR_RATE=$(./get-error-rate.sh canary)
        if [ "$ERROR_RATE" -gt 1 ]; then
          ./rollback-canary.sh
          exit 1
        fi

    - name: Full rollout
      run: ./deploy-canary.sh 100
```

## Release Management

### Semantic Versioning

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: {{CI_RUNNER}}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        run: |
          git log $(git describe --tags --abbrev=0 HEAD^)..HEAD \
            --format='- %s' > CHANGELOG.md

      - name: Create release
        uses: softprops/action-gh-release@v1
        with:
          body_path: CHANGELOG.md
          files: |
            {{BUILD_OUTPUT}}/*
```

### Automated Version Bumping

```yaml
# Using conventional commits
- name: Bump version
  run: |
    npm version $(npx conventional-recommended-bump -p angular) \
      --no-git-tag-version

- name: Create tag
  run: |
    VERSION=$(node -p "require('./package.json').version")
    git tag "v$VERSION"
    git push origin "v$VERSION"
```
