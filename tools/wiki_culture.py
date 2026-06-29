#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
RAW = VAULT / "knowledge" / "raw"
WIKI = VAULT / "knowledge" / "wiki"
CULTURE = WIKI / "culture"
MAPS = WIKI / "maps"


READING = [
    ("Sapiens", "Yuval Noah Harari"),
    ("Phenomenology of Spirit", "Georg Wilhelm Friedrich Hegel"),
    ("Play the Piano Drunk Like a Percussion Instrument Until the Fingers Begin to Bleed a Bit", "Charles Bukowski"),
    ("Fanged Noumena", "Nick Land"),
    ("Design as Art", "Bruno Munari"),
    ("Batman: Year One", "Frank Miller; David Mazzucchelli"),
    ("Technopoly", "Neil Postman"),
    ("Beethoven: His Spiritual Development", "J. W. N. Sullivan"),
    ("Homo Deus", "Yuval Noah Harari"),
    ("The Prophet", "Khalil Gibran"),
    ("The Dark Enlightenment", "Nick Land"),
    ("No Longer Human", "Osamu Dazai"),
    ("The Beyond Within", "Sidney Cohen"),
    ("My First Book", "Honor Levy"),
    ("Sin City", "Frank Miller"),
    ("The Letters of Vincent van Gogh", "Vincent van Gogh"),
    ("The Andy Warhol Diaries", "Andy Warhol"),
    ("Galatea 2.2", "Richard Powers"),
    ("Tomie", "Junji Ito"),
    ("The Romantic Manifesto", "Ayn Rand"),
    ("Les Fleurs du mal", "Charles Baudelaire"),
    ("Gothic Violence", "Mike Ma"),
    ("The Art of Dying", "Peter Schjeldahl"),
    ("Akira", "Katsuhiro Otomo"),
    ("The Denial of Death", "Ernest Becker"),
    ("Becoming Steve Jobs", "Brent Schlender; Rick Tetzeli"),
    ("Tao Te Ching", "Lao Tzu"),
    ("The Art Spirit", "Robert Henri"),
    ("New Dark Age", "James Bridle"),
    ("The Dhammapada", "Unknown"),
    ("The Stranger", "Albert Camus"),
    ("Look Back", "Tatsuki Fujimoto"),
    ("Halfway Home", "Reuben Jonathan Miller"),
    ("Fragments", "Heraclitus"),
    ("Sexual Personae", "Camille Paglia"),
    ("In Search of Lost Time", "Marcel Proust"),
]

MUSIC = [
    ("The Complete Parlophone & Columbia Solo Recordings", "Eileen Joyce"),
    ("elseq", "Autechre"),
    ("J. S. Bach: The Well-Tempered Clavier, Books I & II", "Sviatoslav Richter"),
    ("Nachthorn", "Maxime Denuc"),
    ("Mezzanine", "Massive Attack"),
    ("Scriabin: The Complete Preludes for Piano", "Piers Lane"),
    ("First Floor", "Theo Parrish"),
    ("Chopin: Preludes & Piano Sonata No. 2", "Martha Argerich"),
    ("Road Movies", "John Adams"),
    ("Consumed", "Plastikman"),
    ("Beethoven: Symphony No. 9", "Berlin Philharmonic"),
    ("One Nation", "Hype Williams"),
    ("The Incredible Jazz Guitar of Wes Montgomery", "Wes Montgomery"),
    ("Settle", "Disclosure"),
    ("Playing the Piano 12122020", "Ryuichi Sakamoto"),
    ("The Album Formerly Known As...", "Carl Craig"),
    ("Mutant", "Arca"),
    ("Schubert: Impromptus Opp. 90 & 142", "Radu Lupu"),
    ("The Best of Sade", "Sade"),
    ("Die Lit", "Playboi Carti"),
    ("Philip Glass Solo", "Philip Glass"),
    ("Faure: Nocturnes", "Eric Le Sage"),
    ("Azimuth", "Kenny Larkin"),
    ("Mompou: Musica Callada", "Stephen Hough"),
    ("Don't Sweat the Technique", "Eric B. & Rakim"),
    ("Beethoven: Pathetique & Moonlight Sonatas", "Emil Gilels"),
    ("LP1", "FKA twigs"),
    ("Trade Winds, White Noise", "Tim Hecker"),
    ("Syro", "Aphex Twin"),
    ("The End of Evangelion: Original Soundtrack", "Shiro Sagisu"),
    ("Madvillainy", "Madvillain"),
    ("Satie: Avant-dernieres pensees", "Unknown"),
    ("Quest for Fire", "Skrillex"),
    ("Scriabin: Vers la flamme", "Yevgeny Sudbin"),
    ("Minimal Nation", "Robert Hood"),
    ("Musik", "Plastikman"),
    ("Ravel: The Complete Piano Works", "Seong-Jin Cho"),
    ("Karma & Desire", "Actress"),
    ("Schumann: Kinderszenen & Kreisleriana", "Martha Argerich"),
    ("Anoyo", "Tim Hecker"),
    ("Bruckner: Piano Works", "Mari Kodama"),
    ("Turbo 093 - Variations", "Gesaffelstein"),
    ("Computer World", "Kraftwerk"),
]

