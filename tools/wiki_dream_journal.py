#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
RAW = VAULT / "knowledge" / "raw"
WIKI = VAULT / "knowledge" / "wiki"
DREAMS = WIKI / "dreams"
MAPS = WIKI / "maps"
DEFAULT_SOURCE = Path(
    "/Users/erneststrauhal/.codex/attachments/"
    "01268b3b-1e7d-420e-936a-0359eb4fe9d6/pasted-text.txt"
)


ENTRIES = [
    {
        "number": 1,
        "title": "The Palantir Panel Outside Target",
        "motifs": ["exposure", "evaluation", "work", "graphic design", "voice"],
        "summary": (
            "Naked except for a bath towel outside Target, Ernest attempts an uncanny "
            "Palantir application amid bottles, trash, strange typography, and a panel "
            "asking about obscure musicians and critical theorists. Congestion gives "
            "him an Alan Rickman voice, which he calls out himself."
        ),
        "links": ["The Attention Economy", "The Internet as Confidant", "Post-Irony"],
    },
    {
        "number": 2,
        "title": "The Jacket, the Cat, and the Streamer",
        "motifs": ["family home", "soiled clothing", "cat", "streaming", "old employer"],
        "summary": (
            "A dinner in the parents' dining room spills outward into a clubhouse, a "
            "laundry search, a cat hidden in a paper bag, an unwanted genre spectacle, "
            "and Asmongold speaking through VR in front of Ernest's mother. An old "
            "employer repeatedly calls in a low, unintelligible voice."
        ),
        "links": ["The Oedipal Screen", "The Attention Economy", "Autofiction"],
    },
    {
        "number": 3,
        "title": "The Broken strauh.al Award Demo",
        "motifs": ["recognition", "technical failure", "childhood church", "community", "surveillance"],
        "summary": (
            "At an awards ceremony in a conference room resembling a disliked childhood "
            "church, strauh.al wins third place but fails during its projected demo. "
            "Ernest drives away to repair it, passes a childhood friend's graduation, "
            "encounters anxiety about surveillance, fixes the bug in a store, and jokes "
            "to a judge that he is responsible for atomization."
        ),
        "links": ["strauh.al Archive", "The Internet as Confidant", "Memory and Preservation"],
    },
    {
        "number": 4,
        "title": "Marriage, 4chan, and the Flight Home",
        "motifs": ["marriage", "online hostility", "creativity", "driving", "autonomy"],
        "summary": (
            "Ernest drives drunk through a heavily policed version of his hometown while "
            "thinking about a misogynistic 4chan thread concerning the woman he has just "
            "married. Commenters claim marriage will extinguish his creativity. A Jung "
            "passage read shortly afterward offers a striking counter-image: shared life "
            "as the sacrifice of isolated autonomy rather than the destruction of efficacy."
        ),
        "links": ["The Internet as Confidant", "Autofiction", "Amor Fati"],
    },
    {
        "number": 5,
        "title": "The Zen Friend and the Windshield Wipers",
        "motifs": ["old community", "grief", "teaching", "lateness", "food", "pursuit"],
        "summary": (
            "An old friend from Zen meditation embraces Ernest in tears. The dream then "
            "moves to a day of teaching: while late to a student's home, Ernest delegates "
            "a food order through an unfamiliar payment app, only to cling to the courier's "
            "windshield wipers as the car speeds away."
        ),
        "links": ["Memory and Preservation", "The Attention Economy", "Spontaneity and Elegance"],
    },
    {
        "number": 6,
        "title": "The Cybertruck and the Wrong Exit",
        "motifs": ["vehicle", "new job", "collectibles", "old coworker", "wrong exit"],
        "summary": (
            "Ernest inexplicably owns a disliked Cybertruck and drives it to a new job at "
            "a comic or collectibles store. Old acquaintances and repeated collectibles "
            "appear amid a search for parking; on the drive home he accelerates hard and "
            "takes the wrong exit."
        ),
        "links": ["Post-Irony", "The Attention Economy", "Autofiction"],
    },
    {
        "number": 7,
        "title": "Chopin Goes Bowling",
        "motifs": ["Chopin", "piano", "bowling", "YouTube", "anime"],
        "summary": (
            "Ernest sees Frederic Chopin perform live. Afterward Chopin proposes that they "
            "become bowling partners, while YouTube fills with reactions to the composer's "
            "taste in anime."
        ),
        "links": ["Spontaneity and Elegance", "Post-Irony", "Map - Current Listening"],
    },
]


def yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(f'"{value}"' for value in values) + "]"


def write_raw(source: Path) -> None:
    today = dt.date.today().isoformat()
    original = source.read_text(errors="ignore").strip()
    body = (
        "---\n"
        "title: Recent Dreams Before Ayahuasca\n"
        "slug: recent-dreams-before-ayahuasca\n"
        "type: dream-journal\n"
        f"ingested: {today}\n"
        "compiled: true\n"
        "temporal_context: after marriage and before an ayahuasca ceremony\n"
        "tags: [raw, dreams, marriage, threshold]\n"
        "---\n\n"
        "# Recent Dreams Before Ayahuasca\n\n"
        "Context supplied by Ernest: these dreams occurred recently, after getting "
        "married and before an ayahuasca ceremony. Exact dates were not supplied.\n\n"
        "The original numbering is preserved below, including the repeated dream 5 label.\n\n"
        "## Original Text\n\n"
        f"{original}\n"
    )
    (RAW / "recent-dreams-before-ayahuasca.md").write_text(body)


def write_dream_notes() -> None:
    today = dt.date.today().isoformat()
    DREAMS.mkdir(parents=True, exist_ok=True)
    for entry in ENTRIES:
        links = "\n".join(f"- [[{target}]]" for target in entry["links"])
        body = f"""---
title: "Dream {entry["number"]} - {entry["title"]}"
type: dream
status: recorded
sequence: {entry["number"]}
date: unknown
temporal_context: after marriage and before an ayahuasca ceremony
motifs: {yaml_list(entry["motifs"])}
tags: [dream, journal, threshold]
sources: ["[[recent-dreams-before-ayahuasca]]"]
created: {today}
updated: {today}
---

# Dream {entry["number"]} - {entry["title"]}

## Dream Record

{entry["summary"]}

This note is an index and reflection surface. The complete first-person account remains in [[recent-dreams-before-ayahuasca]].

## Motifs

{chr(10).join(f"- {motif}" for motif in entry["motifs"])}

## Connections

{links}
- [[Map - Recent Dreams]]
- [[Dreams Series]]

## Reflection

No fixed interpretation has been assigned. Add remembered details, waking associations, or later resonances here.
"""
        path = DREAMS / f"dream-{entry['number']:02d}.md"
        path.write_text(body)


