# Web Project Verification Commands

## Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| Dev server | `npx nx serve web` | Hot reload at localhost:4200 |
| Unit tests | `npx nx test session-waveform` | Vitest |
| Storybook dev | `npx nx storybook session-waveform` | Port 4400 |
| Storybook tests | `npx test-storybook` | Requires Storybook running |
| Type check | `npx tsc --noEmit` | TypeScript only |
| Lint | `npx nx lint web` | ESLint |

## Verification Steps (DO NOT BUILD)

### 1. Run Unit Tests (Fast)
```bash
npx nx test session-waveform
```
Runs Vitest tests for the session-waveform library.

### 2. Run Storybook Tests (Interactive Components)
First, start Storybook in one terminal:
```bash
npx nx storybook session-waveform
```

Then run interaction tests in another terminal:
```bash
npx test-storybook --url http://localhost:4400 --config-dir libs/session-waveform/.storybook
```

**Note:** Storybook tests use Playwright with real browsers, so they take ~60-90 seconds for the full suite. Filter output with:
```bash
npx test-storybook --url http://localhost:4400 --config-dir libs/session-waveform/.storybook 2>&1 | grep -E "(PASS|FAIL)"
```

### 3. Check Dev Server (Visual Verification)
```bash
npx nx serve web
```
Opens development server with hot reload. Check the browser console for errors.

### 4. Type Check (Optional)
```bash
npx tsc --noEmit
```
Note: `vue-tsc` has issues with Node 24, use plain `tsc` instead.

## Common Mistakes to Avoid

1. **DON'T run `npx nx build` for verification** - Build is for production, not testing
2. **DON'T run `npx nx build-storybook`** - This builds static files, not needed for testing
3. **DON'T confuse build errors with runtime errors** - Use dev server to see actual behavior

## Project Structure

- `web/` - Main Vue application
- `web/libs/session-waveform/` - Waveform editor library with Storybook
- `web/src/views/` - Application views and components

## NX Targets Available

### web project
- `serve` - Dev server
- `build` - Production build
- `test` - Unit tests
- `lint` - ESLint

### session-waveform library
- `build` - Library build
- `test` - Unit tests
- `lint` - ESLint
- `storybook` - Storybook dev server
- `build-storybook` - Build static Storybook (CI only)
