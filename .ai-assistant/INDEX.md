# Documentation Index

> Quick lookup for patterns, errors, and topics across all AI instruction files.

---

## Workflows

| Command | Workflow | Purpose |
|---------|----------|---------|
| `/explore` | [explore.prompt.md](./workflows/explore.prompt.md) | Understand code (read-only) |
| `/plan` | [plan.prompt.md](./workflows/plan.prompt.md) | Design approach before coding |
| `/implement` | [implement.prompt.md](./workflows/implement.prompt.md) | Full workflow: explore → plan → code → commit |
| `/debug` | [debug.prompt.md](./workflows/debug.prompt.md) | Find and fix bugs |
| `/validate` | [validate.prompt.md](./workflows/validate.prompt.md) | Run type check, lint, tests |
| `/commit` | [commit.prompt.md](./workflows/commit.prompt.md) | Review and commit changes |
| `/pr` | [create-pr.prompt.md](./workflows/create-pr.prompt.md) | Create pull request |
| `/refactor` | [refactor.prompt.md](./workflows/refactor.prompt.md) | Multi-file changes with tracking |
| `/review` | [review-branch.prompt.md](./workflows/review-branch.prompt.md) | Review branch changes |
| `/cover` | [cover.prompt.md](./workflows/cover.prompt.md) | Add test coverage |
| `/wrap` | [wrap.prompt.md](./workflows/wrap.prompt.md) | Wrap up work session |
| `/docs` | [docs.prompt.md](./workflows/docs.prompt.md) | Documentation tasks |
| `/init` | [init.prompt.md](./workflows/init.prompt.md) | Initialize project config |
| `/hotfix` | [hotfix.prompt.md](./workflows/hotfix.prompt.md) | Emergency fixes |
| `/release` | [release.prompt.md](./workflows/release.prompt.md) | Release management |
| `/deps` | [deps.prompt.md](./workflows/deps.prompt.md) | Dependency updates |
| `/revert` | [revert.prompt.md](./workflows/revert.prompt.md) | Revert changes |
| `/sync` | [sync.prompt.md](./workflows/sync.prompt.md) | Sync branches |
| `/create-todo` | [create-todo.prompt.md](./workflows/create-todo.prompt.md) | Track deferred work |
| `/file-list` | [create-file-list.prompt.md](./workflows/create-file-list.prompt.md) | Track batch operations |
| `/add-story` | [add-story.prompt.md](./workflows/add-story.prompt.md) | Add Storybook story for component |

---

## Chatmodes

| Mode | File | Purpose |
|------|------|---------|
| 🔍 Explorer | [explorer.chatmode.md](./chatmodes/explorer.chatmode.md) | Read-only exploration |
| 📋 Planner | [planner.chatmode.md](./chatmodes/planner.chatmode.md) | Design and planning |
| 👨‍💻 Developer | [developer.chatmode.md](./chatmodes/developer.chatmode.md) | Code implementation |
| 🧪 Tester | [tester.chatmode.md](./chatmodes/tester.chatmode.md) | Testing and QA |
| 👁️ Reviewer | [reviewer.chatmode.md](./chatmodes/reviewer.chatmode.md) | Code review |
| 🏗️ Architect | [architect.chatmode.md](./chatmodes/architect.chatmode.md) | Architecture decisions |
| 🐛 Debugger | [debugger.chatmode.md](./chatmodes/debugger.chatmode.md) | Problem diagnosis |
| 💾 Committer | [committer.chatmode.md](./chatmodes/committer.chatmode.md) | Git commits |
| ♻️ Refactorer | [refactorer.chatmode.md](./chatmodes/refactorer.chatmode.md) | Multi-file changes |
| 🚀 Releaser | [releaser.chatmode.md](./chatmodes/releaser.chatmode.md) | PRs and releases |

---

## Domain Guidelines

### Code Quality
| Domain | File | Topics |
|--------|------|--------|
| TypeScript | [typescript.instructions.md](./domains/typescript.instructions.md) | Types, imports, exports |
| Testing | [testing.instructions.md](./domains/testing.instructions.md) | Test plans, mocking |
| Storybook | [storybook.instructions.md](./domains/storybook.instructions.md) | Stories, play functions, visual testing |
| Naming | [naming.instructions.md](./domains/naming.instructions.md) | Naming conventions |
| Code Review | [code-review.instructions.md](./domains/code-review.instructions.md) | Review guidelines |

### Architecture
| Domain | File | Topics |
|--------|------|--------|
| API Design | [api.instructions.md](./domains/api.instructions.md) | REST, requests, responses |
| Error Handling | [error-handling.instructions.md](./domains/error-handling.instructions.md) | Error patterns |
| Data Validation | [data-validation.instructions.md](./domains/data-validation.instructions.md) | Input validation |
| Performance | [performance.instructions.md](./domains/performance.instructions.md) | Optimization |