def write_map() -> None:
    today = dt.date.today().isoformat()
    notes = "\n".join(
        f"- [[Dream {entry['number']} - {entry['title']}]]" for entry in ENTRIES
    )
    body = f"""---
title: Map - Recent Dreams
type: map
tags: [map, dreams, journal, threshold]
sources: ["[[recent-dreams-before-ayahuasca]]"]
created: {today}
updated: {today}
---

# Map - Recent Dreams

Seven recent dreams recorded after Ernest's marriage and before an ayahuasca ceremony. The context matters, but it is not treated as a universal key that explains every image.

## Dreams

{notes}

## Recurring Constellations

### Exposure and evaluation

- [[Dream 1 - The Palantir Panel Outside Target]]
- [[Dream 3 - The Broken strauh.al Award Demo]]
- Public judgment repeatedly meets bodily vulnerability or technical failure.

### Networks entering intimate life

- [[Dream 2 - The Jacket, the Cat, and the Streamer]]
- [[Dream 4 - Marriage, 4chan, and the Flight Home]]
- [[Dream 7 - Chopin Goes Bowling]]
- Platforms, streamers, group chats, and reaction culture intrude into family, marriage, art, and history.

### Old communities returning

- [[Dream 2 - The Jacket, the Cat, and the Streamer]]
- [[Dream 3 - The Broken strauh.al Award Demo]]
- [[Dream 5 - The Zen Friend and the Windshield Wipers]]
- Former coworkers, childhood friends, churches, temples, employers, and parents recur as social memory.

### Vehicles, urgency, and uncertain direction

- [[Dream 3 - The Broken strauh.al Award Demo]]
- [[Dream 4 - Marriage, 4chan, and the Flight Home]]
- [[Dream 5 - The Zen Friend and the Windshield Wipers]]
- [[Dream 6 - The Cybertruck and the Wrong Exit]]
- Movement is fast and purposeful, but compromised by intoxication, pursuit, surveillance, or a wrong turn.

### Marriage and creative autonomy

- [[Dream 4 - Marriage, 4chan, and the Flight Home]]
- The dream voices a fear that attachment could erase creativity; the Jung passage recorded after waking supplies Ernest's own counterpoint, where shared life enlarges rather than imprisons the self.

## Existing Bridges

- [[Dreams Series]] - an earlier visual practice made at the threshold of sleep.
- [[The Internet as Confidant]] - digital networks as witness, audience, threat, and memory.
- [[The Oedipal Screen]] - screens entering domestic and psychic life.
- [[Memory and Preservation]] - the archive as a way of retaining unstable experience.
- [[Spontaneity and Elegance]] - immediacy before interpretation hardens.

## Forward — the threshold

These seven are the *before*. The line they were recorded against is [[The Ceremony]];
[[Megan]] is present on both sides of it. When there is an *after*, it links back here.

## Method

These links are descriptive rather than diagnostic. Dream images can remain funny, embarrassing, frightening, contradictory, or unresolved.
"""
    (MAPS / "Map - Recent Dreams.md").write_text(body)


def write_source_bridge() -> None:
    today = dt.date.today().isoformat()
    anchors = WIKI / "anchors"
    anchors.mkdir(parents=True, exist_ok=True)
    body = f"""---
title: recent-dreams-before-ayahuasca
type: source-index
aliases: [Recent Dreams Before Ayahuasca]
tags: [source, dreams, journal, provenance]
created: {today}
updated: {today}
---

# Recent Dreams Before Ayahuasca

Source bridge for a private first-person dream journal recorded after Ernest's marriage and before an ayahuasca ceremony.

## Compiled View

- [[Map - Recent Dreams]]
- [[Dreams Series]]

## Editorial Boundary

The verbatim account is preserved in `knowledge/raw/recent-dreams-before-ayahuasca.md`. Compiled notes provide navigation and descriptive motifs, not clinical or definitive symbolic interpretations.
"""
    (anchors / "recent-dreams-before-ayahuasca.md").write_text(body)


def update_registry() -> None:
    path = RAW / "_sources.md"
    text = path.read_text(errors="ignore")
    slug = "recent-dreams-before-ayahuasca"
    if f"| {slug} |" not in text:
        text = text.rstrip() + f"\n| {slug} | dream-journal | {dt.date.today().isoformat()} | true |\n"
        path.write_text(text)


def main() -> None:
    source = DEFAULT_SOURCE
    if not source.exists():
        raise SystemExit(f"Dream source not found: {source}")
    RAW.mkdir(parents=True, exist_ok=True)
    MAPS.mkdir(parents=True, exist_ok=True)
    write_raw(source)
    write_dream_notes()
    write_map()
    write_source_bridge()
    update_registry()
    print(f"Integrated {len(ENTRIES)} recent dreams.")


if __name__ == "__main__":
    main()
