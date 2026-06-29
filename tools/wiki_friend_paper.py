#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
RAW = VAULT / "knowledge" / "raw"
PAPERS = RAW / "papers"
WIKI = VAULT / "knowledge" / "wiki"
SOURCES = WIKI / "sources"
WORKS = WIKI / "works"
CONCEPTS = WIKI / "concepts"
MAPS = WIKI / "maps"
ATTACHMENT = Path(
    "/Users/erneststrauhal/.codex/attachments/"
    "142bb7df-0c88-4413-beef-129456a84ed2/pasted-text.txt"
)
RAW_TEXT = PAPERS / "no-more-human-art.txt"


def source_text() -> str:
    if ATTACHMENT.exists():
        text = ATTACHMENT.read_text(errors="ignore").strip()
        PAPERS.mkdir(parents=True, exist_ok=True)
        RAW_TEXT.write_text(text + "\n")
        return text
    if RAW_TEXT.exists():
        return RAW_TEXT.read_text(errors="ignore").strip()
    raise SystemExit("No More Human Art source text is unavailable.")


def write_raw_note(text: str) -> None:
    today = dt.date.today().isoformat()
    body = f"""---
title: No More Human Art
slug: no-more-human-art
type: secondary-source
author: Ben Read
subject: Ernest Strauhal
ingested: {today}
compiled: true
tags: [raw, criticism, ai-art, gan]
---

# No More Human Art

**Full title:** No More Human Art: Ernest Strauhal and the Use of Generative Adversarial Networks in Artistic Production

**Author:** Ben Read

This is a secondary source written by a friend about Ernest's work. Its descriptions and interpretations belong to the author unless independently corroborated.

## Original Text

{text}
"""
    (RAW / "no-more-human-art.md").write_text(body)


def write_criticism_note() -> None:
    today = dt.date.today().isoformat()
    body = f"""---
title: No More Human Art - Source Essay
type: criticism
author: Ben Read
subject: Ernest Strauhal
status: compiled
tags: [criticism, ai-art, gan, authorship]
sources: []
created: {today}
updated: {today}
---

# No More Human Art

Ben Read's essay examines Ernest's use of Pix2Pix and StyleGAN as a way of testing authorship, control, and generated time rather than merely automating image production.

## Argument

Read places Ernest's practice against public anxiety about artificial intelligence in art. The essay argues that the work matters because it stages a visible negotiation between hand, dataset, algorithm, and editorial judgment.

The central sequence is:

1. Ernest produces a drawing, movement, voice recording, or personal dataset.
2. A GAN introduces outputs that can be directed but not fully predicted.
3. Ernest edits, accepts, rejects, sequences, or reframes those outputs.

Read calls this relation a [[Human-Machine Tug of War]]. The machine is collaborator and exterior force, but the finished work remains subject to Ernest's aesthetic judgment.

## Works Discussed

- [[GAN Color Studies]] - line drawings colorized through Pix2Pix and edited afterward.
- [[Vocal Study 3]] - body and voice returned as an uncanny generated continuation.
- [[Untitled 15 - Dynamic Color Study 1]] - line drawing transformed into looping generated color.
- [[Implicit Distance]] and [[Video Portraiture]] - adjacent works already represented in the vault.

## Concepts

- [[Human-Machine Tug of War]] - temporary relinquishment and recovery of control.
- [[Dead Architecture]] - generated motion as predetermined pixel change that resembles living duration.
- [[Latent Space]] - personal images and bodily attributes reorganized as navigable model space.
- [[AI Slop]] - the broader tension between critical suspicion and active machine-assisted practice.
- [[Spontaneity and Elegance]] - a productive contrast between human trace and generated cleanliness.

## Attribution Boundary

The essay reports statements attributed to Ernest, including descriptions of GAN collaboration as a tug of war, generated video as dead architecture, and AI output as clean art without human imperfection. These are retained as reported statements until a transcript or first-person source is added.

## Source

The complete supplied text is preserved at `knowledge/raw/no-more-human-art.md`, with a plain-text preservation copy at `knowledge/raw/papers/no-more-human-art.txt`.
"""
    SOURCES.mkdir(parents=True, exist_ok=True)
    (SOURCES / "No More Human Art.md").write_text(body)


