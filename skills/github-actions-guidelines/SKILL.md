---
name: github-actions-guidelines
description: CI/CD guidelines for GitHub Actions including pipeline structure, caching, secrets management, deployment strategies, and quality gates. Auto-loaded when working with workflow files.
user-invocable: false
---

# CI/CD Guidelines

## Core Principles

1. **Automate everything** - No manual steps in the release process
2. **Fail fast** - Run quick checks first
3. **Reproducible builds** - Same inputs produce same outputs
4. **Security first** - Scan for vulnerabilities, manage secrets
5. **Observable** - Know what's deployed where

## Pipeline Structure

### Standard Pipeline Stages

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [{{DEFAULT_BRANCH}}]
  pull_request:
    branches: [{{DEFAULT_BRANCH}}]

jobs:
  # Stage 1: Quick checks (fail fast)
  lint:
    runs-on: {{CI_RUNNER}}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '{{NODE_VERSION}}'
          cache: '{{PACKAGE_MANAGER}}'
      - run: {{INSTALL_COMMAND}}
      - run: {{LINT_COMMAND}}

  typecheck:
    runs-on: {{CI_RUNNER}}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '{{NODE_VERSION}}'
          cache: '{{PACKAGE_MANAGER}}'
      - run: {{INSTALL_COMMAND}}
      - run: {{TYPECHECK_COMMAND}}

  # Stage 2: Tests (after lint passes)
  test:
    needs: [lint, typecheck]
    runs-on: {{CI_RUNNER}}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '{{NODE_VERSION}}'
          cache: '{{PACKAGE_MANAGER}}'
      - run: {{INSTALL_COMMAND}}
      - run: {{TEST_COVERAGE_COMMAND}}
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  # Stage 3: Build
  build:
    needs: [test]
    runs-on: {{CI_RUNNER}}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '{{NODE_VERSION}}'
          cache: '{{PACKAGE_MANAGER}}'
      - run: {{INSTALL_COMMAND}}
      - run: {{BUILD_COMMAND}}
      - uses: actions/upload-artifact@v4
        with:
          name: build
          path: {{BUILD_OUTPUT}}/

  # Stage 4: Security scan
  security:
    needs: [build]
    runs-on: {{CI_RUNNER}}
    steps:
      - uses: actions/checkout@v4
      - run: {{PACKAGE_MANAGER}} audit --audit-level=high
      - uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### Pull Request Checks

```yaml
# .github/workflows/pr.yml
name: PR Checks

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  pr-validation:
    runs-on: {{CI_RUNNER}}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # For commit history

      # Check PR size
      - name: Check PR size
        run: |
          ADDITIONS=$(gh pr view ${{ github.event.pull_request.number }} --json additions -q '.additions')
          if [ "$ADDITIONS" -gt 800 ]; then
            echo "::warning::Large PR with $ADDITIONS additions. Consider splitting."
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # Check commit messages
      - name: Validate commits
        run: |
          git log origin/{{DEFAULT_BRANCH}}..HEAD --format='%s' | while read msg; do
            if ! echo "$msg" | grep -qE '^(feat|fix|docs|style|refactor|perf|test|chore|ci|revert)(\(.+\))?: .+'; then
              echo "::error::Invalid commit message: $msg"
              exit 1
            fi
          done

      # Run tests for changed files only
      - name: Test changed files
        run: |
          {{INSTALL_COMMAND}}
          {{TEST_COMMAND}} -- --changedSince=origin/{{DEFAULT_BRANCH}}
```

## Caching

### Dependency Caching

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '{{NODE_VERSION}}'
    cache: '{{PACKAGE_MANAGER}}'  # Built-in caching

# Or manual cache for more control
- uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

### Build Caching

```yaml
- uses: actions/cache@v4
  with:
    path: |
      {{FRAMEWORK_CACHE}}
      {{BUILD_OUTPUT}}/.cache
    key: ${{ runner.os }}-build-${{ hashFiles('src/**') }}
    restore-keys: |
      ${{ runner.os }}-build-
```

## Secrets Management

### Using Secrets

```yaml
jobs:
  deploy:
    runs-on: {{CI_RUNNER}}
    steps:
      - name: Deploy
        env:
          API_KEY: ${{ secrets.API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          # Secrets are masked in logs
          ./deploy.sh

      # For deployment environments
      - name: Deploy to production
        environment: production  # Uses environment-specific secrets
        env:
          API_KEY: ${{ secrets.PROD_API_KEY }}
        run: ./deploy.sh
```

### Secrets Best Practices

```yaml
# Never echo secrets
- run: echo ${{ secrets.API_KEY }}  # BAD - masked but avoid

# Use environment variables
- env:
    API_KEY: ${{ secrets.API_KEY }}
  run: ./script.sh  # Script reads from env

# Rotate secrets regularly
# Use OIDC for cloud providers instead of long-lived credentials
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789:role/deploy
    aws-region: us-east-1
```

## Known Gotchas

### Workflow Permissions

```yaml
# Default permissions are restrictive
permissions:
  contents: read
  pull-requests: write  # If you need to comment on PRs
  issues: write         # If you need to create issues
```

### Checkout Depth

```yaml
# Shallow clone by default - some operations need full history
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Full history for versioning/changelogs
```

### Concurrent Runs

```yaml
# Prevent concurrent deployments
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false  # Don't cancel running deploys
```

### Environment Variables in Scripts

```yaml
# Variables aren't available in run scripts by default
- run: echo $MY_VAR  # Won't work

# Must set in env
- env:
    MY_VAR: ${{ vars.MY_VAR }}
  run: echo $MY_VAR  # Works
```

## Additional References

- [Deployment Strategies & Release Management](references/deployment-strategies.md)
- [Quality Gates, Notifications & Performance Optimization](references/ci-quality-notifications.md)
