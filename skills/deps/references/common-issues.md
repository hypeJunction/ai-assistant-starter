# Handling Common Issues

## Type Errors After Update

```bash
# Check what changed in the package
npm info package-name changelog

# Or check the repo
gh repo view package-name/package-name --web
```

## Peer Dependency Conflicts

```markdown
> **WARNING:**
> Peer dependency conflict detected:
>
> ```
> [conflict details]
> ```
>
> **Options:**
> 1. Use `--legacy-peer-deps` (npm)
> 2. Update conflicting packages together
> 3. Skip this update
```

## Lock File Conflicts

```bash
# Regenerate lock file
rm package-lock.json && npm install

# Or for other managers
# rm pnpm-lock.yaml && pnpm install
# rm yarn.lock && yarn install
```