def write_work_notes() -> None:
    today = dt.date.today().isoformat()
    notes = {
        "GAN Color Studies.md": f"""---
title: GAN Color Studies
type: work
aliases: [Untitled 4 Color Study 1, Pix2Pix color studies]
tags: [work, drawing, pix2pix, gan, color]
sources: ["[[No More Human Art]]", "[[ideas-sketchbook]]"]
created: {today}
updated: {today}
---

# GAN Color Studies

A drawing-to-model-to-editing process described by Ben Read: Ernest builds geometric line drawings by following an initial contour with successive semi-parallel lines, sends the drawing through Pix2Pix for colorization, then adjusts the output through color correction and editorial judgment.

## Example

- **Untitled 4** (2022) - the unmanipulated line drawing.
- **Untitled 4 (Color Study 1)** (2023) - the edited Pix2Pix output.

## Significance

The process makes authorship sequential rather than singular. Hand drawing establishes structure, the model introduces partially unpredictable color, and editing returns the result to Ernest's judgment.

## Connections

- [[Human-Machine Tug of War]]
- [[AI Slop]]
- [[Spontaneity and Elegance]]
- [[Latent Space]]
- [[No More Human Art]]
""",
        "Vocal Study 3.md": f"""---
title: Vocal Study 3
type: work
year: 2024
tags: [work, video, voice, stylegan, gan, self-portrait]
sources: ["[[No More Human Art]]"]
created: {today}
updated: {today}
---

# Vocal Study 3

A 2024 work described by Ben Read in which recordings of Ernest's movement and voice are processed through StyleGAN, producing an algorithmic continuation of embodied source material.

Read frames the result as an uncanny doppelganger: voice, body, and movement remain recognizable while escaping direct control. The work is therefore less a synthetic portrait than a negotiation over who or what may continue a person.

## Connections

- [[Video Portraiture]]
- [[kits.ai Voice]]
- [[Human-Machine Tug of War]]
- [[Dead Architecture]]
- [[Latent Space]]
- [[No More Human Art]]
""",
        "Untitled 15 - Dynamic Color Study 1.md": f"""---
title: Untitled 15 - Dynamic Color Study 1
type: work
year: 2023
tags: [work, video, drawing, stylegan, color]
sources: ["[[No More Human Art]]"]
created: {today}
updated: {today}
---

# Untitled 15 - Dynamic Color Study 1

A 2023 work described by Ben Read that carries the line-based color studies into time: generated colors move through a looping pattern rather than settling into a static image.

## Connections

- [[GAN Color Studies]]
- [[Dead Architecture]]
- [[Video Portraiture]]
- [[Implicit Distance]]
- [[No More Human Art]]
""",
    }
    WORKS.mkdir(parents=True, exist_ok=True)
    for filename, body in notes.items():
        (WORKS / filename).write_text(body)


def write_concept_notes() -> None:
    today = dt.date.today().isoformat()
    notes = {
        "Human-Machine Tug of War.md": f"""---
title: Human-Machine Tug of War
type: concept
aliases: [tug of war, machine collaboration, negotiated authorship]
tags: [concept, ai-art, authorship, control]
sources: ["[[No More Human Art]]"]
created: {today}
updated: {today}
---

# Human-Machine Tug of War

Ben Read's term for the movement of control in Ernest's GAN-assisted work: the artist establishes source material and conditions, the model produces additions that cannot be completely predicted, and editorial judgment accepts, alters, or rejects the result.

The machine is neither an autonomous author nor a neutral brush. It is a temporarily empowered collaborator whose agency is bounded by the larger artistic process.

## Connections

- [[GAN Color Studies]]
- [[Vocal Study 3]]
- [[AI Slop]]
- [[Latent Space]]
- [[Spontaneity and Elegance]]
- [[No More Human Art]]
""",
        "Dead Architecture.md": f"""---
title: Dead Architecture
type: concept
aliases: [dead digital space, illusion of movement]
tags: [concept, video, time, space, gan]
sources: ["[[No More Human Art]]"]
created: {today}
updated: {today}
---

# Dead Architecture

Ben Read reports Ernest describing generated video as “dead architecture with the illusion of movement.” The phrase names a paradox: a model produces apparent motion from predetermined transitions and interpolated data, creating duration without a newly performed event.

The generated body seems to move, but the motion is a pixel structure assembled from traces of prior movement. This makes time inside the work feel simultaneously fluid and already completed.

## Connections

- [[Vocal Study 3]]
- [[Untitled 15 - Dynamic Color Study 1]]
- [[Implicit Distance]]
- [[Video Portraiture]]
- [[Latent Space]]
- [[No More Human Art]]
""",
    }
    CONCEPTS.mkdir(parents=True, exist_ok=True)
    for filename, body in notes.items():
        (CONCEPTS / filename).write_text(body)


def write_map() -> None:
    today = dt.date.today().isoformat()
    body = f"""---
title: Map - Writing About Ernest
type: map
tags: [map, criticism, secondary-sources]
created: {today}
updated: {today}
---

# Map - Writing About Ernest

Secondary writing about Ernest's work. Interpretations remain attributed to their authors and are not silently converted into first-person biography.

## Essays

- [[No More Human Art - Source Essay|No More Human Art]] - Ben Read on GANs, authorship, control, and generated temporality.

## Works Identified

- [[GAN Color Studies]]
- [[Vocal Study 3]]
- [[Untitled 15 - Dynamic Color Study 1]]

## Concepts Introduced

- [[Human-Machine Tug of War]]
- [[Dead Architecture]]
"""
    MAPS.mkdir(parents=True, exist_ok=True)
    (MAPS / "Map - Writing About Ernest.md").write_text(body)


def update_registry() -> None:
    path = RAW / "_sources.md"
    text = path.read_text(errors="ignore")
    if "| no-more-human-art |" not in text:
        text = text.rstrip() + f"\n| no-more-human-art | criticism | {dt.date.today().isoformat()} | true |\n"
        path.write_text(text)


def main() -> None:
    text = source_text()
    write_raw_note(text)
    write_criticism_note()
    write_work_notes()
    write_concept_notes()
    write_map()
    update_registry()
    print("Integrated No More Human Art and its work/concept links.")


if __name__ == "__main__":
    main()
