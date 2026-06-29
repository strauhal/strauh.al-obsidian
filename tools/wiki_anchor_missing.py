#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
ANCHORS = WIKI / "anchors"


def fm(text: str, key: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    block = text[4:end] if end != -1 else ""
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", block, re.M)
    return match.group(1).strip().strip('"') if match else ""


def slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:140] or "untitled"


def links(text: str) -> list[str]:
    return [
        m.group(1).strip()
        for m in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text)
        if "/" not in m.group(1)
    ]


def known_targets() -> set[str]:
    known: set[str] = set()
    for path in WIKI.rglob("*.md"):
        body = path.read_text(errors="ignore")
        title = fm(body, "title") or path.stem
        values = {title, path.stem}
        aliases = fm(body, "aliases")
        for alias in re.findall(r"[^,\[\]]+", aliases):
            if alias.strip():
                values.add(alias.strip())
        for value in values:
            known.add(value)
            known.add(value.lower())
            known.add(slug(value))
    return known


def main() -> None:
    ANCHORS.mkdir(parents=True, exist_ok=True)
    known = known_targets()
    missing: set[str] = set()
    for path in WIKI.rglob("*.md"):
        for link in links(path.read_text(errors="ignore")):
            if link not in known and link.lower() not in known and slug(link) not in known:
                missing.add(link)

    today = dt.date.today().isoformat()
    created = 0
    for title in sorted(missing):
        if not title or title.startswith("media/"):
            continue
        path = ANCHORS / f"{slug(title)}.md"
        if path.exists():
            continue
        body = (
            "---\n"
            f"title: {title}\n"
            "type: anchor\n"
            "tags: [anchor, generated]\n"
            "sources: []\n"
            f"created: {today}\n"
            f"updated: {today}\n"
            "---\n\n"
            f"# {title}\n\n"
            "Generated anchor note for an otherwise unresolved wikilink. Expand or merge this later if it becomes important.\n"
        )
        path.write_text(body)
        created += 1
    print(f"Created {created} anchor notes for unresolved links.")


if __name__ == "__main__":
    main()
