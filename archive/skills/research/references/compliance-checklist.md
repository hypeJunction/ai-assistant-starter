# Compliance Checklist

Run this checklist before delivering research output. Every item must pass or be explicitly noted as an exception.

## 1. Source Access

- [ ] **robots.txt respected** — Did not access content from URLs disallowed by robots.txt
- [ ] **Terms of Service respected** — No content from sites whose ToS prohibit AI use
- [ ] **No paywalled content** — Did not bypass paywalls, logins, or access controls
- [ ] **No pirated content** — All sources are legitimate (not mirrors of copyrighted content)

## 2. Attribution

- [ ] **Every claim has a source** — No unsourced factual assertions in the output
- [ ] **CC-BY content attributed** — All Creative Commons Attribution content has: author, title, URL, and license link (see `citation-formats.md`)
- [ ] **CC-BY-SA obligations noted** — If CC-BY-SA content was used, ShareAlike requirement is disclosed in License Obligations section
- [ ] **Code attribution present** — Code snippets include project name, URL, and license

## 3. Content Use

- [ ] **No verbatim prose** — Creative expression has been paraphrased, not copied
- [ ] **No market substitution** — Output summarizes and links; does not replace the need to visit original sources
- [ ] **Copyleft code excluded** — GPL/AGPL code is not included directly; concepts are described with links to originals
- [ ] **Unknown-license code excluded** — Code without identifiable license is not reproduced verbatim
- [ ] **Facts distinguished from opinion** — Factual claims separated from editorial analysis

## 4. Output Format

- [ ] **Sources table present** — Research output ends with a complete Sources table
- [ ] **License Obligations section** — Present if any licensed content (code or CC-BY) was included
- [ ] **Confidence levels assigned** — Each finding has HIGH/MEDIUM/LOW confidence rating
- [ ] **Dates included** — Sources include publication dates for currency assessment

## 5. Special Cases

### License Check Mode (`--license-check`)

Additional items when the research focuses on license analysis:

- [ ] **License detected from primary source** — Checked LICENSE file, package manifest, or repo metadata (not just a blog post about the project)
- [ ] **Version-specific** — License identified for the specific version in question
- [ ] **Compatibility assessed** — If the consumer's project license is known, compatibility is evaluated

### Deep Research Mode (`--depth=deep`)

Additional items for comprehensive research:

- [ ] **Multiple sources per claim** — Key findings corroborated by 2+ independent sources
- [ ] **Recency check** — Sources are current (within 2 years) or staleness is noted
- [ ] **Conflicting views represented** — Significant disagreements among sources are noted, not hidden
