#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import re
import shutil
from pathlib import Path


VAULT = Path(__file__).resolve().parents[1]
WIKI = VAULT / "knowledge" / "wiki"
ARTISTS = WIKI / "artists"
ARCHIVE = VAULT / "knowledge" / "archive" / "auto-generated" / "artists-stale"
ANCHORS = WIKI / "anchors"
ANCHOR_ARCHIVE = VAULT / "knowledge" / "archive" / "auto-generated" / "anchors-stale"
IMAGES = WIKI / "images"


def links(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", text)
    }


def main() -> None:
    referenced: set[str] = set()
    for path in IMAGES.glob("*.md"):
        referenced.update(link for link in links(path.read_text(errors="ignore")) if link.startswith("Artist - "))

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in ARTISTS.glob("*.md"):
        title = path.stem
        if title in referenced:
            continue
        destination = ARCHIVE / path.name
        if destination.exists():
            stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
            destination = ARCHIVE / f"{path.stem}-{stamp}{path.suffix}"
        shutil.move(path, destination)
        moved += 1

    referenced_anchors: set[str] = set()
    for path in WIKI.rglob("*.md"):
        if ANCHORS in path.parents:
            continue
        referenced_anchors.update(links(path.read_text(errors="ignore")))
    ANCHOR_ARCHIVE.mkdir(parents=True, exist_ok=True)
    anchors_moved = 0
    for path in ANCHORS.glob("*.md"):
        body = path.read_text(errors="ignore")
        match = re.search(r"^title:\s*(.+)$", body, re.M)
        title = match.group(1).strip().strip('"') if match else path.stem
        if title in referenced_anchors:
            continue
        destination = ANCHOR_ARCHIVE / path.name
        if destination.exists():
            stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
            destination = ANCHOR_ARCHIVE / f"{path.stem}-{stamp}{path.suffix}"
        shutil.move(path, destination)
        anchors_moved += 1
    print(
        f"Archived {moved} stale artist notes and {anchors_moved} stale anchors; "
        "no files deleted."
    )


if __name__ == "__main__":
    main()
