#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
RAW = VAULT / "knowledge" / "raw"
BOOKS = WIKI / "books"
MAPS = WIKI / "maps"
OUTPUT = VAULT / "knowledge" / "output"


DEFAULT_LIST = Path("/Users/erneststrauhal/.codex/attachments/2028eb92-8d91-4875-820c-be7eef1761b8/pasted-text.txt")
READINGS_DIR = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Readings"

# Curated metadata overrides, keyed by the exact source filename. Repairs the
# "Unknown" authors and garbled titles that filename parsing alone cannot recover.
OVERRIDES_PATH = RAW / "books-metadata.json"


def load_overrides() -> dict[str, dict]:
    if not OVERRIDES_PATH.exists():
        return {}
    try:
        data = json.loads(OVERRIDES_PATH.read_text())
    except json.JSONDecodeError:
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


OVERRIDES = load_overrides()


CATEGORY_RULES = [
    ("Art and Aesthetics", r"art|aesthetic|drawing|figure|visual|painting|beuys|kandinsky|bacon|gombrich|arnheim|hockney|munari|typographic|loomis|schiele|berger"),
    ("Philosophy", r"hegel|nietzsche|kant|deleuze|spinoza|descartes|heraclitus|phenomenology|husserl|sartre|camus|schopenhauer|stirner|epicurus|plato|aristotle|baudrillard|derrida|foucault|adorno|benjamin|marx|kojeve|koj[eè]ve"),
    ("Psychoanalysis and Psychology", r"jung|lacan|freud|psych|attention|adhd|scattered minds|kahneman|sacks|becker|denial of death|narcissism|suicid|madness"),
    ("Media and Technology", r"internet|technology|technopoly|ai|artificial intelligence|virtual reality|comput|cyber|singularity|new dark age|shallow|postman|brindle|briddle|kurzweil|tegmark|gibson|snow crash"),
    ("Literature", r"novel|poem|poet|nabokov|dickens|melville|moby|pynchon|zola|auster|lockwood|mccarthy|gatsby|kerouac|pessoa|plath|mishima|murakami|bradbury|borges|lerner|wallace|proust|houellebecq|dostoevsky"),
    ("Politics and Society", r"politic|warfare|coercion|cia|capitalism|society|jim crow|graeber|lasch|fukuyama|harari|incarceration|manifesto|kaczynski|security analysis|buffett"),
    ("Spirituality and Esoterica", r"buddha|buddhism|upanishad|bhagavad|tao|dao|i ching|occult|magic|alchemy|psychedelic|leary|watts|don juan|zhuangzi|lotus sutra|meditations|stoic|enchiridion"),
    ("Music and Sound", r"music|sound|noise|timbre|chord|piano|bach|sakamoto|hecker|cage|slonimsky|spectral|notation|inventions"),
    ("Design and Making", r"design|making|manufactur|shop class|creative act|skill acquisition|code as creative|maxmsp|electronics|macintosh"),
]


def clean(value: str) -> str:
    value = unquote(value).strip()
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    replacements = {
        "GÃ¶del": "Gödel",
        "MatÃ©": "Maté",
        "Débâcle": "Débâcle",
        "Émile": "Émile",
        "André": "André",
        "Nāgārjuna": "Nāgārjuna",
        "â": "'",
        "ï¼": ":",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:140] or "untitled"


def strip_ext(value: str) -> str:
    return re.sub(r"\.(pdf|epub|mobi|djvu|html|txt|rtf|docx|pages|jpg|jpeg|png)$", "", value, flags=re.I)


def safe_title(value: str) -> str:
    value = value.replace("[", "").replace("]", "")
    value = value.replace("|", " - ")
    value = value.replace("/", " - ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -") or "Untitled"


