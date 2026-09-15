# Security Notes — `apply-template` Install Scripts

`/apply-template` runs three scripts, all in
`skills/apply-template/scripts/`. Each is short enough to read in full before
trusting it — that's deliberate, not incidental. Read them; this file
summarizes what you'll find.

## `backup-claude-md.sh`
Copies the target project's existing `CLAUDE.md` to
`CLAUDE.md.bak.<UTC timestamp>` before anything else runs. No network calls,
no `eval`. Only reads/writes the single path passed to it. If there's no
existing file, it exits successfully and writes nothing.

## `apply-template.sh`
Merges the template's marker-delimited sections
(`<!-- ai-assistant-starter:begin:X -->` … `:end:X -->`) into the target
`CLAUDE.md`.

- **Dry-run by default.** It prints a unified diff and writes nothing unless
  called with `--apply`. The skill always shows you this diff before asking
  whether to apply.
- **Marker-scoped, not blind regex.** Each managed section is replaced
  wholesale between its own begin/end markers, or appended if the target has
  no such block yet. Everything else in your `CLAUDE.md` — your own project
  conventions, anything outside a recognized marker block — is left
  untouched. Re-running it is safe: it won't duplicate sections it already
  applied.
- **No network access**, no `curl`/`wget`, no sourcing of external files.
  Only two paths are ever touched (template, target), both passed explicitly
  as arguments — nothing is inferred or globbed.

## `copy-readmes.sh`
Copies the companion READMEs you selected into the target project's `docs/`.

- Refuses any filename it doesn't already recognize under this skill's
  `assets/readmes/` — it can't be redirected at an arbitrary source.
- Refuses path-like or dotfile names (`../`, absolute paths, leading `.`) to
  stay confined to the destination directory you gave it.
- Won't overwrite an existing destination file unless you pass `--force`.

## What none of these do
No script here downloads anything, shells out to another script, phones
home, or touches files outside the explicit paths it's given. If you want to
verify that independently: `grep -n 'curl\|wget\|eval\|source \|\. \$' skills/apply-template/scripts/*.sh`
should only match this file's own explanatory comments about their absence —
never an actual invocation.
