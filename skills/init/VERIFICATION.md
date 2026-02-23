# Verification: init

## Scenario

A developer joins a team working on a Next.js 14 + Tailwind + Prisma + TypeScript project. They clone the repo and run `/init` to bootstrap AI assistant configuration. The project has:

- `pnpm-lock.yaml` present (package manager is pnpm)
- `prisma/schema.prisma` with database models
- `src/app/` directory (Next.js App Router)
- `tailwind.config.ts` for Tailwind CSS configuration
- Existing `.env.local` with environment variables
- `package.json` with dependencies: `next`, `react`, `@prisma/client`, `tailwindcss`, `typescript`
- `package.json` scripts: `dev`, `build`, `lint`, `test`, `db:migrate`, `db:push`
- No pre-existing `.ai-project/` directory

## Expected Outcome

- `.ai-project/` directory is fully populated with project-specific values (not placeholders)
- `.memory.md` has architecture overview mentioning Next.js App Router + Prisma + Tailwind
- `.context.md` has common import patterns from the actual codebase (e.g., `import { prisma } from '@/lib/prisma'`, Next.js `'use client'` directives, Tailwind `cn()` utility usage)
- `config.yaml` has `packageManager: pnpm` and detected domains listed
- `project/stack.md` lists Next.js 14, TypeScript, Prisma, Tailwind CSS
- `project/commands.md` uses `pnpm run dev`, not `npm run dev`
- Domain detection identifies Next.js, Tailwind, Prisma, TypeScript and generates corresponding `.instructions.md` files
- `CLAUDE.md` at project root is populated with real values

## Checkpoints

- [ ] Checkpoint 1: Package manager detected as pnpm (from `pnpm-lock.yaml` lockfile presence)
- [ ] Checkpoint 2: Tech stack detected -- Next.js 14 (from `next` in dependencies), Tailwind CSS (from `tailwindcss` in dependencies + `tailwind.config.ts`), Prisma (from `@prisma/client` + `prisma/schema.prisma`), TypeScript (from `typescript` in devDependencies + `tsconfig.json`)
- [ ] Checkpoint 3: `.memory.md` populated with real architecture info -- mentions Next.js App Router (`src/app/`), Prisma ORM, Tailwind CSS; no `{{PLACEHOLDER}}` variables remain (the template has 70+ placeholders that all must be replaced)
- [ ] Checkpoint 4: `.context.md` populated with actual import patterns from the codebase -- framework-specific imports like `next/image`, `next/link`, `@prisma/client`, Tailwind utility patterns; no `{{PLACEHOLDER}}` variables remain
- [ ] Checkpoint 5: `config.yaml` persists detected settings including package manager, detected domains, and project structure paths
- [ ] Checkpoint 6: Domain-specific instruction files generated for detected stack -- at minimum `typescript.instructions.md`, `prisma.instructions.md`, `nextjs.instructions.md`, `tailwind.instructions.md` in `.ai-project/domains/`
- [ ] Checkpoint 7: User shown summary of detected configuration (tech stack, commands, project structure) and asked to confirm before files are written
- [ ] Checkpoint 8: All generated commands use `pnpm` (e.g., `pnpm run dev`, `pnpm run build`), not `npm`
- [ ] Checkpoint 9: `project/structure.md` reflects the actual directory layout including `src/app/`, `prisma/`, and other real directories
- [ ] Checkpoint 10: `CLAUDE.md` at project root has no remaining `{{PLACEHOLDER}}` variables

## Anti-patterns

- Agent should not leave `{{PLACEHOLDER}}` variables in generated files -- every placeholder in `.memory.md`, `.context.md`, `CLAUDE.md`, and all project files must be replaced with real or sensible default values
- Agent should not hardcode `npm` when `pnpm-lock.yaml` exists -- lockfile detection must drive the package manager choice
- Agent should not skip codebase scanning and leave `.memory.md` / `.context.md` empty or with only template content
- Agent should not write files without showing the user what will be created and waiting for confirmation
- Agent should not generate generic/boilerplate domain instruction files that ignore actual codebase conventions (e.g., a `prisma.instructions.md` that doesn't reference the project's actual schema patterns)
- Agent should not ignore `src/app/` as a signal for Next.js App Router and default to Pages Router
- Agent should not skip the `.env.local` detection -- environment variable patterns should be noted (without exposing secret values)
- Agent should not create domain instruction files for frameworks not in the project (e.g., no `vue.instructions.md`)

## Gap Analysis

