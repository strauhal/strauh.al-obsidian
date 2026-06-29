#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
CHATGPT = VAULT / "knowledge" / "wiki" / "chatgpt"
MAPS = VAULT / "knowledge" / "wiki" / "maps"
SUMMARY = CHATGPT / "Memory Summary.md"


def write_profile() -> None:
    today = dt.date.today().isoformat()
    body = f"""---
title: Map - Ernest Creative Profile
type: map
status: synthesized
tags: [map, profile, creative-practice, chatgpt-memory]
sources: ["[[ChatGPT Memory Summary]]", "[[about]]", "[[diary]]", "[[influences]]"]
created: {today}
updated: {today}
---

# Map - Ernest Creative Profile

A working profile synthesized from ChatGPT's memory summary and linked back into Ernest's own archive. ChatGPT's wording is evidence about prior conversations, not an authority over Ernest's identity.

## Working Description

Ernest is an artist, musician, teacher, writer, and toolmaker whose practice moves between drawing, sound, text, philosophy, archives, and software. The recurring ambition is not simply to work in many media, but to let each medium become a way of thinking through the others.

## Creative Practice

- [[Spontaneity and Elegance]] - drawing and the sketch as thought with minimal delay.
- [[strauh.al Archive]] - personal image archive and externalized consciousness.
- [[Memory and Preservation]] - diary, photography, web archives, and collected images as memory technologies.
- [[Dreams Series]] and [[Video Portraiture]] - examples of image, duration, process, and altered attention crossing media.
- [[Implicit Distance]] - music as another site where texture, structure, and memory meet.

ChatGPT also remembers an ongoing book combining diary entries and notebook drawings from roughly 2024-2026, plus work in watercolor, gouache, paint pens, technical pens, instant photography, audio, video, and digital publishing.

## Teaching

The memory summary describes visual-art teaching, piano teaching, bilingual communication with families, and a proposed course titled **Drawing as Total Practice**. That course idea closely matches the archive's existing aesthetic: drawing as a foundational activity that can extend into music, writing, video, and software.

## Music

- [[Map - Current Listening]] - the current listening field.
- [[Alexander Scriabin]], [[Ryuichi Sakamoto]], [[Playboi Carti]], and [[Tim Hecker]] - already represented influence nodes.
- [[Spontaneity and Elegance]] - the preference for piano works and sketches as relatively unfiltered traces of thought.
- [[Listening - Playing the Piano 12122020|Playing the Piano 12122020]] and the broader piano queue.

ChatGPT remembers sustained study of piano technique, improvisation, composition, sight-reading, memory, modes, chromaticism, harmonic function, pedal tones, and rhythm.

## Philosophy and Reading

- [[Map - Current Reading]]
- [[Map - Reading Constellations]]
- [[Albert Camus]], [[Charles Baudelaire]], and [[Marcel Proust]]
- [[The Internet as Confidant]], [[The Oedipal Screen]], and [[The Attention Economy]]

The remembered intellectual field centers on phenomenology, continental philosophy, psychoanalysis, aesthetics, media theory, technology, and modernity, approached through detailed questions tied back to ordinary creative practice.

## Total Practitioners

The memory summary notices a consistent attraction to creators who cross disciplinary boundaries rather than remaining specialists. Existing influence nodes include [[Barry McGee]], [[Egon Schiele]], [[Clyfford Still]], [[Rei Kawakubo]], [[Wassily Kandinsky]], and [[Ryuichi Sakamoto]].

## Tools as Creative Thought

- [[SEEKER]] - archive browsing as a creative instrument.
- [[kits.ai Voice]] - identity, tools, and reproducibility.
- [[AI Slop]] and [[Latent Space]] - critical engagement with generative systems.
- [[The Internet as Confidant]] - software and networks as psychic as well as technical infrastructure.

ChatGPT remembers interest in Ableton, Premiere Pro, Pages, image generation, language models, e-paper, Raspberry Pi systems, audio formats, interfaces, and publishing workflows. The through-line is artistic affordance rather than technical novelty alone.

## Provenance

- [[ChatGPT Memory Summary]] - verbatim supplied memory synthesis.
- [[ChatGPT Memory Review]] - details still needing confirmation or qualification.
- [[Map - ChatGPT Memory]] - import and trust model.
"""
    MAPS.mkdir(parents=True, exist_ok=True)
    (MAPS / "Map - Ernest Creative Profile.md").write_text(body)


def write_review() -> None:
    today = dt.date.today().isoformat()
    body = f"""---
title: ChatGPT Memory Review
type: review-queue
status: needs-review
tags: [chatgpt, memory, profile, review]
sources: ["[[ChatGPT Memory Summary]]"]
created: {today}
updated: {today}
---

# ChatGPT Memory Review

Claims from ChatGPT's memory synthesis that are specific, potentially time-sensitive, or not yet clearly corroborated by Ernest's existing source material.

## Confirmed or Strongly Corroborated

- [x] Born October 15, 2000. The date appears in [[diary]].
- [x] strauh.al is a personal art and image archive. See [[about]] and [[strauh.al Archive]].
- [x] Cross-disciplinary influences include Scriabin, Chopin, Arca, King Crimson, Massive Attack, Ryuichi Sakamoto, Camus, Baudelaire, Proust, and others. See [[influences]].
- [x] Piano, drawing, archives, philosophy, and technology are recurring concerns across the diary, ideas, cultural queues, and works.

## Confirm or Update

- [ ] Current teaching roles and the preferred language for describing the students served.
- [ ] Current use or ownership of computerdrawing.club.
- [ ] Status and intended form of the 2024-2026 diary and notebook book project.
- [ ] Status of the Sacramento State Studio Art / Drawing Lecturer application.
- [ ] Whether **Drawing as Total Practice** should become a dedicated work or teaching-project note.
- [ ] Current software and hardware setup, including the 37-key MIDI keyboard.
- [ ] Birthplace in San Francisco and childhood move to the Sacramento area.
- [ ] Elliot Ranch Elementary, Elizabeth Pinkerton Middle School, and West Campus High School.
- [ ] California College of the Arts design acceptance in 2018.
- [ ] School of the Art Institute of Chicago graduate-program acceptance in 2022.
- [ ] Exhibitions in New York and Chicago.
- [ ] Music-performance and release history.
- [ ] Chinese family ancestry and the railroad-era San Francisco history.

## Editorial Notes

- ChatGPT used the phrase “handicapped children and adults.” Confirm Ernest's preferred current language before carrying that wording into a public biography.
- “Currently” is fragile metadata. Roles, tools, applications, and projects should receive dates when confirmed.
- This review note is intentionally private-facing and should not be treated as publishable biography.
"""
    CHATGPT.mkdir(parents=True, exist_ok=True)
    (CHATGPT / "Memory Review.md").write_text(body)


def main() -> None:
    if not SUMMARY.exists() or "status: awaiting-input" in SUMMARY.read_text(errors="ignore"):
        print("ChatGPT memory summary is not available yet; skipped profile compilation.")
        return
    write_profile()
    write_review()
    print("Compiled ChatGPT memory into a creative profile and review queue.")


if __name__ == "__main__":
    main()
