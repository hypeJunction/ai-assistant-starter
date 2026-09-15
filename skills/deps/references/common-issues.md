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

## Reverting Applied Updates

Requires `package.json`/lock file to have been clean before updates started (see Step 3.1).

```bash
# Discard update changes and restore the last committed manifest/lockfile
git checkout -- package.json package-lock.json   # or pnpm-lock.yaml / yarn.lock

# Reinstall from the restored lockfile
npm install   # or pnpm install / yarn install
```

If the bad update was already committed, revert that commit instead (see the `revert` skill) and reinstall afterward.