MOVIES = [
    ("Happy as Lazzaro", "Alice Rohrwacher"),
    ("Speed Racer (2008)", "The Wachowskis"),
    ("Megalopolis", "Francis Ford Coppola"),
    ("American Beauty", "Sam Mendes"),
    ("Young Frankenstein", "Mel Brooks"),
    ("Gattaca", "Andrew Niccol"),
    ("Cloud Atlas", "The Wachowskis; Tom Tykwer"),
    ("Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb", "Stanley Kubrick"),
    ("Pan's Labyrinth", "Guillermo del Toro"),
    ("The King of Masks", "Wu Tianming"),
    ("Koyaanisqatsi", "Godfrey Reggio"),
    ("Sunset Boulevard", "Billy Wilder"),
    ("The End of Evangelion", "Hideaki Anno; Kazuya Tsurumaki"),
    ("The Truman Show", "Peter Weir"),
    ("Carrie (1976)", "Brian De Palma"),
    ("A Beautiful Mind", "Ron Howard"),
    ("My Own Private Idaho", "Gus Van Sant"),
    ("Casablanca", "Michael Curtiz"),
    ("Playback Time", "Carson Clay"),
    ("Cyrano de Bergerac", "Unknown"),
    ("Crouching Tiger, Hidden Dragon", "Ang Lee"),
    ("Godzilla (1998)", "Roland Emmerich"),
    ("Edward Scissorhands", "Tim Burton"),
    ("Ali: Fear Eats the Soul", "Rainer Werner Fassbinder"),
    ("Trainspotting", "Danny Boyle"),
    ("Lawrence of Arabia", "David Lean"),
    ("Crumb", "Terry Zwigoff"),
    ("Children of Men", "Alfonso Cuaron"),
    ("The Wizard of Oz", "Victor Fleming"),
    ("Whiplash", "Damien Chazelle"),
    ("Cinema Paradiso", "Giuseppe Tornatore"),
    ("Watchmen", "Zack Snyder"),
    ("Taxi Driver", "Martin Scorsese"),
    ("Akira", "Katsuhiro Otomo"),
    ("The Shawshank Redemption", "Frank Darabont"),
    ("Perfect Blue", "Satoshi Kon"),
    ("Requiem for a Dream", "Darren Aronofsky"),
    ("The 7th Voyage of Sinbad (1958)", "Nathan H. Juran"),
    ("Charlie and the Chocolate Factory (2005)", "Tim Burton"),
    ("Fist of Fury", "Lo Wei"),
    ("Man of Steel", "Zack Snyder"),
]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:140] or "untitled"


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def people_links(value: str) -> str:
    if value == "Unknown":
        return "Unknown / traditional"
    return "; ".join(f"[[{name.strip()}]]" for name in value.split(";"))


