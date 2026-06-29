#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
RAW = VAULT / "knowledge" / "raw"
OUTPUT = VAULT / "knowledge" / "output"
PEOPLE = WIKI / "people"
CONCEPTS = WIKI / "concepts"
MAPS = WIKI / "maps"
IMAGE_ROOT = Path("/Users/erneststrauhal/GitHub/strauh.al3.1")


def text(path: Path) -> str:
    return path.read_text(errors="ignore")


def slug(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def titlecase_from_slug(value: str) -> str:
    words = value.replace("-", " ").replace("_", " ").split()
    special = {"ai": "AI", "vr": "VR", "html": "HTML"}
    return " ".join(special.get(w.lower(), w.capitalize()) for w in words)


def frontmatter_field(body: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", body, re.M)
    return match.group(1).strip().strip('"') if match else ""


def wiki_notes() -> list[Path]:
    return sorted(p for p in WIKI.rglob("*.md") if p.is_file())


def richer_note_index() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in wiki_notes():
        body = text(path)
        if "source_kind: \"stub_concept\"" in body:
            continue
        title = frontmatter_field(body, "title") or path.stem
        keys = {slug(title), slug(path.stem)}
        aliases = frontmatter_field(body, "aliases")
        for alias in re.findall(r"[^,\[\]]+", aliases):
            if alias.strip():
                keys.add(slug(alias.strip()))
        for key in keys:
            out.setdefault(key, path)
    return out


def wikilink_for(path: Path) -> str:
    title = frontmatter_field(text(path), "title") or path.stem
    return f"[[{title}]]"


def polish_stub_redirects() -> int:
    rich = richer_note_index()
    changed = 0
    for path in sorted(CONCEPTS.glob("*.md")):
        body = text(path)
        if "source_kind: \"stub_concept\"" not in body:
            continue
        title = frontmatter_field(body, "title") or path.stem
        target = rich.get(slug(title)) or rich.get(slug(path.stem))
        if not target or target == path:
            continue
        link = wikilink_for(target)
        new_body = (
            "---\n"
            f'title: "{title}"\n'
            'source_kind: "redirect_stub"\n'
            'compiled: "True"\n'
            'tags: ["strauhal", "concept", "redirect"]\n'
            "---\n"
            f"# {title}\n\n"
            f"See {link}.\n\n"
            "This note exists because generated pages linked this spelling or alias. "
            "The richer article is the canonical place to expand the idea.\n"
        )
        if body != new_body:
            path.write_text(new_body)
            changed += 1
    return changed


def influence_entries() -> list[tuple[str, str, str]]:
    raw = RAW / "influences.md"
    if not raw.exists():
        return []
    entries = []
    for line in text(raw).splitlines():
        match = re.search(r"/influences/([^/\s]+\.(?:jpg|jpeg|png|gif|webp))", line, re.I)
        if not match:
            continue
        filename = match.group(1)
        stem = Path(filename).stem
        title = titlecase_from_slug(stem)
        rel = f"influences/{filename}"
        entries.append((title, stem, rel))
    return entries


def create_influence_notes() -> int:
    PEOPLE.mkdir(parents=True, exist_ok=True)
    existing = richer_note_index()
    created = 0
    for title, stem, rel in influence_entries():
        key = slug(title)
        if key in existing:
            continue
        path = PEOPLE / f"{slug(title)}.md"
        if path.exists():
            continue
        image_path = IMAGE_ROOT / rel
        embed = f"![[media/strauh.al3.1/{rel}]]" if image_path.exists() else ""
        content = (
            "---\n"
            f"title: {title}\n"
            "type: person\n"
            f"aliases: [{stem.replace('_', ' ')}]\n"
            "tags: [person, influence, stub]\n"
            'sources: ["[[influences]]"]\n'
            f"created: {dt.date.today().isoformat()}\n"
            f"updated: {dt.date.today().isoformat()}\n"
            "---\n\n"
            f"# {title}\n\n"
            f"{embed}\n\n" if embed else f"# {title}\n\n"
        )
        content += (
            f"Listed in [[influences]] as part of the strauh.al influence wall.\n\n"
            "## Connections\n\n"
            "- [[strauh.al Archive]] — part of the authorial constellation around the archive.\n"
            "- [[Map - Influences]] — grouped with the other influence-wall entries.\n\n"
            "## Sources\n\n"
            "- [[influences]]\n"
        )
        path.write_text(content)
        created += 1
    return created


def note_type(path: Path) -> str:
    return frontmatter_field(text(path), "type")


def source_kind(path: Path) -> str:
    return frontmatter_field(text(path), "source_kind")


def note_list(folder: str, limit: int | None = None, curated_only: bool = False) -> list[str]:
    paths = sorted((WIKI / folder).glob("*.md"))
    if curated_only:
        paths = [p for p in paths if note_type(p) in {"person", "concept", "work", "map"}]
    if limit:
        paths = paths[:limit]
    lines = []
    for path in paths:
        title = frontmatter_field(text(path), "title") or path.stem
        if "\n" in title:
            continue
        lines.append(f"- [[{title}]]")
    return lines


def count(folder: str) -> int:
    return len(list((WIKI / folder).glob("*.md")))


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def write_maps() -> None:
    today = dt.date.today().isoformat()
    MAPS.mkdir(parents=True, exist_ok=True)

    home = f"""---
title: strauh.al Knowledge Base
type: map
aliases: [Atlas, strauh.al Atlas, home]
tags: [map, home, strauhal, atlas]
created: {today}
updated: {today}
---

# strauh.al — an atlas, not a feed

A knowledge system built the opposite way from the old web. Instead of a flat pile
of pages linking to index pages, this is a **layered atlas**: a spine of *ideas* at
the center, and everything else — people, works, reading, images — arranged as what
*feeds* those ideas. From here, any of ~{count("images") + count("books") + count("artists")} notes is three hops away.

## ① The spine — start here

→ **[[Map - Concepts|The Idea Atlas]]** — the ideas the whole system hangs from,
grouped into four themes. This is the front door; read the vault *through* the ideas.

## ② The domains — what feeds the ideas

| Domain | Map | What's in it |
| --- | --- | --- |
| People | [[Map - Influences]] | The influences behind the ideas |
| Works | [[Map - Works]] | Where the ideas get made |
| Reading | [[Map - Library]] | The library, shelved by subject and wired to ideas |
| Images | [[Map - Image Archive]] | The collected visual corpus |
| Now | [[Map - Current Culture]] | What's feeding the ideas this season |
| Dreams | [[Map - Recent Dreams]] | The unconscious feed |
| Time | [[Map - Timeline]] | The vault as a sequence, 2015 → now |
| Interface | [[Map - Living Graph]] | A conversational, moving view of the atlas |
| 3D | [[Map - 3D Graph]] | A fly-through 3D map: height = abstraction, floor = theme |

## ③ The record — Ernest, in his own and others' words

- [[Map - Ernest Creative Profile]] · [[Map - Writing About Ernest]] · [[Map - Audience Correspondence]]
- [[Map - ChatGPT Memory]] · [[Map - Reading Constellations]]
- Life: [[Ernest Strauhal]] · [[Family]] · [[Failures and Abandoned Projects]] · [[The Ceremony]] · [[Megan]]

## Brightest hubs

- [[Ernest Strauhal]] — the person all of this maps; [[Family]] is the lineage behind him.
- [[strauh.al Archive]] — the website this all mirrors.
- [[Latent Space]] · [[The Internet as Confidant]] · [[AI Slop]] — the load-bearing ideas.
- [[Implicit Distance]] · [[SEEKER]] — the load-bearing works.

## Keep it healthy

- [[Map - Maintenance]] — how the vault is built and checked.
- Search: `python3 tools/wiki_search.py "latent space"`

## Current counts

people {count("people")} · concepts {count("concepts")} · works {count("works")} · books {count("books")} · culture {count("culture")} · dreams {count("dreams")} · images {count("images")} · pages {count("pages")} · collections {count("collections")}
"""
    write(WIKI / "Home.md", home)
    write(VAULT / "Welcome.md", home)

    works = f"""---
title: Map - Works
type: map
tags: [map, works]
created: {today}
updated: {today}
---

# Map - Works

The work layer collects projects, tools, and recurring bodies of work.

## Works

{os.linesep.join(note_list("works", curated_only=True))}

## Related Concepts

- [[Latent Space]]
- [[Spontaneity and Elegance]]
- [[AI Slop]]
- [[The Attention Economy]]
- [[Memory and Preservation]]
"""
    write(MAPS / "Map - Works.md", works)

    concepts = f"""---
title: Map - Concepts
type: map
aliases: [Idea Atlas, The Idea Atlas, Concept Atlas]
tags: [map, concepts, atlas]
created: {today}
updated: {today}
---

# The Idea Atlas

**The spine of the vault.** Everything else — influences, works, the reading
library, the image archive — is here to feed one of these ideas. Read the system
*through* the ideas, not through the folders. The four clusters below are the load-
bearing themes; each idea links down to the people, works, and books that orbit it.

> [!tip] Reading the graph
> In the graph view the bright teal nodes are these concepts. They are the most-
> connected nodes by design; the dim grey mass is the image archive (kept, not
> deleted, just pushed to the background). To study the idea web on its own, paste
> this into the graph's search box:
> `path:knowledge/wiki/concepts OR path:knowledge/wiki/works OR path:knowledge/wiki/people OR path:knowledge/wiki/maps`

## I · The Machine & the Latent
*AI as both medium and metaphor — the engine of Ernest's practice.*

- [[Latent Space]] — identity, art, and feeling as positions and trajectories inside a continuous interpolated space. The central metaphor.
- [[Dead Architecture]] — generated video as "dead architecture with the illusion of movement": duration without a performed event.
- [[Human-Machine Tug of War]] — authorship as a negotiation; the model a temporarily empowered collaborator.
- [[AI Slop]] — the running critique of AI-generated culture, and his uneasy implication in it.
- [[Interpolating the Instruction Set]] — the sharper reading of latent space: you move through the *recipe*, not the images.
- [[Transmitting My Neural Signals by Hand]] — the bodily twin of latent space: the hand as a lossy channel out of the mind.
- [[Synesthesia]] — color as sound, sound as color: latent space felt through the senses.
- [[The Spatial Web]] — knowledge as a place you walk; the wish behind [[Map - 3D Graph]].

Orbiting: [[Implicit Distance]] · [[GAN Color Studies]] · [[Vocal Study 3]] · [[kits.ai Voice]] · [[Video Portraiture]] · [[SEEKER]] · [[Terry A. Davis]]

## II · The Self & Its Narration
*The diary's slow turn from record into literature.*

- [[Autofiction]] — "this diary began as an earnest attempt at recording daily events, but has morphed into autofiction."
- [[Amor Fati]] — the Nietzschean stance copied into the diary as aspiration: to become a "Yes-sayer."
- [[Post-Irony]] — the register where sincere, ironic, and post-ironic can no longer be told apart.
- [[Memory and Preservation]] — the drive to capture and keep that underwrites the whole archive.
- [[The Archive as Consciousness]] — the mind offloaded into HTML; collecting as thinking.
- [[To Render Myself Unnecessary]] — teaching as the inverse of authorship; an inherited value.
- [[Rebuilding from the Bottom]] — collapse as the precondition for the next build.

Orbiting: [[Marcel Proust]] · [[Albert Camus]] · [[Dreams Series]] · [[strauh.al Archive]] · [[Ernest Strauhal]]

## III · The Internet & Attention
*The networked condition the work is addressed to and against.*

- [[The Internet as Confidant]] — the internet as confidant, consciousness, sacred presence: the entity the diary is addressed to.
- [[The Attention Economy]] — the endless personalized feed, blamed for hollowing out art, activism, and focus.
- [[The Oedipal Screen]] — the screen as the supreme power that has displaced both father and mother.
- [[The Flâneur as Web Surfer]] — the stroller of the arcades, rebooted for the feed.
- [[Reading Like a Computer]] — the attention economy felt at the level of reading.
- [[Atomization]] — the isolated user the whole system presupposes.

Orbiting: [[strauh.al Archive]] · [[Andy Warhol]] · [[Arcades Project (Revisited)]] · [[Charles Baudelaire]]

## IV · Aesthetics & Affinities
*The taste underneath everything — what counts as beautiful.*

- [[Spontaneity and Elegance]] — prizing the spontaneous, unfinished, and elegant-simple over the labored.
- [[The Tedium of the Art Is the Goal]] — the friction of making *is* the work; the value AI slop inverts.
- [[Art Fills the God-Shaped Hole]] — beauty as secular re-enchantment; the bridge to the spirituality shelf and [[The Ceremony]].
- [[Trainpilled]] — an affinity for rail and a whole aesthetic of slow, analog, distinctly-American infrastructure.

Orbiting: [[Barry McGee]] · [[Egon Schiele]] · [[Yohji Yamamoto]] · [[Rei Kawakubo]] · [[Tim Hecker]] · [[Ryuichi Sakamoto]]

## The rest of the system, by domain

- [[Map - Influences]] — the people who feed these ideas.
- [[Map - Works]] — the works the ideas are realized in.
- [[Map - Library]] — the reading behind the ideas.
- [[Map - Image Archive]] — the visual corpus the ideas are extracted from.
- [[Map - Current Culture]] — what's feeding the ideas now.
- [[Map - Recent Dreams]] — the unconscious feed.

## All ideas (index)

{os.linesep.join(note_list("concepts", curated_only=True))}
"""
    write(MAPS / "Map - Concepts.md", concepts)

    influences = f"""---
title: Map - Influences
type: map
tags: [map, influences, people]
created: {today}
updated: {today}
---

# Map - Influences

People from the influence wall and the diary-linked constellation.

## People

{os.linesep.join(note_list("people", curated_only=True))}
"""
    write(MAPS / "Map - Influences.md", influences)

    archive = f"""---
title: Map - Image Archive
type: map
tags: [map, images, archive]
created: {today}
updated: {today}
---

# Map - Image Archive

The image archive is indexed without copying the 15 GB source folder. Notes embed files through `media/strauh.al3.1`, which is a local symlink to the original archive.

## Browse

- [[strauh.al Image Archive]]
- [[Collection - influences]]
- [[Collection - 1900s]]
- [[Collection - 2000s]]
- [[Collection - artists]]
- [[Collection - diary]]
- [[Collection - computers]]

## Generated Layers

- [[Generated Corpus Stats]]
- Image notes: {count("images")}
- Artist notes inferred from filenames: {count("artists")}
- Collection/date-bucket notes: {count("collections")}
- HTML page notes: {count("pages")}
"""
    write(MAPS / "Map - Image Archive.md", archive)

    review = (dt.date.today() + dt.timedelta(days=30)).isoformat()
    maintenance = f"""---
title: Map - Maintenance
type: map
tags: [map, maintenance]
created: {today}
updated: {today}
---

# Map - Maintenance

## The 30-day habit (most important)

A second brain that isn't updated becomes an archive of who you *were* — and there is
already one of those. This one should track who you're *becoming*. So the simplest,
load-bearing habit: **re-open the vault about every 30 days and add what changed.**

- Last refresh: **{today}** · next review due: **{review}**
- Add new work/event/idea nodes; date every entry ([[Map - Timeline]]).
- Log what stopped in [[Failures and Abandoned Projects]]; write the *after* of [[The Ceremony]] once there is one.
- Then rebuild (below) and confirm the lint is still clean.

## Rebuild

```sh
python3 tools/wiki_refresh.py
```

## Reports

- [wiki-lint-report](../../output/wiki-lint-report.md)
- [overnight-build-report](../../output/overnight-build-report.md)

## Source Roots

- `/Users/erneststrauhal/GitHub/strauh.al4`
- `/Users/erneststrauhal/GitHub/strauh.al3.1`

## Collaboration Rule

Generated archive notes can be rebuilt. Curated `people`, `works`, and non-stub `concepts` should be treated as hand-authored knowledge.
"""
    write(MAPS / "Map - Maintenance.md", maintenance)


def write_report(redirects: int, people_created: int) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    body = f"""# Overnight Build Report

Generated: {dt.datetime.now().isoformat(timespec="seconds")}

## Completed

- Reconciled generated stubs with richer curated notes.
- Added missing influence-wall people notes.
- Created top-level maps of content.
- Kept source archives in place and linked them through `media/`.

## Counts

- Redirect stubs updated: {redirects}
- Influence people notes created: {people_created}
- People notes: {count("people")}
- Concept notes: {count("concepts")}
- Work notes: {count("works")}
- Image notes: {count("images")}
- HTML page notes: {count("pages")}

## Morning Entry Point

Open [[Home]] or [[Map - Maintenance]].
"""
    write(OUTPUT / "overnight-build-report.md", body)


def main() -> None:
    redirects = polish_stub_redirects()
    people = create_influence_notes()
    write_maps()
    write_report(redirects, people)
    print(f"Polished wiki: {redirects} redirect stubs updated, {people} influence notes created.")


if __name__ == "__main__":
    main()