def parse_line(line: str, source_path: Path | None = None) -> dict[str, str]:
    original = line.strip()
    stem = clean(strip_ext(original))
    stem = re.sub(r"\s+-\s+libgen\.[a-z]+$", "", stem, flags=re.I)
    stem = re.sub(r"\s+\(z-lib\.org\)$", "", stem, flags=re.I)
    stem = re.sub(r"\s+--\s+Anna.s Archive$", "", stem, flags=re.I)
    year = ""
    ym = re.search(r"\b(1[5-9][0-9]{2}|20[0-9]{2})\b", stem)
    if ym:
        year = ym.group(1)

    author = ""
    title = stem
    if " -- " in stem:
        parts = [p.strip() for p in stem.split(" -- ") if p.strip()]
        if len(parts) >= 2:
            title = parts[0]
            author = parts[1]
    elif " - " in stem:
        parts = [p.strip() for p in stem.split(" - ", 1)]
        if len(parts) == 2:
            author, title = parts

    title = re.sub(r"\s+\([^)]*(?:19|20)[0-9]{2}[^)]*\)", "", title).strip()
    title = re.sub(r"\s+\[[^\]]+\]$", "", title).strip()
    author = re.sub(r"\s+\([^)]*\)", "", author).strip()
    if not author and re.search(r" by ", title, re.I):
        title, author = re.split(r"\s+by\s+", title, maxsplit=1, flags=re.I)
    title = safe_title(title or stem)
    author = safe_title(author) if author else ""
    entry = {
        "filename": original,
        "title": title,
        "author": author,
        "year": year,
        "category": categorize(f"{title} {author} {stem}"),
        "source_path": str(source_path) if source_path else "",
        "aliases": [],
        "concepts": [],
        "curated": False,
    }
    # Apply curated overrides (impute author/year, repair title/category).
    override = OVERRIDES.get(original)
    if override:
        auto_title = entry["title"]
        for key in ("title", "author", "year", "category"):
            if override.get(key):
                entry[key] = override[key]
        if override.get("aliases"):
            entry["aliases"] = list(override["aliases"])
        if override.get("concepts"):
            entry["concepts"] = list(override["concepts"])
        # Preserve the pre-override title as an alias so existing references to
        # the old machine-generated title keep resolving after a retitle.
        if entry["title"] != auto_title and auto_title not in entry["aliases"]:
            entry["aliases"].append(auto_title)
        entry["curated"] = True
    return entry


def categorize(value: str) -> str:
    for name, pattern in CATEGORY_RULES:
        if re.search(pattern, value, re.I):
            return name
    return "Unsorted"


def wikilink(title: str) -> str:
    return f"[[{title}]]"


# Editorial suffixes that should not be part of a linked author name.
_AUTHOR_NOISE = re.compile(r"\s*\((?:ed|eds|trans|transl|translator)\.?[^)]*\)", re.I)


def author_names(author: str) -> list[str]:
    """Split an author string into clean personal names, dropping editorial
    fragments ("et al.", "(ed.)", "Google Research")."""
    if not author or author == "Unknown":
        return []
    names = []
    for part in re.split(r"\s*(?:,|&| and )\s*", author):
        part = part.strip()
        if not part or re.search(r"et al\.?|research|press|\(.*\)", part, re.I):
            continue
        clean_name = _AUTHOR_NOISE.sub("", part).strip()
        if clean_name:
            names.append(clean_name)
    return names


def author_links(author: str, known: set[str]) -> str:
    """Render an author string, wikilinking only names that already have a note
    in the wiki (so the lint stays at zero broken links). Unlinked names remain
    plain text and surface separately as new-article candidates.
    """
    if not author or author == "Unknown":
        return "Unknown"
    parts = re.split(r"\s*(?:,|&| and )\s*", author)
    rendered = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        clean_name = _AUTHOR_NOISE.sub("", part).strip()
        if clean_name and clean_name in known and not re.search(r"et al\.?|research|press", part, re.I):
            suffix = part[len(clean_name):]
            rendered.append(f"[[{clean_name}]]{suffix}")
        else:
            rendered.append(part)
    return ", ".join(rendered)


def known_targets() -> set[str]:
    """All resolvable wikilink targets in the wiki: note titles, filename
    stems, and aliases. Used to decide which author names are safe to link."""
    known: set[str] = set()
    for path in WIKI.rglob("*.md"):
        known.add(path.stem)
        text = path.read_text(errors="ignore")
        fm = text.split("---")
        block = fm[1] if len(fm) >= 3 and text.lstrip().startswith("---") else ""
        tm = re.search(r"^title:\s*(.+)$", block, re.M)
        if tm:
            known.add(tm.group(1).strip().strip('"'))
        am = re.search(r"^aliases:\s*\[(.*?)\]", block, re.M)
        if am:
            for alias in am.group(1).split(","):
                alias = alias.strip().strip('"')
                if alias:
                    known.add(alias)
    return known


def file_url(value: str) -> str:
    return "file://" + quote(value, safe="/:")