### Operations
| Domain | File | Topics |
|--------|------|--------|
| Git | [git.instructions.md](./domains/git.instructions.md) | Branches, commits |
| CI/CD | [ci-cd.instructions.md](./domains/ci-cd.instructions.md) | Pipelines |
| Docker | [docker.instructions.md](./domains/docker.instructions.md) | Containers |
| Env Config | [env-config.instructions.md](./domains/env-config.instructions.md) | Environment variables |

### Security & Ops
| Domain | File | Topics |
|--------|------|--------|
| Security | [security.instructions.md](./domains/security.instructions.md) | Security practices |
| Logging | [logging.instructions.md](./domains/logging.instructions.md) | Logging patterns |
| Database | [database.instructions.md](./domains/database.instructions.md) | Database patterns |
| Documentation | [documentation.instructions.md](./domains/documentation.instructions.md) | Doc guidelines |

---

## By Topic

### TypeScript
- **Avoid `any` type** → [typescript.instructions.md](./domains/typescript.instructions.md#avoid-any-type)
- **`satisfies` vs `as`** → [typescript.instructions.md](./domains/typescript.instructions.md#use-satisfies-instead-of-as)
- **Named exports only** → [typescript.instructions.md](./domains/typescript.instructions.md#named-exports-only)
- **Type guards** → [typescript.instructions.md](./domains/typescript.instructions.md#type-guards)

### Testing
- **Test plan format (Gherkin)** → [testing.instructions.md](./domains/testing.instructions.md#test-plan-format)
- **Testing Library queries** → [testing.instructions.md](./domains/testing.instructions.md#testing-library-queries)
- **Mocking patterns** → [testing.instructions.md](./domains/testing.instructions.md#mocking)

### Storybook
- **Story file structure** → [storybook.instructions.md](./domains/storybook.instructions.md#story-file-structure)
- **Play functions** → [storybook.instructions.md](./domains/storybook.instructions.md#interaction-tests-with-play)
- **MSW mocking** → [storybook.instructions.md](./domains/storybook.instructions.md#mocking)
- **Query strategies** → [storybook.instructions.md](./domains/storybook.instructions.md#query-strategies)

### Git
- **Branch naming** → [git.instructions.md](./domains/git.instructions.md#branch-naming)
- **Commit messages** → [git.instructions.md](./domains/git.instructions.md#commit-messages)

---

## By Pattern

### Data Patterns
- **Type guards** → `function isType(value: unknown): value is Type`
- **Discriminated unions** → `type Result = { success: true; data: T } | { success: false; error: string }`

### Testing Patterns
- **Test plan** → Gherkin format at top of test file
- **Scoped tests** → `npm run test -- ComponentName`

### Storybook Patterns
- **Story factory** → `const createStory = (args, config) => ({ args, ...config })`
- **Play function** → `play: async ({ canvasElement, step }) => { ... }`
- **Component query** → `within(canvasElement).getByRole('button')`
- **Global query** → `screen.getByRole('dialog')` for modals/toasts

---

## Project Layer Template

When `/init` is run, these templates are copied to `.ai-project/`:

| Template | Purpose |
|----------|---------|
| [.memory.md](./.ai-project/.memory.md) | Project architecture & stack |
| [.context.md](./.ai-project/.context.md) | Common patterns & imports |
| [project/](./ai-project/project/) | Project configuration |
| [todos/](./.ai-project/todos/) | Technical debt tracking |
| [history/](./.ai-project/history/) | Knowledge from past work |
| [decisions/](./.ai-project/decisions/) | Architecture Decision Records |
| [file-lists/](./.ai-project/file-lists/) | Batch operation tracking |

---

## Provider Configurations

Choose the right configuration for your AI assistant:

| Provider | File | Recommendation |
|----------|------|----------------|
| Claude Code | [claude.provider.md](./providers/claude.provider.md) | **Recommended** - Full feature support |
| Cursor | [cursor.provider.md](./providers/cursor.provider.md) | Good for inline edits |
| GitHub Copilot | [copilot.provider.md](./providers/copilot.provider.md) | Code suggestions only |
| Windsurf | [windsurf.provider.md](./providers/windsurf.provider.md) | Similar to Cursor |
| Gemini | [gemini.provider.md](./providers/gemini.provider.md) | Experimental |

**Compatibility Matrix:** [providers/README.md](./providers/README.md)

---

## Configuration

### Project Config

Override framework defaults in `.ai-project/config.md`:

```yaml
use_emojis: true       # false for text-only output
message_style: detailed # 'detailed' or 'compact'
auto_validate: true    # Run checks after changes
commit_style: conventional # 'conventional', 'ticket', 'simple'
```

---

## Navigation

**Entry Point:** [.instructions.md](./.instructions.md)

**Reference:**
- [scope.md](./scope.md) - Scope flags and inheritance
- [README.md](./README.md) - Framework overview
- [CHANGELOG.md](../CHANGELOG.md) - Version history and migration notes

---

**Tip:** Use Ctrl+F to search this index for keywords.