def note_title(kind: str, title: str) -> str:
    return f"{'Reading' if kind == 'reading' else 'Listening' if kind == 'music' else 'Watchlist'} - {title}"


def write_note(kind: str, title: str, creator: str, index: int) -> None:
    today = dt.date.today().isoformat()
    full_title = note_title(kind, title)
    noun = {"reading": "book", "music": "recording", "movie": "film"}[kind]
    role = {"reading": "Author", "music": "Artist / performer", "movie": "Director"}[kind]
    map_title = {"reading": "Current Reading", "music": "Current Listening", "movie": "Film Watchlist"}[kind]
    body = [
        "---",
        f"title: {yaml_quote(full_title)}",
        f"type: {kind}",
        f"work: {yaml_quote(title)}",
        f"creator: {yaml_quote(creator)}",
        "status: queued",
        f"queue_order: {index}",
        f"tags: [culture, {kind}, queued]",
        'sources: ["[[current-cultural-diet]]"]',
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        f"# {title}",
        "",
        f"**{role}:** {people_links(creator)}",
        "",
        "**Status:** queued",
        "",
        f"This is an active {noun} in Ernest's current cultural diet. Add dates, reactions, favorite passages or tracks, and stronger concept links here as the encounter develops.",
        "",
        "## Connections",
        "",
        f"- [[Map - {map_title}]]",
        "- [[Map - Current Culture]]",
        "- [[current-cultural-diet]]",
        "",
        "## Notes",
        "",
        "",
    ]
    (CULTURE / f"{kind}-{slug(title)}.md").write_text("\n".join(body))


def write_queue_map(kind: str, entries: list[tuple[str, str]]) -> None:
    today = dt.date.today().isoformat()
    title = {"reading": "Current Reading", "music": "Current Listening", "movie": "Film Watchlist"}[kind]
    description = {
        "reading": "Books currently in the reading orbit. Queued means selected, not necessarily started.",
        "music": "Recordings and albums in active rotation or awaiting a focused listen.",
        "movie": "Films queued to watch. Checkboxes are intentionally preserved as the useful interface.",
    }[kind]
    lines = [
        "---", f"title: Map - {title}", "type: map",
        f"tags: [map, culture, {kind}, queue]",
        f"created: {today}", f"updated: {today}", "---", "",
        f"# Map - {title}", "", description, "", f"Entries: {len(entries)}", "",
    ]
    for work, creator in entries:
        target = note_title(kind, work)
        credit = "" if creator == "Unknown" else f" - {creator}"
        prefix = "- [ ]" if kind == "movie" else "-"
        lines.append(f"{prefix} [[{target}|{work}]]{credit}")
    (MAPS / f"Map - {title}.md").write_text("\n".join(lines) + "\n")


