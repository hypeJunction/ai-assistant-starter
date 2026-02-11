Quality gates, notification patterns, and performance optimization for GitHub Actions CI/CD pipelines.

## Quality Gates

### Required Checks

```yaml
# Branch protection rules (configure in GitHub)
# - Require status checks: lint, test, build
# - Require reviews: 1
# - Require up-to-date branches

# In workflow, set required checks
jobs:
  lint:
    # This job name must match branch protection rule
    runs-on: {{CI_RUNNER}}
    steps:
      - run: npm run lint

  # Matrix builds report as single check
  test:
    strategy:
      matrix:
        node: [{{NODE_VERSION}}]
    runs-on: {{CI_RUNNER}}
    steps:
      - run: npm test
```

### Code Coverage

```yaml
test:
  steps:
    - run: {{TEST_COVERAGE_COMMAND}}

    - name: Check coverage threshold
      run: |
        COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
        if (( $(echo "$COVERAGE < 80" | bc -l) )); then
          echo "Coverage $COVERAGE% is below 80% threshold"
          exit 1
        fi
```

## Notifications

### Slack Notifications

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    channel: '#deployments'
    fields: repo,commit,author,action,ref
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Failure Notifications

```yaml
- name: Notify on failure
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `CI failed on ${context.sha.slice(0, 7)}`,
        body: `Workflow: ${context.workflow}\nRun: ${context.runId}`,
        labels: ['ci-failure']
      })
```

## Performance Optimization

### Parallel Jobs

```yaml
jobs:
  # These run in parallel
  lint:
    runs-on: {{CI_RUNNER}}
    steps: [...]

  typecheck:
    runs-on: {{CI_RUNNER}}
    steps: [...]

  # This waits for both
  test:
    needs: [lint, typecheck]
    runs-on: {{CI_RUNNER}}
```

### Matrix Builds

```yaml
test:
  strategy:
    fail-fast: false  # Don't cancel others on failure
    matrix:
      os: [{{CI_RUNNER}}]
      node: [{{NODE_VERSION}}]
  runs-on: ${{ matrix.os }}
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node }}
    - run: npm test
```
