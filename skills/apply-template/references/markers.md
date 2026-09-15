# Marker Convention

Each managed section in `assets/templates/CLAUDE.md.template` is wrapped in:

```
<!-- ai-assistant-starter:begin:<section-id> -->
...
<!-- ai-assistant-starter:end:<section-id> -->
```

`apply-template.sh` extracts each `<section-id>` from the template and, for
every one:

- If the target file already contains a matching `begin`/`end` pair, the
  content between them is replaced wholesale with the template's current
  version of that block.
- If not, the block is appended to the end of the target file.

Content outside recognized marker pairs — a project's own headings, prose,
or other sections — is never read or modified by the merge.

## Adding a new managed section

1. Add a new `begin`/`end` pair with a unique `<section-id>` to
   `assets/templates/CLAUDE.md.template`.
2. No script change is needed — `apply-template.sh` discovers section ids by
   scanning the template's own markers.
3. Document the new section in `SKILL.md`'s workflow if it changes what gets
   shown in the dry-run diff meaningfully.

## Conditional sections (content depends on user choice)

`CLAUDE.md.template` only holds sections that apply unconditionally to every
target. A section whose content depends on what the user actually chose to
install (e.g. "Further Reading", which must list only the companion READMEs
that were copied) does **not** belong there — a fixed version of it would
get merged into every target regardless of what's actually on disk,
producing dead links.

Instead, generate that section's content at the point the choice is made and
merge it with `apply-template.sh` against a small temp template file built
for that run (see `scripts/write-further-reading.sh` for the pattern: build
one section's marker block into a temp file, then call `apply-template.sh
<temp-file> <target> [--apply]`). Skip the merge entirely if the user's
choice was empty — never fall back to listing all options as if they were
installed.
