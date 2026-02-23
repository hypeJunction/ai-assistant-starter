# Citation Formats

Templates for attributing sources in research output. Load when producing the Sources table or including licensed content.

## Inline Citations

Use numbered references in square brackets within text:

```
WebAssembly supports streaming compilation [1], which allows browsers
to begin compiling while still downloading [2].
```

Numbers correspond to rows in the Sources table.

## Sources Table Format

Every research output ends with this table:

```markdown
| # | Source | Author/Org | Date | License | Confidence |
|---|--------|------------|------|---------|------------|
| [1] | [Title](URL) | Author or Organization | YYYY-MM | License ID or "Not stated" | HIGH/MED/LOW |
```

**Rules:**
- Order by first appearance in text
- Date: use `YYYY-MM` if exact day unknown; `YYYY` if month unknown
- License: use SPDX identifier when possible (MIT, Apache-2.0, CC-BY-4.0)
- If license not determinable, write "Not stated"
- Confidence reflects source reliability, not agreement with findings

## CC-BY Attribution (Legally Required)

When including or adapting content from CC-BY licensed sources, attribution is a legal obligation. Use this format:

```markdown
> Based on [Title](URL) by [Author/Organization],
> licensed under [CC BY X.0](https://creativecommons.org/licenses/by/X.0/).
```

**Requirements (all four must be present):**
1. Title of the original work
2. Author or organization name
3. Link to the source
4. License name with link to license text

**CC-BY-SA (ShareAlike):** Same attribution requirements plus: if the output is shared publicly, it must use the same CC-BY-SA license.

## Code Attribution

When including code from open source projects:

### Permissive (MIT, Apache-2.0, BSD)

```markdown
// From [project-name](URL), [license]. Copyright [year] [author].
```

Or in the License Obligations section:

```markdown
### License Obligations
- Code snippet in [section] adapted from [project](URL) under MIT license.
  Copyright notice: "Copyright (c) [year] [author]"
```

### Copyleft (GPL, AGPL)

Do not include copyleft code directly. Instead:

```markdown
**Note:** [project](URL) is licensed under GPL-3.0. The approach described
above is inspired by their implementation but uses original code to avoid
copyleft obligations. See the original for reference.
```

## RFC / Specification Citations

```markdown
| [N] | [RFC NNNN: Title](https://www.rfc-editor.org/rfc/rfcNNNN) | IETF | YYYY-MM | IETF Trust | HIGH |
```

For W3C specifications:

```markdown
| [N] | [Spec Title](URL) | W3C | YYYY-MM | W3C Document License | HIGH |
```

## When Attribution Is NOT Required

- **Common knowledge:** "HTTP uses port 80 by default" — no citation needed
- **Project-internal facts:** information from the codebase being worked on
- **Mathematical or logical facts:** "O(n log n) is the lower bound for comparison sorting"
- **CLI usage or syntax:** `git commit -m "message"` — standard tool usage

When in doubt, cite. Over-attribution is harmless; under-attribution carries legal risk.
