# License Detection

Rules for identifying and classifying licenses on code and content encountered during research.

## Detection Order

Check these locations in order (first match wins):

1. `LICENSE` or `LICENCE` file in repository root
2. `license` field in `package.json` (npm) or equivalent manifest
3. SPDX license identifier in file headers
4. License section in `README.md`
5. License badge in `README.md`
6. Repository metadata (GitHub "About" sidebar, PyPI classifiers)

If none found → classify as **Unknown / All Rights Reserved**.

## License Classification

### Permissive (Low Risk)

| License | SPDX ID | Can Adapt | Requirements |
|---------|---------|-----------|--------------|
| MIT | MIT | Yes | Retain copyright notice and license text |
| Apache 2.0 | Apache-2.0 | Yes | Retain notice, state changes, patent grant |
| BSD 2-Clause | BSD-2-Clause | Yes | Retain copyright notice and license text |
| BSD 3-Clause | BSD-3-Clause | Yes | Above + no endorsement clause |
| ISC | ISC | Yes | Retain copyright notice |
| Unlicense | Unlicense | Yes | None (public domain dedication) |

### Weak Copyleft (Medium Risk)

| License | SPDX ID | Can Adapt | Requirements |
|---------|---------|-----------|--------------|
| LGPL 2.1 | LGPL-2.1-only | File-level | Modified files must stay LGPL; linking permitted |
| LGPL 3.0 | LGPL-3.0-only | File-level | Same as 2.1 with additional patent provisions |
| MPL 2.0 | MPL-2.0 | File-level | Modified files must stay MPL; new files can differ |
| EPL 2.0 | EPL-2.0 | Module-level | Derivative modules must stay EPL or compatible |

### Strong Copyleft (High Risk)

| License | SPDX ID | Can Adapt | Requirements |
|---------|---------|-----------|--------------|
| GPL 2.0 | GPL-2.0-only | Project-level | Entire derivative work must use GPL |
| GPL 3.0 | GPL-3.0-only | Project-level | Same + patent grant + anti-tivoization |
| AGPL 3.0 | AGPL-3.0-only | Project-level | GPL-3.0 + network use triggers distribution |

**Handling:** Do not include GPL/AGPL code in output. Describe the approach conceptually and link to the source.

### Creative Commons

| License | SPDX ID | Can Adapt | Requirements |
|---------|---------|-----------|--------------|
| CC0 1.0 | CC0-1.0 | Yes | None (public domain) |
| CC BY 4.0 | CC-BY-4.0 | Yes | Attribution required (author, title, URL, license) |
| CC BY-SA 4.0 | CC-BY-SA-4.0 | Yes | Attribution + share under same license |
| CC BY-NC 4.0 | CC-BY-NC-4.0 | Non-commercial only | Attribution + non-commercial use only |
| CC BY-ND 4.0 | CC-BY-ND-4.0 | No | No derivatives allowed — do not adapt |

### No License / Unknown

| Scenario | Handling |
|----------|----------|
| No license file or statement found | Assume All Rights Reserved — do not copy |
| "All Rights Reserved" stated | Do not copy; paraphrase concepts only |
| Contradictory license statements | Use the more restrictive interpretation |

## Compatibility with MIT Projects

When the consuming project uses MIT license:

| Source License | Compatible? | Notes |
|----------------|-------------|-------|
| MIT, BSD, ISC, Unlicense | Yes | Include with attribution |
| Apache-2.0 | Yes | Include with attribution + notice |
| CC0, CC-BY | Yes | CC-BY requires attribution |
| LGPL | Conditional | OK for linking; modifications must stay LGPL |
| MPL-2.0 | Conditional | Modified MPL files stay MPL; new files OK |
| CC-BY-SA | No | ShareAlike infects the whole work |
| CC-BY-NC | No | Commercial use prohibited |
| GPL, AGPL | No | Copyleft incompatible with MIT |

## Red Flags

Stop and flag these to the user:

- **No license at all** — legally "All Rights Reserved" by default
- **Custom or non-standard license** — needs manual review
- **AGPL in a SaaS context** — network use triggers full source disclosure
- **License changed between versions** — verify which version is in use
- **Dual-licensed code** — clarify which license applies to the use case
- **"Fair use" as justification for copying** — fair use is a legal defense, not a permission; do not rely on it for code
