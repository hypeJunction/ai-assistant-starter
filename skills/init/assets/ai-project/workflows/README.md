# Custom Workflows

Project-specific workflow extensions. Use these to define custom multi-step processes that go beyond the base workflow skills.

## File Format

Custom workflows use the `.workflow.md` extension:

```markdown
<!-- deploy.workflow.md -->
# Deploy Workflow

## Steps
1. Run validate
2. Build production bundle
3. Run smoke tests
4. Deploy to staging
5. Confirm before production deploy
```

## When to Create Custom Workflows

- Your project has unique multi-step processes not covered by base skills
- You want to combine base skills in a specific order
- You have project-specific gates or approval steps
