---
name: research
description: Ethical web research with attribution tracking, license compliance, and citation-based output. Use for technical research, competitive analysis, or content synthesis requiring source transparency.
category: process
model: sonnet
effort: medium
triggers:
  - research topic
  - find information
  - web research
  - cite sources
  - license check
  - attribution
---

# Research

> **Purpose:** Conduct web research ethically with proper attribution and license compliance.
> **Mode:** Read-only output — produces cited research, does not modify project files.
> **Usage:** `/research [flags] <topic or question>`

## Iron Laws

1. **NEVER PRESENT UNCITED CLAIMS** — Every factual assertion must trace to a specific source. If the source is unknown, say "unverified" rather than omitting attribution.

2. **RESPECT ACCESS BOUNDARIES** — Do not use content from sources that explicitly prohibit AI access (robots.txt disallow, Terms of Service restrictions). If a source is inaccessible, note it and find an alternative.

3. **LICENSE DETERMINES USE** — Code snippets and creative content carry licenses. Permissive (MIT, Apache, BSD) may be adapted with attribution. Copyleft (GPL, AGPL) requires disclosure. Unknown license means "do not copy verbatim." See `references/license-detection.md`.

4. **FACTS ARE FREE, EXPRESSION IS NOT** — Facts, data, and ideas are not copyrightable. The specific wording, structure, and creative expression used to present them are. Always paraphrase and synthesize rather than copying prose.

5. **PROVENANCE OVER CONVENIENCE** — When two sources conflict, prefer the one with clearer provenance (official docs > blog post). When a source cannot be verified, flag it rather than silently including it.

6. **NO MARKET SUBSTITUTION** — Research output must not substitute for visiting or purchasing the original source. Summarize and link; do not reproduce.

7. **ATTRIBUTE CC-BY CONTENT** — Creative Commons Attribution (CC-BY) licensed content requires explicit attribution with author, title, source URL, and license. This is a legal obligation, not optional.

## When to Use

- Technical research before implementation decisions
- Technology or library comparison with license analysis
- Finding best practices, standards, or specifications
- Investigating library options with license requirements
- Synthesizing documentation from multiple sources
- Checking license compatibility for a dependency

## When NOT to Use

- Codebase exploration → use `/explore`
- Bug investigation → use `/debug`
- Security assessment → use `/security-review`
- Questions answerable from project context alone → use `/explore`

## Scope Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--depth=<quick\|standard\|deep>` | Research depth | `standard` |
| `--format=<summary\|report\|comparison>` | Output format | `summary` |
| `--license-check` | Focus on license analysis for specific libraries/content | off |

## Content Classification

| Category | Copyright Status | Handling |
|----------|-----------------|----------|
| **Facts and data** | Not copyrightable | Freely usable; cite for credibility |
| **Standards and specs** | Varies (often CC-BY) | Check license; attribute if required |
| **Code snippets** | License-dependent | Classify per `references/license-detection.md` |
| **Creative expression** | Protected | Paraphrase and synthesize; never copy verbatim |
| **Public domain / CC0** | Not protected | Freely usable; cite for provenance |

## Confidence Levels

| Level | Criteria | Handling |
|-------|----------|----------|
| **HIGH** | Primary source, official documentation, peer-reviewed | Present as established fact |
| **MEDIUM** | Reputable secondary source, well-maintained blog, verified community answer | Present with source qualification |
| **LOW** | Single unverified source, personal blog, outdated content | Flag as unverified; seek corroboration |

## Workflow

### Phase 1: Scope

1. Parse the research question — what specifically needs answering?
2. Classify the research type:
   - **Factual lookup** — quick answer from authoritative source
   - **Comparison** — structured evaluation of alternatives
   - **Deep research** — comprehensive analysis with multiple perspectives
   - **License check** — focused license and compliance analysis
3. Select depth level based on `--depth` flag or question complexity
4. Identify relevant source types: official docs, specs, RFCs, code repos, articles

### Phase 2: Gather

For each source accessed:

1. **Record provenance:**
   - URL, title, author/organization, publication date
   - License (if stated — check footer, LICENSE file, meta tags)
   - Access method and any restrictions observed
2. **Classify content type** per the Content Classification table above
3. **Check access boundaries:**
   - Was this content behind a paywall or login? → Do not use
   - Does the site's ToS prohibit AI use? → Note and find alternative
4. For code: identify license using the detection order in `references/license-detection.md`
5. Cross-reference claims across multiple sources when possible

### Phase 3: Analyze

1. **Synthesize** — paraphrase and combine findings; never copy prose verbatim
2. **Resolve conflicts** using source hierarchy:
   - Primary/official documentation
   - Reputable secondary sources
   - Community sources (Stack Overflow, blog posts)
3. **License classification** for any code to be included:
   - Run through `references/license-detection.md` classification
   - Determine obligations: attribution, notice, share-alike, or prohibited
4. **Assign confidence levels** to each finding

### Phase 4: Cite and Verify

Run the compliance checklist from `references/compliance-checklist.md`:

- [ ] Every factual claim has a source
- [ ] No verbatim copying of creative expression
- [ ] Code snippets have license classification
- [ ] CC-BY content has proper attribution (see `references/citation-formats.md`)
- [ ] Copyleft code flagged with obligations, not silently included
- [ ] Source access boundaries were respected
- [ ] Output does not substitute for visiting original sources

### Phase 5: Output

Format based on `--format` flag:

#### Summary (default)

```
## [Topic]

[Synthesized findings with inline citations [1][2]...]

### Sources

| # | Source | Author/Org | Date | License | Confidence |
|---|--------|------------|------|---------|------------|
| [1] | [Title](URL) | Author | Date | License | HIGH/MED/LOW |
```

#### Report

```
## [Topic]

### Background
[Context and scope]

### Findings
[Structured sections with inline citations]

### Analysis
[Synthesis, trade-offs, recommendations]

### Sources
[Full source table as above]

### License Obligations
[Only if code or CC-BY content included — what the consumer must do]
```

#### Comparison

```
## [Topic]: Comparison

| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| [aspect] | [value] [1] | [value] [2] | [value] [3] |

### Recommendation
[Based on findings]

### Sources
[Full source table]
```

All formats end with a **Sources** table and, when applicable, a **License Obligations** section listing what the consumer must do with any included licensed content.

## Quick Reference

| Task | Command |
|------|---------|
| Quick lookup | `/research --depth=quick what is X` |
| Compare technologies | `/research --format=comparison React vs Vue vs Svelte` |
| Check a library's license | `/research --license-check lodash` |
| Deep technical report | `/research --depth=deep --format=report state of WebAssembly` |

## Acceptance Tests

| ID | Type | Prompt / Condition | Expected |
|----|------|--------------------|----------|
| RES-T1 | Positive | "Research best practices for caching" | Skill triggers |
| RES-T2 | Positive | "Find information about WebSocket libraries" | Skill triggers |
| RES-T3 | Positive | "What license does lodash use" | Skill triggers |
| RES-T4 | Positive | "Compare X vs Y" | Skill triggers |
| RES-T5 | Negative | "How does our auth module work?" | Does NOT trigger → /explore |
| RES-T6 | Negative | "Fix this bug" | Does NOT trigger → /debug |
| RES-T7 | Boundary | "Research and then implement X" | Triggers for research phase only |
