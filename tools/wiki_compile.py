#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import html
import os
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


VAULT = Path(__file__).resolve().parents[1]
HTML_ROOT = Path("/Users/erneststrauhal/GitHub/strauh.al4")
IMAGE_ROOT = Path("/Users/erneststrauhal/GitHub/strauh.al3.1")

WIKI = VAULT / "knowledge" / "wiki"
RAW = VAULT / "knowledge" / "raw"
PAGES = WIKI / "pages"
COLLECTIONS = WIKI / "collections"
IMAGES = WIKI / "images"
ARTISTS = WIKI / "artists"
CONCEPTS = WIKI / "concepts"
OUTPUT = VAULT / "knowledge" / "output"
MEDIA = VAULT / "media"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".tif", ".avif"}
SKIP_PARTS = {".git", "__pycache__"}


class BodyMarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.in_scriptish = False
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.images: list[tuple[str, str]] = []
        self._link_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {k.lower(): v or "" for k, v in attrs}
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        if tag in {"script", "style", "canvas", "svg"}:
            self.in_scriptish = True
        if self.in_scriptish:
            return
        if tag in {"h1", "h2", "h3"}:
            level = {"h1": "#", "h2": "##", "h3": "###"}[tag]
            self.parts.append(f"\n\n{level} ")
        elif tag in {"p", "div", "section", "article", "br"}:
            self.parts.append("\n")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag == "a":
            href = attrs_d.get("href", "").strip()
            self._link_stack.append(href)
            self.parts.append("[")
        elif tag == "img":
            src = attrs_d.get("src", "").strip()
            alt = attrs_d.get("alt", "").strip()
            if src:
                self.images.append((src, alt))
                self.parts.append(f"\n\n![{alt}]({src})\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag in {"script", "style", "canvas", "svg"}:
            self.in_scriptish = False
            return
        if self.in_scriptish:
            return
        if tag == "a":
            href = self._link_stack.pop() if self._link_stack else ""
            self.parts.append(f"]({href})")
            if href:
                text = ""
                self.links.append((href, text))
        elif tag in {"h1", "h2", "h3", "p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.in_scriptish:
            return
        clean = re.sub(r"\s+", " ", data)
        if clean.strip():
            self.parts.append(clean)

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = html.unescape(text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\[\s+", "[", text)
        text = re.sub(r"\s+\]", "]", text)
        return text.strip()


def ensure_dirs() -> None:
    for path in [RAW, PAGES, COLLECTIONS, IMAGES, ARTISTS, CONCEPTS, OUTPUT, MEDIA]:
        path.mkdir(parents=True, exist_ok=True)
    link_sources()


def link_sources() -> None:
    links = {
        MEDIA / "strauh.al3.1": IMAGE_ROOT,
        MEDIA / "strauh.al4": HTML_ROOT,
    }
    for dest, src in links.items():
        if dest.exists() or dest.is_symlink():
            continue
        dest.symlink_to(src, target_is_directory=True)


def slug(value: str, fallback: str = "untitled") -> str:
    value = unquote(value)
    value = re.sub(r"\.[a-z0-9]+$", "", value, flags=re.I)
    value = value.replace("&", " and ")
    value = re.sub(r"[_/\-\\\\]+", " ", value)
    value = re.sub(r"[^A-Za-z0-9 .,'()+-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value or fallback


def safe_filename(value: str) -> str:
    name = slug(value)
    name = re.sub(r"[/:\\\\]+", " - ", name)
    return name[:150].strip() or "untitled"


def yaml(value: object) -> str:
    if isinstance(value, list):
        if not value:
            return "[]"
        return "[" + ", ".join(yaml(v) for v in value) + "]"
    s = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def frontmatter(**fields: object) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {yaml(value)}")
    lines.append("---\n")
    return "\n".join(lines)


def wikilink(name: str) -> str:
    return f"[[{name}]]"


def page_note_name(path: Path, title: str) -> str:
    rel = path.relative_to(HTML_ROOT)
    if rel.name == "index.html":
        return "strauh.al Home"
    base = title.replace("strauh.al/", "") if title else str(rel.with_suffix(""))
    base = base.replace("strauh.al", "strauh.al Home")
    return safe_filename(base)


def read_html(path: Path) -> tuple[str, str, list[tuple[str, str]], list[tuple[str, str]]]:
    parser = BodyMarkdownParser()
    parser.feed(path.read_text(errors="ignore"))
    return parser.title.strip(), parser.markdown(), parser.links, parser.images


def local_page_link(href: str, current: Path, page_names: dict[Path, str]) -> str | None:
    if not href or href.startswith("#"):
        return None
    parsed = urlparse(href)
    if parsed.scheme and parsed.scheme not in {"file"}:
        return None
    target = (current.parent / parsed.path).resolve()
    try:
        rel = target.relative_to(HTML_ROOT.resolve())
    except ValueError:
        return None
    if target.is_dir():
        target = target / "index.html"
    if target.suffix.lower() != ".html":
        return None
    return page_names.get(target)


def extract_artist(name: str) -> str | None:
    clean = slug(name)
    match = re.search(
        r"\bby ([A-Za-z][A-Za-z0-9 .'-]+?)(?: c | ca | circa | [12][0-9]{2,3}\b|$)",
        clean,
        flags=re.I,
    )
    if not match:
        return None
    artist = match.group(1).strip(" .'-")
    if len(artist) < 3 or len(artist.split()) > 8:
        return None
    if artist.lower().split()[0] in {"a", "an", "the", "this", "that"}:
        return None
    if re.search(r"\b(with|against|surrounded|holding|wearing|formed|created|connected)\b", artist, re.I):
        return None
    return artist


# Filenames that are camera/counter/screenshot IDs, not dated artworks.
_COUNTER_PREFIX = re.compile(
    r"^(img|dsc|dscn|pxl|p|gif|dcim|screenshot|screen[ _-]?shot|photo|fb|received|"
    r"tumblr|gd|image|untitled|original|thumbnail|file|pasted)\b",
    re.I,
)


def real_year(path: Path) -> str:
    """A plausible *artwork* year from the filename, or "".

    Only accepts a 4-digit year in [1400, 2027] when the filename also reads like a
    description (has a word), and isn't a bare camera/counter id like IMG_1875.
    This is what stops image counters (IMG_1058, IMG_2882) from being mistaken for
    years and spawning hundreds of junk "Date Bucket" notes.
    """
    stem = path.stem.strip()
    if not re.search(r"[A-Za-z]{3,}", stem):
        return ""
    if _COUNTER_PREFIX.match(stem):
        return ""
    cands = [
        c for c in re.findall(r"(?<!\d)(1[4-9]\d{2}|20[0-2]\d)(?!\d)", stem)
        if 1400 <= int(c) <= 2027
    ]
    return cands[-1] if cands else ""


def decade_bucket(path: Path) -> str:
    """The decade a dated artwork belongs to (e.g. 1929 -> "1920s"), or "".

    Buckets group by decade rather than exact year: meaningful chronology without a
    separate node for every one of ~400 distinct years in the archive."""
    y = real_year(path)
    return f"{(int(y) // 10) * 10}s" if y else ""


def infer_year(path: Path) -> str:
    """Year metadata for an image note: a real artwork year, else the era folder
    (e.g. "1800s"), else "". Era is metadata only — it does NOT get its own date
    bucket, since the matching `Collection - <era>` note already groups those."""
    ry = real_year(path)
    if ry:
        return ry
    rel = path.relative_to(IMAGE_ROOT)
    for part in rel.parts:
        if re.fullmatch(r"\d{3,4}s", part):
            return part
    return ""


def image_size(path: Path) -> str:
    if Image is None:
        return ""
    try:
        with Image.open(path) as img:
            return f"{img.width}x{img.height}"
    except Exception:
        return ""


def media_embed(path: Path) -> str:
    rel = path.relative_to(IMAGE_ROOT)
    return f"![[media/strauh.al3.1/{rel.as_posix()}]]"


def media_link(path: Path) -> str:
    rel = path.relative_to(IMAGE_ROOT)
    return f"[[media/strauh.al3.1/{rel.as_posix()}|source file]]"


def source_link_html(path: Path) -> str:
    rel = path.relative_to(HTML_ROOT)
    return f"[[media/strauh.al4/{rel.as_posix()}|source file]]"


def html_pages() -> list[Path]:
    return sorted(
        p for p in HTML_ROOT.rglob("*.html")
        if not any(part in SKIP_PARTS for part in p.parts)
    )


def image_files() -> list[Path]:
    return sorted(
        p for p in IMAGE_ROOT.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and not any(part in SKIP_PARTS for part in p.parts)
    )


def compile_html_pages() -> dict[Path, str]:
    pages = html_pages()
    parsed: dict[Path, tuple[str, str, list[tuple[str, str]], list[tuple[str, str]]]] = {}
    proposed_names: dict[str, list[Path]] = {}
    page_names: dict[Path, str] = {}
    for path in pages:
        parsed[path] = read_html(path)
        proposed = page_note_name(path, parsed[path][0])
        proposed_names.setdefault(proposed, []).append(path)
    for path in pages:
        proposed = page_note_name(path, parsed[path][0])
        if len(proposed_names[proposed]) > 1:
            proposed = safe_filename(str(path.relative_to(HTML_ROOT).with_suffix("")))
        page_names[path.resolve()] = proposed

    for path in pages:
        title, body, links, imgs = parsed[path]
        note = page_names[path.resolve()]
        rel = path.relative_to(HTML_ROOT)
        local_links = sorted({local_page_link(href, path.resolve(), page_names) for href, _ in links} - {None})
        concepts = {"strauh.al Archive", "HTML Source"}
        concepts.update(slug(part) for part in rel.parts[:-1])
        if rel.name != "index.html":
            concepts.add(slug(rel.stem))
        related = "\n".join(f"- {wikilink(name)}" for name in local_links[:40]) or "- None yet"
        concept_links = ", ".join(wikilink(c) for c in sorted(concepts) if c)
        content = frontmatter(
            title=note,
            source_kind="html",
            source_file=str(path),
            source_relpath=str(rel),
            compiled=True,
            compiled_at=dt.datetime.now().isoformat(timespec="seconds"),
            tags=["strauhal", "source/html"],
        )
        content += f"# {note}\n\n"
        content += f"Source: {source_link_html(path)}\n\n"
        content += f"Concepts: {concept_links}\n\n"
        if imgs:
            content += "Images referenced here are preserved as links to their original sources.\n\n"
        content += "## Compiled Page\n\n"
        content += (body or "_No readable body text extracted._") + "\n\n"
        content += "## Related Local Pages\n\n" + related + "\n"
        (PAGES / f"{note}.md").write_text(content)

    return {p.resolve(): n for p, n in page_names.items()}


def compile_images() -> dict[str, list[Path]]:
    files = image_files()
    by_collection: dict[str, list[Path]] = {}
    by_artist: dict[str, list[Path]] = {}
    for path in files:
        rel = path.relative_to(IMAGE_ROOT)
        collection = rel.parts[0] if len(rel.parts) > 1 else "root"
        by_collection.setdefault(collection, []).append(path)
        artist = extract_artist(path.stem)
        if artist:
            by_artist.setdefault(artist, []).append(path)

        title = safe_filename(path.stem)
        digest = hashlib.sha1(str(rel).encode()).hexdigest()[:8]
        note_name = f"{title} {digest}"
        year = infer_year(path)
        artist_link = wikilink(f"Artist - {extract_artist(path.stem)}") if artist else "Unknown"
        size = image_size(path)
        content = frontmatter(
            title=title,
            source_kind="image",
            source_file=str(path),
            source_relpath=str(rel),
            collection=collection,
            inferred_year=year,
            artist=artist or "",
            dimensions=size,
            compiled=True,
            tags=["strauhal", "source/image", f"collection/{collection}"],
        )
        content += f"# {title}\n\n"
        content += f"{media_embed(path)}\n\n"
        content += f"Collection: {wikilink('Collection - ' + safe_filename(collection))}\n\n"
        bucket = decade_bucket(path)
        if bucket:
            content += f"Date bucket: {wikilink('Date Bucket - ' + bucket)}\n\n"
        content += f"Artist: {artist_link}\n\n"
        content += f"Source: {media_link(path)}\n\n"
        content += f"Original path: `{path}`\n"
        (IMAGES / f"{note_name}.md").write_text(content)

    for collection, paths in sorted(by_collection.items()):
        write_collection_note(collection, paths)
    write_date_notes(files)
    for artist, paths in sorted(by_artist.items()):
        write_artist_note(artist, paths)
    return by_collection


def write_collection_note(collection: str, paths: list[Path]) -> None:
    sample = paths[:24]
    note_title = f"Collection - {safe_filename(collection)}"
    content = frontmatter(
        title=note_title,
        source_kind="image_collection",
        count=len(paths),
        compiled=True,
        tags=["strauhal", "collection"],
    )
    content += f"# {note_title}\n\n"
    content += f"Part of {wikilink('strauh.al Image Archive')}.\n\n"
    content += f"Files: {len(paths)}\n\n"
    content += "## Sample\n\n"
    content += "\n\n".join(media_embed(p) for p in sample) or "_No images found._"
    content += "\n\n## Image Notes\n\n"
    for p in paths[:200]:
        title = safe_filename(p.stem)
        digest = hashlib.sha1(str(p.relative_to(IMAGE_ROOT)).encode()).hexdigest()[:8]
        content += f"- [[{title} {digest}|{title}]]\n"
    if len(paths) > 200:
        content += f"\n_Only the first 200 image notes are listed here; search covers all {len(paths)}._\n"
    (COLLECTIONS / f"Collection - {safe_filename(collection)}.md").write_text(content)


def write_date_notes(files: list[Path]) -> None:
    # Only real artwork years get a bucket. Era folders are already covered by their
    # `Collection - <era>` note, and counter/id filenames get no bucket at all.
    buckets: dict[str, list[Path]] = {}
    for path in files:
        bucket = decade_bucket(path)
        if bucket:
            buckets.setdefault(bucket, []).append(path)
    produced: set[Path] = set()
    for bucket, paths in sorted(buckets.items()):
        content = frontmatter(
            title=f"Date Bucket - {bucket}",
            source_kind="date_bucket",
            count=len(paths),
            compiled=True,
            tags=["strauhal", "date-bucket"],
        )
        content += f"# Date Bucket - {bucket}\n\n"
        content += f"Artworks dated {bucket}, by filename. Part of {wikilink('strauh.al Image Archive')}.\n\n"
        content += f"Files: {len(paths)}\n\n"
        content += "## Sample\n\n"
        content += "\n\n".join(media_embed(p) for p in paths[:24])
        content += "\n"
        path_out = COLLECTIONS / f"Date Bucket - {safe_filename(bucket)}.md"
        path_out.write_text(content)
        produced.add(path_out)
    prune_stale_date_buckets(produced)


def prune_stale_date_buckets(produced: set[Path]) -> None:
    """Archive Date Bucket notes no longer produced — the junk buckets that the old
    heuristic spun out of image counters (IMG_1058 → "Date Bucket - 1058")."""
    archive = VAULT / "_archive" / "auto-generated" / "date-buckets-stale"
    moved = 0
    for path in COLLECTIONS.glob("Date Bucket - *.md"):
        if path in produced:
            continue
        archive.mkdir(parents=True, exist_ok=True)
        target = archive / path.name
        if target.exists():
            target.unlink()
        path.rename(target)
        moved += 1
    if moved:
        print(f"  archived {moved} stale date buckets")


def write_artist_note(artist: str, paths: list[Path]) -> None:
    content = frontmatter(
        title=f"Artist - {artist}",
        source_kind="artist",
        count=len(paths),
        compiled=True,
        tags=["strauhal", "artist"],
    )
    content += f"# Artist - {artist}\n\n"
    content += f"Images attributed by filename: {len(paths)}\n\n"
    content += "## Sample\n\n"
    content += "\n\n".join(media_embed(p) for p in paths[:24])
    content += "\n\n## Image Notes\n\n"
    for p in paths[:200]:
        title = safe_filename(p.stem)
        digest = hashlib.sha1(str(p.relative_to(IMAGE_ROOT)).encode()).hexdigest()[:8]
        content += f"- [[{title} {digest}|{title}]]\n"
    (ARTISTS / f"Artist - {safe_filename(artist)}.md").write_text(content)


def write_generated_stats(page_count: int, image_count: int, collection_count: int) -> None:
    generated = WIKI / "maps" / "Generated Corpus Stats.md"
    generated.parent.mkdir(parents=True, exist_ok=True)
    content = frontmatter(title="Generated Corpus Stats", source_kind="index", compiled=True, tags=["strauhal", "index"])
    content += "# Generated Corpus Stats\n\n"
    content += f"HTML pages compiled: {page_count}\n\n"
    content += f"Images compiled: {image_count}\n\n"
    content += f"Collections compiled: {collection_count}\n\n"
    content += f"Browse from {wikilink('Map - Image Archive')} or search with `tools/wiki_search.py`.\n"
    generated.write_text(content)


def write_indexes(page_names: dict[Path, str], collections: dict[str, list[Path]]) -> None:
    page_count = len(page_names)
    image_count = sum(len(v) for v in collections.values())
    write_generated_stats(page_count, image_count, len(collections))
    content = frontmatter(
        title="strauh.al Index",
        source_kind="index",
        compiled=True,
        compiled_at=dt.datetime.now().isoformat(timespec="seconds"),
        tags=["strauhal", "index"],
    )
    content += "# strauh.al Index\n\n"
    content += "This is the compiled Obsidian layer for the strauh.al database: raw sources in, linked wiki out.\n\n"
    content += "## Start Here\n\n"
    content += f"- {wikilink('strauh.al Archive')}\n"
    content += f"- {wikilink('strauh.al Image Archive')}\n"
    content += f"- {wikilink('Compiled Wiki')}\n\n"
    content += "## Counts\n\n"
    content += f"- HTML pages compiled: {page_count}\n"
    content += f"- Image files indexed: {image_count}\n"
    content += f"- Image collections: {len(collections)}\n\n"
    content += "## HTML Pages\n\n"
    for note in sorted(set(page_names.values())):
        content += f"- {wikilink(note)}\n"
    content += "\n## Image Collections\n\n"
    for collection, paths in sorted(collections.items()):
        content += f"- {wikilink('Collection - ' + safe_filename(collection))} ({len(paths)} files)\n"
    content += "\n## Maintenance\n\n"
    content += "- Recompile: `python3 tools/wiki_compile.py`\n"
    content += "- Health check: `python3 tools/wiki_lint.py`\n"
    content += "- Search: `python3 tools/wiki_search.py \"query\"`\n"
    (WIKI / "_index.md").write_text(content)
    (WIKI / "strauh.al Index.md").write_text(content)
    welcome = VAULT / "Welcome.md"
    if not welcome.exists():
        welcome.write_text(content)


def write_missing_link_concepts() -> None:
    known = {p.stem for p in WIKI.rglob("*.md")}
    linked: set[str] = set()
    for path in WIKI.rglob("*.md"):
        text = path.read_text(errors="ignore")
        for match in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text):
            target = match.group(1).strip()
            if target and "/" not in target:
                linked.add(target)
    for target in sorted(linked - known):
        if "/" in target or ":" in target:
            continue
        path = CONCEPTS / f"{target}.md"
        if path.exists():
            continue
        content = frontmatter(
            title=target,
            source_kind="stub_concept",
            compiled=True,
            tags=["strauhal", "concept", "stub"],
        )
        content += f"# {target}\n\n"
        content += "Stub concept created to keep the Obsidian graph connected. Expand this when the idea becomes important.\n"
        path.write_text(content)


def write_raw_manifest() -> None:
    html_count = len(html_pages())
    image_count = len(image_files())
    content = frontmatter(title="Raw Source Manifest", source_kind="manifest", compiled=True, tags=["strauhal", "manifest"])
    content += "# Raw Source Manifest\n\n"
    content += f"- HTML root: `{HTML_ROOT}` ({html_count} HTML files)\n"
    content += f"- Image root: `{IMAGE_ROOT}` ({image_count} image files)\n"
    content += "- Media symlinks live in `media/` so Obsidian can render source files without copying the archive.\n"
    (RAW / "source-manifest.md").write_text(content)


def write_obsidian_config() -> None:
    app = VAULT / ".obsidian" / "app.json"
    if not app.exists():
        app.write_text('{"alwaysUpdateLinks": true,"newFileLocation": "current","showLineNumber": false}\\n')


def main() -> None:
    if not HTML_ROOT.exists() or not IMAGE_ROOT.exists():
        raise SystemExit("Expected /Users/erneststrauhal/GitHub/strauh.al4 and strauh.al3.1 to exist.")
    ensure_dirs()
    write_obsidian_config()
    write_raw_manifest()
    page_names = compile_html_pages()
    collections = compile_images()
    write_indexes(page_names, collections)
    print(f"Compiled {len(page_names)} HTML pages and {sum(len(v) for v in collections.values())} images.")


if __name__ == "__main__":
    main()