def write_raw(entries: list[dict[str, str]]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    lines = [
        "---",
        "title: Books Folder Title List",
        "slug: books",
        "type: library",
        f"ingested: {today}",
        "compiled: true",
        "tags: [raw, books]",
        "---",
        "",
        "# Books Folder Title List",
        "",
        f"Entries: {len(entries)}",
        "",
    ]
    for e in entries:
        by = f" — {e['author']}" if e["author"] else ""
        yr = f" ({e['year']})" if e["year"] else ""
        lines.append(f"- {e['title']}{by}{yr}")
    (RAW / "books.md").write_text("\n".join(lines) + "\n")


def write_book_notes(entries: list[dict[str, str]]) -> int:
    BOOKS.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    known = known_targets()
    written = 0
    seen: set[str] = set()
    produced: set[Path] = set()
    for e in entries:
        base = slug(f"{e['author']} {e['title']}" if e["author"] else e["title"])
        path = BOOKS / f"{base}.md"
        if base in seen:
            continue
        seen.add(base)
        produced.add(path)
        title = e["title"]
        author = e["author"] or "Unknown"
        curated = e.get("curated")
        year_line = f"**Year:** {e['year']}\n" if e["year"] else ""
        frontmatter = [
            "---",
            f"title: {json.dumps(title, ensure_ascii=False)}",
            "type: book",
            f"author: {json.dumps(author, ensure_ascii=False)}",
            f"year: {e['year']}",
            f"category: {e['category']}",
            f"status: {'available-local' if e['source_path'] else 'title-only'}",
            f"metadata: {'curated' if curated else 'auto'}",
        ]
        if e.get("aliases"):
            frontmatter.append(f"aliases: [{', '.join(e['aliases'])}]")
        frontmatter += [
            f"source_path: {json.dumps(e['source_path'], ensure_ascii=False) if e['source_path'] else ''}",
            'sources: ["[[books]]"]',
            f"created: {today}",
            f"updated: {today}",
            "---",
        ]
        content = frontmatter + [
            "",
            f"# {title}",
            "",
            f"**Author:** {author_links(author, known)}",
            "",
        ]
        if e["year"]:
            content += [f"**Year:** {e['year']}", ""]
        content += [
            f"**Category:** [[Library - {e['category']}]]",
            "",
            (
                "Status: available in the local iCloud Readings folder."
                if e["source_path"]
                else "Status: title-only bibliographic stub from the iCloud books folder listing."
            ),
            "",
        ]
        # Wire the book into the idea spine (only link concepts that exist).
        concept_links = [c for c in e.get("concepts", []) if c in known]
        if concept_links:
            content += ["## Ideas", "", "*The ideas this book feeds in [[Map - Concepts|the Idea Atlas]]:*", ""]
            content += [f"- [[{c}]]" for c in concept_links]
            content += [""]
        content += [
            "## Connections",
            "",
            "- [[Map - Library]] — library-wide index.",
            f"- [[Library - {e['category']}]] — category shelf.",
            "- [[books]] — raw title list source.",
            "",
            "## Source Filename",
            "",
            f"`{e['filename']}`",
            "",
        ]
        if e["source_path"]:
            content += [
                "## Open",
                "",
                f"[Open the reading file]({file_url(e['source_path'])})",
                "",
            ]
        path.write_text("\n".join(content))
        written += 1
    prune_stale_books(produced)
    return written


def write_author_candidates(entries: list[dict[str, str]]) -> int:
    """Surface authors who appear across multiple books but have no note yet —
    a ranked queue of new-article candidates for the curated people/ layer."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    known = known_targets()
    counts: dict[str, int] = {}
    titles: dict[str, list[str]] = {}
    for e in entries:
        for name in author_names(e.get("author", "")):
            counts[name] = counts.get(name, 0) + 1
            titles.setdefault(name, []).append(e["title"])
    candidates = sorted(
        ((n, c) for n, c in counts.items() if n not in known and c >= 2),
        key=lambda x: (-x[1], x[0]),
    )
    today = dt.date.today().isoformat()
    body = [
        "---",
        "title: Book Author Candidates",
        "type: report",
        "tags: [report, books, candidates]",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# Book Author Candidates",
        "",
        "Authors referenced by two or more books in the library who do not yet "
        "have a note. Each is a candidate for a curated [[Map - Library|library]] "
        "or people page; once a page exists, the importer auto-links every book "
        "to it on the next refresh.",
        "",
    ]
    for name, count in candidates:
        sample = "; ".join(sorted(set(titles[name]))[:4])
        body.append(f"- **{name}** — {count} books: {sample}")
    if not candidates:
        body.append("- None")
    (OUTPUT / "book-author-candidates.md").write_text("\n".join(body) + "\n")
    return len(candidates)


def prune_stale_books(produced: set[Path]) -> None:
    """Move book notes no longer produced by the current title list into the
    archive. Renamed entries (e.g. after an author/title override changes the
    slug) would otherwise linger as orphaned stubs."""
    archive = VAULT / "_archive" / "auto-generated" / "books-stale"
    for path in BOOKS.glob("*.md"):
        if path in produced:
            continue
        archive.mkdir(parents=True, exist_ok=True)
        target = archive / path.name
        if target.exists():
            target.unlink()
        path.rename(target)


def write_category_maps(entries: list[dict[str, str]]) -> None:
    today = dt.date.today().isoformat()
    grouped: dict[str, list[dict[str, str]]] = {}
    for e in entries:
        grouped.setdefault(e["category"], []).append(e)
    for category, items in sorted(grouped.items()):
        body = [
            "---",
            f"title: Library - {category}",
            "type: map",
            "tags: [map, library, books]",
            f"created: {today}",
            f"updated: {today}",
            "---",
            "",
            f"# Library - {category}",
            "",
            f"Books/files: {len(items)}",
            "",
            "## Titles",
            "",
        ]
        for e in sorted(items, key=lambda x: (x["author"], x["title"])):
            note_title = e["title"]
            by = f" — {e['author']}" if e["author"] else ""
            body.append(f"- {wikilink(note_title)}{by}")
        (MAPS / f"Library - {category}.md").write_text("\n".join(body) + "\n")


def write_library_map(entries: list[dict[str, str]]) -> None:
    MAPS.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    grouped: dict[str, int] = {}
    for e in entries:
        grouped[e["category"]] = grouped.get(e["category"], 0) + 1
    body = [
        "---",
        "title: Map - Library",
        "type: map",
        "tags: [map, library, books]",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# Map - Library",
        "",
        "A linked map of the iCloud Readings folder. It knows titles, likely authors, source paths, and broad themes, but it does not pretend to summarize unread books.",
        "",
        f"Total entries: {len(entries)}",
        "",
        f"[Open the iCloud Readings folder]({file_url(str(READINGS_DIR))})",
        "",
        "## Categories",
        "",
    ]
    for category, n in sorted(grouped.items()):
        body.append(f"- [[Library - {category}]] ({n})")
    body += [
        "",
        "## Strong Bridges Into The Wiki",
        "",
        "- [[AI Slop]] with [[Library - Media and Technology]]",
        "- [[Latent Space]] with [[Library - Media and Technology]] and [[Library - Philosophy]]",
        "- [[Spontaneity and Elegance]] with [[Library - Art and Aesthetics]]",
        "- [[Amor Fati]] with [[Library - Philosophy]] and [[Library - Spirituality and Esoterica]]",
        "- [[The Internet as Confidant]] with [[Library - Media and Technology]]",
        "",
        "## Next Useful Metadata",
        "",
        "- Read / unread / to-read status.",
        "- Personal ratings or annotations.",
        "- Extracted highlights, if you want concept notes grounded in passages.",
    ]
    (MAPS / "Map - Library.md").write_text("\n".join(body) + "\n")
    (OUTPUT / "library-build-report.md").write_text(
        "# Library Build Report\n\n"
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}\n\n"
        f"Entries parsed: {len(entries)}\n\n"
        + "\n".join(f"- {category}: {n}" for category, n in sorted(grouped.items()))
        + "\n"
    )


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else (READINGS_DIR if READINGS_DIR.exists() else DEFAULT_LIST)
    if source.is_dir():
        items = sorted(
            path for path in source.iterdir()
            if not path.name.startswith(".")
        )
        entries = [parse_line(path.name, path.resolve()) for path in items]
    else:
        lines = [line for line in source.read_text(errors="ignore").splitlines() if line.strip()]
        entries = [parse_line(line) for line in lines]
    write_raw(entries)
    written = write_book_notes(entries)
    write_category_maps(entries)
    write_library_map(entries)
    candidates = write_author_candidates(entries)
    curated = sum(1 for e in entries if e.get("curated"))
    print(
        f"Parsed {len(entries)} book/file titles; wrote {written} book notes "
        f"({curated} curated via overrides); {candidates} author candidates."
    )


if __name__ == "__main__":
    main()