def write_current_map() -> None:
    today = dt.date.today().isoformat()
    body = f"""---
title: Map - Current Culture
type: map
tags: [map, culture, reading, listening, watching]
created: {today}
updated: {today}
---

# Map - Current Culture

What Ernest is reading, listening to, and planning to watch right now. This is a living intake layer: selected works first, interpretation later.

## Queues

- [[Map - Current Reading]] ({len(READING)})
- [[Map - Current Listening]] ({len(MUSIC)})
- [[Map - Film Watchlist]] ({len(MOVIES)})

## Constellations

### Technology, systems, and the manufactured world

- [[Reading - Technopoly|Technopoly]]
- [[Reading - New Dark Age|New Dark Age]]
- [[Reading - Sapiens|Sapiens]]
- [[Reading - Homo Deus|Homo Deus]]
- [[Watchlist - Gattaca|Gattaca]]
- [[Watchlist - Children of Men|Children of Men]]
- [[Watchlist - The Truman Show|The Truman Show]]
- [[Listening - Computer World|Computer World]]
- [[The Internet as Confidant]]

### Death, alienation, and ways through

- [[Reading - The Denial of Death|The Denial of Death]]
- [[Reading - No Longer Human|No Longer Human]]
- [[Reading - The Stranger|The Stranger]]
- [[Reading - The Art of Dying|The Art of Dying]]
- [[Reading - Tao Te Ching|Tao Te Ching]]
- [[Reading - The Dhammapada|The Dhammapada]]
- [[Watchlist - Perfect Blue|Perfect Blue]]
- [[Watchlist - Requiem for a Dream|Requiem for a Dream]]
- [[Amor Fati]]

### Piano as thought and touch

- [[Listening - J. S. Bach: The Well-Tempered Clavier, Books I & II|Bach / Richter]]
- [[Listening - Scriabin: The Complete Preludes for Piano|Scriabin / Lane]]
- [[Listening - Playing the Piano 12122020|Sakamoto]]
- [[Listening - Mompou: Musica Callada|Mompou / Hough]]
- [[Listening - Ravel: The Complete Piano Works|Ravel / Cho]]
- [[Reading - Beethoven: His Spiritual Development|Beethoven: His Spiritual Development]]
- [[Spontaneity and Elegance]]

### Electronic space, texture, and repetition

- [[Listening - elseq|elseq]]
- [[Listening - Consumed|Consumed]]
- [[Listening - Syro|Syro]]
- [[Listening - Anoyo|Anoyo]]
- [[Listening - Minimal Nation|Minimal Nation]]
- [[Listening - Karma & Desire|Karma & Desire]]
- [[Implicit Distance]]
- [[Latent Space]]

### Animation, comics, and unstable identity

- [[Reading - Akira|Akira]]
- [[Reading - Tomie|Tomie]]
- [[Reading - Look Back|Look Back]]
- [[Reading - Batman: Year One|Batman: Year One]]
- [[Watchlist - Akira|Akira (film)]]
- [[Watchlist - The End of Evangelion|The End of Evangelion]]
- [[Watchlist - Perfect Blue|Perfect Blue]]
- [[Watchlist - Speed Racer (2008)|Speed Racer]]
- [[Autofiction]]

## A Small Editorial Note

[[Ayn Rand]] is here without apology. Brittle logic and personal charm can coexist; a useful knowledge base records the attraction before trying to prosecute it.
"""
    (MAPS / "Map - Current Culture.md").write_text(body)


def write_raw_source() -> None:
    today = dt.date.today().isoformat()
    lines = [
        "---", "title: Current Cultural Diet", "slug: current-cultural-diet",
        "type: source", f"ingested: {today}", "compiled: true",
        "tags: [raw, culture, reading, listening, watching]", "---", "",
        "# Current Cultural Diet", "",
        "Supplied by Ernest on 2026-06-22. Wording is lightly normalized in compiled notes; this source preserves the selected works and the spirit of the list.",
        "", "## Reading", "",
    ]
    lines += [f"- {title} - {creator}" for title, creator in READING]
    lines += [
        "",
        "> Yes, Ayn Rand is in my list. Yes, you may laugh at me, but despite her brittle logic, I find her quite charming.",
        "", "## Music", "",
    ]
    lines += [f"- {title} - {creator}" for title, creator in MUSIC]
    lines += ["", "## Movies", ""]
    lines += [f"- [ ] {title}" for title, _ in MOVIES]
    (RAW / "current-cultural-diet.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    CULTURE.mkdir(parents=True, exist_ok=True)
    MAPS.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    write_raw_source()
    for kind, entries in (("reading", READING), ("music", MUSIC), ("movie", MOVIES)):
        for index, (title, creator) in enumerate(entries, 1):
            write_note(kind, title, creator, index)
        write_queue_map(kind, entries)
    write_current_map()
    print(f"Integrated {len(READING)} books, {len(MUSIC)} recordings, and {len(MOVIES)} films.")


if __name__ == "__main__":
    main()
