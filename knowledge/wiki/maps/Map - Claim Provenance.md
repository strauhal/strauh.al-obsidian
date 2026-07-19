---
title: Map - Claim Provenance
type: map
aliases: [Claim Provenance, Provenance Model, Epistemic Integrity]
tags: [map, provenance, epistemology, maintenance, brain]
claim_schema: "1"
created: 2026-07-19
updated: 2026-07-19
---

# Map - Claim Provenance

**A trust model for claims made by the vault and by [[brain|strauh.al/brain]].** The archive
contains primary material, later recollection, secondary criticism, generated synthesis,
and inference. Those layers must remain distinguishable so repetition does not turn an
interpretation into an apparent fact.

## Required claim record

Curated analytical notes using `claim_schema: "1"` record each substantive claim inside
`<!-- claim:start -->` and `<!-- claim:end -->`. Every block retains:

- **Source type** — raw self-report, secondary criticism, generated synthesis, inference,
  or an explicit mixture.
- **Claim date** — when the interpretation entered the vault, not the date of the event.
- **Confidence** — high, moderate, or low.
- **Evidence** — direct links to the smallest useful set of sources.
- **Contradictions** — disconfirming evidence, competing readings, or known limits.
- **Retrospective editing** — whether the source was later revised, pruned, compiled, or
  remembered after the fact.
- **Derivation** — whether apparently separate notes are independent evidence or descend
  from the same original passage.

`tools/wiki_claim_provenance.py` validates the schema and writes
`knowledge/output/claim-provenance-report.md` during a full vault refresh.

## Trust order

1. **Contemporaneous primary material** — dated diary entries, source files, code, and
   surviving artifacts. Strongest for what was written or built; still not transparent
   access to motive.
2. **Later direct self-report** — useful testimony, but vulnerable to reconstruction and
   present-day narrative.
3. **Secondary criticism** — evidence about reception and interpretation, not automatic
   authority over Ernest's intention.
4. **Generated synthesis** — useful for navigation and hypothesis formation; never an
   independent confirmation of the material it summarizes.
5. **Inference** — a proposed relation that must retain uncertainty and counterevidence.

## Independence rule

Ten notes quoting one diary sentence count as one source. A concept note, map, chatbot
reply, and memory summary that all descend from the same passage do not provide fourfold
corroboration. Independence is established by separate primary events, artifacts, or
observers.

## Editing rule

The [[Autofiction|diary]] identifies itself as narrativized and records that entries were
pruned. It is therefore primary evidence for the language and self-understanding present
in the saved version, but not an unedited transcript of the original moment.

<!-- claim:start -->
### Claim: provenance is part of the content, not administrative decoration
- **Source type:** generated synthesis and inference
- **Claim date:** 2026-07-19
- **Confidence:** high
- **Evidence:** [[Autofiction]]; [[The Archive as Consciousness]]; [[knowledge/raw/diary|raw diary]]; [[ChatGPT Memory Summary]]
- **Contradictions:** Added metadata cannot eliminate interpretation, and highly granular provenance can make ordinary reading cumbersome.
- **Retrospective editing:** This policy was added after the vault had already accumulated generated notes and crosslinks.
- **Derivation:** The claim synthesizes the diary's explicit narrativization, the imported-memory trust warning, and the archive's generated layers; those sources overlap but are not identical.
<!-- claim:end -->

## Connections

- [[Psychological Architecture]] — the first analysis note fully using this schema.
- [[Recursive Myth-Making]] — the failure mode this map is designed to prevent.
- [[Map - ChatGPT Memory]] — an existing model for separating imported synthesis from
  confirmed biography.
- [[Map - Maintenance]] — provenance validation belongs in recurring maintenance.
- [[The Archive as Consciousness]] — a second memory requires an explicit trust model.

<!-- vault-crosslinks:start -->
## Discovered Connections

- [[knowledge/wiki/maps/Map - ChatGPT Conversations|Map - ChatGPT Conversations]] — named in this note
- [[knowledge/wiki/books/narrative|Narrative]] — named in this note
- [[knowledge/wiki/concepts/Curated Disorder|Curated Disorder]] — shared language: evidence, rule, independent
- [[knowledge/wiki/concepts/Recognition Through Shared Objects|Recognition Through Shared Objects]] — shared language: evidence, confidence
- [[knowledge/wiki/works/The Record Label|The Record Label]] — shared language: record, diary, start
- [[knowledge/wiki/works/strauh.al Archive|strauh.al Archive]] — shared language: memory, diary, maintenance
- [[knowledge/wiki/life/Beliefs and Temperament|Beliefs and Temperament]] — shared language: inference, diary, self-report
- [[knowledge/wiki/maps/Map - Ernest Creative Profile|Map - Ernest Creative Profile]] — shared language: memory, chatgpt, summary
<!-- vault-crosslinks:end -->
