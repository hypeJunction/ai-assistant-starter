# Domain Instructions

Stack-specific domain rules for your project. These files supplement (and can override) the base domain guideline skills.

## How It Works

During `/init`, domain instruction files are copied here based on your detected tech stack. You can also create your own.

## File Format

Domain instruction files use the `.instructions.md` extension:

```markdown
<!-- my-domain.instructions.md -->
# My Domain Conventions

Rules and patterns specific to this domain.

## Patterns
- Pattern 1
- Pattern 2
```

## Creating Local Domain Rules

To add project-specific rules that go beyond the base skills:

1. Create a new `<name>.instructions.md` file in this directory
2. Write your domain-specific conventions
3. The assistant will load these when working in the relevant domain

## Precedence

When rules conflict:
1. User's explicit request (highest)
2. Project domain rules (this directory)
3. Base domain guideline skills
4. General best practices (lowest)
