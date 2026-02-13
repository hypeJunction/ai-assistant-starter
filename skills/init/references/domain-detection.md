# Domain Detection Rules

Generate project-specific domain instruction files in `.ai-project/domains/` based on detected stack. These complement the base background skills with project-specific conventions.

## Detection Table

| Detection | Generate When |
|-----------|---------------|
| Language: TypeScript | `package.json` has TypeScript |
| Language: Python | `pyproject.toml` or `requirements.txt` exists |
| Test: Vitest | Vitest in devDependencies |
| Test: Jest | Jest in devDependencies |
| Test: Pytest | pytest in Python deps |
| Framework: React | React in dependencies |
| Framework: Vue | Vue in dependencies |
| Framework: Express | Express in dependencies |
| Framework: FastAPI | FastAPI in Python deps |
| Storybook | Storybook in devDependencies |
| ORM: Prisma | Prisma in dependencies |
| ORM: Drizzle | Drizzle in dependencies |
| Validation: Zod | Zod in dependencies |
| Validation: Pydantic | Pydantic in Python deps |
| Docker | Dockerfile exists |
| CI: GitHub Actions | `.github/workflows/` exists |

## What to Generate

For each detected domain, create a `<domain>.instructions.md` file containing project-specific conventions observed from the codebase (e.g., import patterns, naming conventions, test organization). These override and supplement the generic base guideline skills.

## Example Generated File

```markdown
<!-- .ai-project/domains/typescript.instructions.md -->
# TypeScript — Project Conventions

## Import Order
1. Node built-ins
2. External packages
3. Internal aliases (@/components, @/utils)
4. Relative imports

## Path Aliases
- `@/` maps to `src/`
- `@test/` maps to `tests/`

## Patterns
- Prefer `type` imports for type-only usage
- Use barrel exports in `index.ts` files
```

## Presenting Results

Present to user which domains were detected:

```markdown
### Domain Context Generated

Based on your stack, project-specific domain files were created in `.ai-project/domains/`:

**Detected domains:**
- typescript.instructions.md (TypeScript detected)
- vitest.instructions.md (Vitest detected)
- react.instructions.md (React detected)

These contain project-specific conventions observed from your codebase.
Base domain guideline skills provide generic best practices.
Project domain files take precedence when rules conflict.
```