| Checkpoint | Coverage | Notes |
|------------|----------|-------|
| 1. Package manager detection | Implicit | `references/template-variables.md` lists `{{PACKAGE_MANAGER}}` but the main workflow (Phase 1) does not explicitly check for lockfiles; detection relies on the agent inferring from `package.json` or lockfile without explicit guidance |
| 2. Tech stack detection | Covered | Phase 1.4 says "Detect: framework, test framework, build tool, linter, formatter" and `references/domain-detection.md` has a detection table |
| 3. `.memory.md` population | Missing | The workflow copies the template (Phase 0) and says "Replace ALL placeholders" (Phase 2) but has no explicit step to scan the codebase and populate `.memory.md` with architecture information; the 70+ placeholders in the template (e.g., `{{DECISION}}`, `{{RECENT_WORK}}`, `{{ONGOING_WORK}}`) have no population rules |
| 4. `.context.md` population | Missing | Same issue -- the template has `{{FRAMEWORK}}`, `{{CATEGORY_1}}`, `{{SERVICE_STRUCTURE}}`, `{{ERROR}}` placeholders but Phase 2 steps (2.1-2.4) only cover `commands.md`, `structure.md`, `patterns.md`, `stack.md`; `.context.md` is never explicitly populated |
| 5. `config.yaml` persistence | Missing | `config.yaml` is copied from template but no step writes detected values (package manager, domains, etc.) into it; it remains a generic defaults file |
| 6. Domain instruction files | Covered | Phase 2.5 + `references/domain-detection.md` provide detection rules and generation guidance |
| 7. User confirmation before writing | Implicit | Phase 1.5 confirms detection accuracy and Phase 1.6 gathers preferences, but there is no explicit gate between Phase 2 (generation) and file writing that shows what files will be created |
| 8. Commands use correct package manager | Implicit | Depends on `{{PACKAGE_MANAGER}}` being detected correctly; no explicit instruction to derive command prefix from package manager |
| 9. Real directory structure | Covered | Phase 1.2 analyzes directory structure with `find` and `tree` commands |
| 10. CLAUDE.md fully populated | Covered | Phase 2.6 explicitly handles CLAUDE.md generation from template with placeholder replacement |

## Findings

- **Gaps**:
  - `.memory.md` and `.context.md` are never explicitly populated -- they are copied from templates with 70+ placeholders but Phase 2 only generates `commands.md`, `structure.md`, `patterns.md`, and `stack.md`. There is no step that says "scan the codebase and write real architecture information into `.memory.md`" or "extract actual import patterns into `.context.md`".
  - Package manager detection is not prominent in the main workflow. The `{{PACKAGE_MANAGER}}` placeholder exists in `references/template-variables.md` but Phase 1 never explicitly says "check for lockfiles to determine package manager." An agent may default to `npm`.
  - `config.yaml` is copied from the template as-is (a generic defaults file) with no step to write detected settings into it. The package manager, detected domains, and project paths are never persisted there.
  - There is no pre-write confirmation gate -- the user confirms detection in Phase 1.5 and preferences in Phase 1.6, but there is no gate after Phase 2 where the agent shows exactly which files it will write and their content before committing to disk.

- **Improvements**:
  - Add explicit Phase 2 steps for populating `.memory.md` and `.context.md` by scanning the codebase -- not just copying templates.
  - Add lockfile-based package manager detection as a named step in Phase 1, not buried in references.
  - Add a `config.yaml` persistence step that writes detected values (package manager, domain list, source directories) after detection.
  - Enhance domain detection with specific patterns for common stacks: Next.js App Router (`src/app/`), Tailwind (`tailwind.config.*`), Prisma (`prisma/schema.prisma`).
  - Add a pre-write confirmation gate showing the file list and key content before writing.
  - Add an early exit for already-initialized projects that are fully populated.

- **Structural**:
  - The `.memory.md` template contains sections (`Architecture Decisions`, `Known Issues`, `Session Context`) with placeholders (`{{DECISION}}`, `{{ISSUE}}`, `{{RECENT_WORK}}`) that have no sensible "detected" value during init. These sections should be initialized with empty tables or "None yet" rather than left with unfilled placeholders.
  - The `.context.md` template mixes framework-specific content (Vitest imports hardcoded) with generic placeholders, making it unclear what the agent should populate vs. what is already correct.
  - The template variable reference (`references/template-variables.md`) acknowledges "structural placeholders" that are "filled contextually during generation" but provides no rules for how to fill them, making it easy for agents to skip them.
