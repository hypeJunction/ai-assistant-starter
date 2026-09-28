# Structurally Dead Permission Entries

`permissions.allow`/`permissions.deny` entries in `settings.json` don't carry a usage counter, so classifying them needs a different test than plugins/skills: **can this literal pattern ever match a different future command?** If no, it's dead regardless of whether it was ever used — a one-shot command that already ran once, hardcoded into the permission list, will never run identically again.

A wildcarded entry (`Bash(pnpm test:*)`, `WebFetch(domain:github.com)`) is reusable by construction — leave it alone even with zero recent use, since it's a *pattern*, not a *transcript*. Only flag entries that are literal, unwildcarded, and specific enough that a future command matching them exactly is implausible.

## Shapes to flag

**Embedded heredocs.** A `Bash(...)` entry containing a `<<'EOF' ... EOF` block with real file content (a license header, a config file body) captured the entire multi-line command as the permission string. It will never match again because the next time that file needs writing, the content (or the invocation) will differ even slightly.

```
Bash(/path/to/LICENSE << 'LICEOF'\nMIT License\n...\nLICEOF)
```

**Hardcoded resolved absolute paths with resolved values baked in.** A path that includes a resolved package version, a specific data file, or a one-off script invocation:

```
Bash(NODE_PATH=/home/user/project/node_modules/.pnpm/better-sqlite3@12.6.2/node_modules node /home/user/project/e2e/seed-test-users.js /home/user/project/apps/web/data.db)
```

The package version will bump, the seed script's arguments will change — this exact string is a photograph of one past invocation, not a rule.

**Hardcoded ports/PIDs/one-off flags.**

```
Bash(node_modules/.bin/vite --port 5556)
Bash(lsof -ti:1420)
```

These are almost always leftovers from a single debugging session pinned to whatever port happened to be free that day.

**Stray shell-loop fragments.** When a multi-line `for`/`do`/`done` shell block gets tool-call-approved, some permission systems record each *line* as a separate allowed command rather than the whole block:

```
Bash(for id in 16r kah bgb 50s 3eh 9mr)
Bash(do bd show modern-starter-$id)
Bash(do)
Bash(done)
```

Each fragment is meaningless standalone — `do` and `done` alone approve nothing reusable, and the `for id in <specific ids>` line hardcodes a set of IDs from one past query.

**One-shot environment/setup commands** that were needed exactly once (installing a browser dependency check, a `pkg-config` probe during a native-build setup, a one-time icon-generation `convert`/`magick` call):

```
Bash(pkg-config --libs --cflags webkit2gtk-4.1)
Bash(convert -size 256x256 xc:'#d4a853' /path/to/icon.png)
```

## Shapes NOT to flag

- Any entry ending in `:*` — reusable by construction.
- A literal command with no embedded variable data that plausibly recurs verbatim (`Bash(cargo --version)`, `Bash(rustc --version)`) — low value to keep, but harmless; only remove these alongside a genuine cleanup pass, not as a priority.
- Domain-scoped `WebFetch(domain:example.com)` entries — these are patterns over an entire domain, not a single request.
- `mcp__<server>__<tool>` entries with no arguments encoded — these gate a whole tool, not one invocation, and remain reusable.

## Judgment call

If an entry is ambiguous (a literal command that's plausible but not certain to recur), prefer leaving it — the cost of one extra unused permission-list line is near zero; the cost of asking for a permission prompt again on a command that should have been pre-approved is a real interruption. Only flag entries where the "this can never match again" case is clear.
