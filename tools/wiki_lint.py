#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
OUTPUT = VAULT / "knowledge" / "output"


def notes() -> list[Path]:
    return sorted(p for p in WIKI.rglob("*.md") if p.is_file())


def title_for(path: Path) -> str:
    return path.stem


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end] if end != -1 else ""


def fm_field(text: str, key: str) -> str:
    fm = frontmatter(text)
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, re.M)
    return match.group(1).strip().strip('"') if match else ""


def is_redirect_or_stub(text: str) -> bool:
    return (
        fm_field(text, "type") == "redirect"
        or "source_kind: \"redirect_stub\"" in text
        or "source_kind: \"stub_concept\"" in text
    )


def note_priority(path: Path, text: str) -> int:
    note_type = fm_field(text, "type")
    if note_type in {"person", "concept", "work", "map"}:
        return 3
    if note_type == "book":
        return 2
    if is_redirect_or_stub(text):
        return 0
    return 1


def slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def has_frontmatter(text: str) -> bool:
    return text.startswith("---\n") and "\n---\n" in text[4:]


def wikilinks(text: str) -> list[str]:
    links = []
    for match in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text):
        target = match.group(1).strip()
        if Path(target).suffix.lower() in {
            ".avif", ".gif", ".heic", ".html", ".jpeg", ".jpg", ".mp3", ".mp4",
            ".pdf", ".png", ".svg", ".tif", ".tiff", ".wav", ".webm", ".webp",
        }:
            continue
        links.append(target)
    return links


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    all_notes = notes()
    note_titles: dict[Path, str] = {}
    known: dict[str, Path] = {}
    note_is_helper: dict[Path, bool] = {}
    priorities: dict[Path, int] = {}
    for p in all_notes:
        body = p.read_text(errors="ignore")
        title = fm_field(body, "title") or title_for(p)
        note_titles[p] = title
        note_is_helper[p] = is_redirect_or_stub(body)
        priorities[p] = note_priority(p, body)
        keys = {title, title_for(p)}
        relative = p.relative_to(VAULT).as_posix()
        keys.update({relative, relative.removesuffix(".md")})
        aliases = fm_field(body, "aliases")
        for alias in re.findall(r"[^,\[\]]+", aliases):
            if alias.strip():
                keys.add(alias.strip())
        for key in keys:
            for variant in {key, key.lower(), slug(key)}:
                existing = known.get(variant)
                if existing is None or priorities[p] > priorities.get(existing, -1):
                    known[variant] = p
    for p in VAULT.glob("*.md"):
        body = p.read_text(errors="ignore")
        title = fm_field(body, "title") or title_for(p)
        keys = {title, title_for(p)}
        relative = p.relative_to(VAULT).as_posix()
        keys.update({relative, relative.removesuffix(".md")})
        for key in keys:
            for variant in {key, key.lower(), slug(key)}:
                known.setdefault(variant, p)
    for p in OUTPUT.rglob("*.md"):
        relative = p.relative_to(VAULT).as_posix()
        for key in {relative, relative.removesuffix(".md")}:
            for variant in {key, key.lower(), slug(key)}:
                known.setdefault(variant, p)
    missing_frontmatter: list[Path] = []
    broken: list[tuple[Path, str]] = []
    outbound: dict[str, set[str]] = {}
    inbound: dict[Path, set[str]] = {p: set() for p in all_notes}

    for path in all_notes:
        text = path.read_text(errors="ignore")
        title = note_titles[path]
        if not has_frontmatter(text):
            missing_frontmatter.append(path)
        links = set(wikilinks(text))
        outbound[title] = links
        for link in links:
            target = known.get(link) or known.get(link.lower()) or known.get(slug(link))
            if not target and "/" in link:
                direct = VAULT / link
                markdown = VAULT / f"{link}.md"
                if direct.exists() or markdown.exists():
                    continue
            if not target:
                broken.append((path, link))
            else:
                inbound.setdefault(target, set()).add(title)

    orphaned = sorted(
        note_titles[path] for path, incoming in inbound.items()
        if not incoming
        and note_titles[path] not in {"_index", "strauh.al Index"}
        and "/images/" not in str(path)
        and "/artists/" not in str(path)
        and "/pages/" not in str(path)
        and "/collections/" not in str(path)
        and "/anchors/" not in str(path)
        and "/books/" not in str(path)
        and note_titles[path] not in {"strauh.al Knowledge Base", "Home"}
        and not note_is_helper.get(path, False)
    )

    report = "# Wiki Lint Report\n\n"
    report += f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}\n\n"
    report += "## Summary\n\n"
    report += f"- Notes checked: {len(all_notes)}\n"
    report += f"- Missing frontmatter: {len(missing_frontmatter)}\n"
    report += f"- Broken wikilinks: {len(broken)}\n"
    report += f"- Orphan notes: {len(orphaned)}\n\n"

    report += "## Missing Frontmatter\n\n"
    report += "\n".join(f"- `{p.relative_to(VAULT)}`" for p in missing_frontmatter[:200]) or "- None"
    report += "\n\n## Broken Wikilinks\n\n"
    report += "\n".join(f"- `{p.relative_to(VAULT)}` -> `[[{link}]]`" for p, link in broken[:300]) or "- None"
    if len(broken) > 300:
        report += f"\n- ...and {len(broken) - 300} more"
    report += "\n\n## Orphan Notes\n\n"
    report += "\n".join(f"- [[{title}]]" for title in orphaned[:300]) or "- None"
    if len(orphaned) > 300:
        report += f"\n- ...and {len(orphaned) - 300} more"
    report += "\n"

    path = OUTPUT / "wiki-lint-report.md"
    managed = ""
    if path.exists():
        previous = path.read_text(errors="ignore")
        match = re.search(
            r"<!-- vault-crosslinks:start -->.*?<!-- vault-crosslinks:end -->",
            previous,
            flags=re.S,
        )
        if match:
            managed = f"\n{match.group(0)}\n"
    report += managed
    path.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
