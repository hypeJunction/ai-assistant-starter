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
